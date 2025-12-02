from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

@dataclass
class Event:
    name: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    
    def __post_init__(self):
        # Hacerlo inmutable después de creación
        object.__setattr__(self, '_frozen', True)
    
    def __setattr__(self, key, value):
        if hasattr(self, '_frozen'):
            raise AttributeError("Event is immutable")
        super().__setattr__(key, value)


class EventBus:
   
    def __init__(self):
        self._subscribers: Dict[str, List[tuple]] = {}
        self._logger = logging.getLogger('events')
        self._event_history: List[Event] = []
        self._max_history = 100
    
    def subscribe(
        self,
        event_pattern: str,
        handler: Callable,
        priority: int = 10,
        filter_fn: Optional[Callable[[Event], bool]] = None
    ):

        if event_pattern not in self._subscribers:
            self._subscribers[event_pattern] = []
        
        self._subscribers[event_pattern].append({
            'handler': handler,
            'priority': priority,
            'filter': filter_fn
        })
        
        # Ordenar por prioridad
        self._subscribers[event_pattern].sort(
            key=lambda x: x['priority'],
            reverse=True
        )
        
        self._logger.debug(
            f"Subscribed: {handler.__name__} to '{event_pattern}' (priority {priority})"
        )
    
    def publish(self, event_name: str, **data) -> Event:
        # Crear evento inmutable
        event = Event(
            name=event_name,
            data=data,
            source=self._get_caller_module()
        )
        
        # Guardar en historial
        self._add_to_history(event)
        
        # Encontrar subscribers que coincidan
        matching_handlers = self._find_matching_handlers(event_name)
        
        if not matching_handlers:
            self._logger.debug(f"No handlers for event: {event_name}")
            return event
        
        # Ejecutar handlers
        for handler_info in matching_handlers:
            handler = handler_info['handler']
            filter_fn = handler_info['filter']
            
            # Aplicar filtro si existe
            if filter_fn and not filter_fn(event):
                continue
            
            try:
                handler(event)
            except Exception as e:
                self._logger.error(
                    f"Error in handler '{handler.__name__}' for event '{event_name}': {e}",
                    exc_info=True
                )
                # Publicar evento de error
                self.publish(
                    "system.handler_error",
                    original_event=event_name,
                    handler=handler.__name__,
                    error=str(e)
                )
        
        return event
    
    def _find_matching_handlers(self, event_name: str) -> List[dict]:
        """Encuentra handlers que coincidan con el evento (soporte para wildcards)"""
        matching = []
        
        for pattern, handlers in self._subscribers.items():
            if self._pattern_matches(pattern, event_name):
                matching.extend(handlers)
        
        # Ordenar por prioridad global
        matching.sort(key=lambda x: x['priority'], reverse=True)
        return matching
    
    def _pattern_matches(self, pattern: str, event_name: str) -> bool:
        if pattern == event_name:
            return True
        
        # Soporte para wildcards
        if '*' in pattern:
            pattern_parts = pattern.split('.')
            event_parts = event_name.split('.')
            
            if len(pattern_parts) != len(event_parts):
                return False
            
            for p, e in zip(pattern_parts, event_parts):
                if p != '*' and p != e:
                    return False
            
            return True
        
        return False
    
    def _add_to_history(self, event: Event):
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
    
    def _get_caller_module(self) -> str:
        import inspect
        frame = inspect.currentframe()
        try:
            # Subir 3 frames: _get_caller -> publish -> caller
            caller_frame = frame.f_back.f_back.f_back
            return caller_frame.f_globals.get('__name__', 'unknown')
        finally:
            del frame
    
    def get_history(self, event_pattern: Optional[str] = None) -> List[Event]:
        if event_pattern:
            return [
                e for e in self._event_history
                if self._pattern_matches(event_pattern, e.name)
            ]
        return self._event_history.copy()
    
    def unsubscribe(self, event_pattern: str, handler: Callable):
        """Desuscribe un handler específico"""
        if event_pattern in self._subscribers:
            self._subscribers[event_pattern] = [
                h for h in self._subscribers[event_pattern]
                if h['handler'] != handler
            ]

event_bus = EventBus()