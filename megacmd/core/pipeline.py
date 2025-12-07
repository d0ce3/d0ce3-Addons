from typing import Callable, List, Any, Dict
from dataclasses import dataclass
from .events import event_bus
import time

@dataclass
class PipelineStep:
    name: str
    function: Callable
    required: bool = True

class PipelineContext:
    def __init__(self, **initial_data):
        self._data = initial_data
        self._start_time = time.time()
    
    def get(self, key: str, default=None):
        return self._data.get(key, default)
    
    def set(self, key: str, value):
        self._data[key] = value
    
    def update(self, data: dict):
        self._data.update(data)
    
    def to_dict(self) -> dict:
        return self._data.copy()
    
    def elapsed_time(self) -> float:
        return time.time() - self._start_time

class Pipeline:
    def __init__(self, name: str):
        self.name = name
        self.steps: List[PipelineStep] = []
    
    def add_step(self, name: str, function: Callable, required: bool = True):
        self.steps.append(PipelineStep(name, function, required))
        return self
    
    def execute(self, **initial_context) -> Dict[str, Any]:
        context = PipelineContext(**initial_context)
        
        event_bus.publish(
            f"{self.name}.started",
            pipeline=self.name,
            initial_context=context.to_dict()
        )
        
        try:
            for step in self.steps:
                self._execute_step(step, context)
            
            duration = context.elapsed_time()
            event_bus.publish(
                f"{self.name}.success",
                pipeline=self.name,
                result=context.to_dict(),
                duration_seconds=duration
            )
            
            return context.to_dict()
            
        except Exception as e:
            event_bus.publish(
                f"{self.name}.failed",
                pipeline=self.name,
                error=str(e),
                error_type=type(e).__name__,
                context=context.to_dict()
            )
            raise
            
        finally:
            duration = context.elapsed_time()
            event_bus.publish(
                f"{self.name}.finished",
                pipeline=self.name,
                duration_seconds=duration
            )
    
    def _execute_step(self, step: PipelineStep, context: PipelineContext):
        step_event_prefix = f"{self.name}.step.{step.name}"
        
        event_bus.publish(f"{step_event_prefix}.started", step_name=step.name)
        
        try:
            result = step.function(context)
            
            if result is not None:
                if isinstance(result, dict):
                    context.update(result)
                else:
                    context.set(step.name, result)
            
            event_bus.publish(f"{step_event_prefix}.success", step_name=step.name, result=result)
            
        except Exception as e:
            event_bus.publish(f"{step_event_prefix}.failed", step_name=step.name, error=str(e))
            
            if step.required:
                raise
            else:
                import logging
                logging.warning(f"Paso '{step.name}' falló pero no es crítico: {e}")