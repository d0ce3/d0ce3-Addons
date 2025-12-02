from core.events import event_bus, Event

def setup_discord_observer():
    
    publisher = CloudModuleLoader.load_module("discord_publisher").publisher
    
    def on_backup_success(event: Event):
        if not publisher.is_enabled():
            return
        
        # Filtrar: solo backups auto
        if 'auto' not in event.name:
            return
        
        result = event.data.get('result', {})
        
        publisher.publish_backup_success(
            backup_file=result.get('backup_name', 'unknown'),
            size_mb=result.get('backup_size_mb', 0),
            duration_seconds=result.get('duration', 0)
        )
    
    def on_backup_failed(event: Event):
        if not publisher.is_enabled():
            return
        
        error = event.data.get('error', 'Unknown error')
        context = event.data.get('context', {})
        
        publisher.publish_backup_error(
            error_type="backup_execution",
            error_message=error,
            backup_file=context.get('backup_name')
        )
    
    event_bus.subscribe("backup.*.success", on_backup_success, priority=50)
    event_bus.subscribe("backup.*.failed", on_backup_failed, priority=50)