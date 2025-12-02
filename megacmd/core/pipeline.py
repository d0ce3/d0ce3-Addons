from typing import Callable, List, Any, Dict, Optional
from dataclasses import dataclass
from .events import event_bus, Event

@dataclass
class PipelineStep:
    name: str
    function: Callable
    required: bool = True
    
class Pipeline:
    def __init__(self, name: str):
        self.name = name
        self.steps: List[PipelineStep] = []
        self._context: Dict[str, Any] = {}
    
    def add_step(self, name: str, function: Callable, required: bool = True):
        """Agrega paso al pipeline"""
        self.steps.append(PipelineStep(name, function, required))
        return self
    
    def execute(self, **initial_context) -> Dict[str, Any]:
        """
        Ejecuta el pipeline completo.
        Publica eventos automáticamente:
        - {name}.started
        - {name}.step.{step_name}.started
        - {name}.step.{step_name}.success
        - {name}.step.{step_name}.failed
        - {name}.success / {name}.failed
        - {name}.finished
        """
        self._context = initial_context.copy()
        
        # Evento: inicio
        event_bus.publish(
            f"{self.name}.started",
            context=self._context.copy()
        )
        
        try:
            # Ejecutar cada paso
            for step in self.steps:
                self._execute_step(step)
            
            # Evento: éxito
            event_bus.publish(
                f"{self.name}.success",
                result=self._context.copy()
            )
            
            return self._context
            
        except Exception as e:
            # Evento: error
            event_bus.publish(
                f"{self.name}.failed",
                error=str(e),
                context=self._context.copy()
            )
            raise
            
        finally:
            # Evento: finalización
            event_bus.publish(
                f"{self.name}.finished",
                context=self._context.copy()
            )
    
    def _execute_step(self, step: PipelineStep):
        """Ejecuta un paso individual"""
        step_event_prefix = f"{self.name}.step.{step.name}"
        
        # Evento: inicio del paso
        event_bus.publish(f"{step_event_prefix}.started")
        
        try:
            # Ejecutar función del paso
            result = step.function(self._context)
            
            # Actualizar contexto con resultado
            if result is not None:
                if isinstance(result, dict):
                    self._context.update(result)
                else:
                    self._context[step.name] = result
            
            event_bus.publish(
                f"{step_event_prefix}.success",
                result=result
            )
            
        except Exception as e:
            event_bus.publish(
                f"{step_event_prefix}.failed",
                error=str(e)
            )
            
            if step.required:
                raise