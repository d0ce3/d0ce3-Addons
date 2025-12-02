from functools import wraps
from core.events import event_bus

def event_publisher(event_name_prefix):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            event_bus.publish(f"{event_name_prefix}.started")
            
            try:
                result = func(*args, **kwargs)
                event_bus.publish(f"{event_name_prefix}.success", result=result)
                return result
            except Exception as e:
                event_bus.publish(f"{event_name_prefix}.failed", error=str(e))
                raise
            finally:
                event_bus.publish(f"{event_name_prefix}.finished")
        return wrapper
    return decorator
