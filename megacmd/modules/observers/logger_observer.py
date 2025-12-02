from core.events import event_bus, Event

def setup_logger_observer():    
    logger = CloudModuleLoader.load_module("logger").logger_manager
       
    def on_backup_started(event: Event):
        mode = event.name.split('.')[1]  # backup.manual.started -> manual
        logger.info(f"========== INICIO BACKUP {mode.upper()} ==========")
    
    def on_backup_success(event: Event):
        result = event.data.get('result', {})
        backup_name = result.get('backup_name', 'unknown')
        size_mb = result.get('backup_size_mb', 0)
        logger.info(f"Backup exitoso: {backup_name} ({size_mb:.1f} MB)")
    
    def on_backup_failed(event: Event):
        error = event.data.get('error', 'Unknown error')
        logger.error(f"Backup falló: {error}")
    
    def on_backup_finished(event: Event):
        logger.info("========== FIN BACKUP ==========")
    
    def on_compress_started(event: Event):
        logger.info("Iniciando compresión...")
    
    def on_compress_success(event: Event):
        result = event.data.get('result', {})
        backup_name = result.get('backup_name')
        size_mb = result.get('backup_size_mb', 0)
        logger.info(f"Comprimido: {backup_name} ({size_mb:.1f} MB)")
    
    def on_upload_started(event: Event):
        logger.info("Subiendo a MEGA...")
    
    def on_upload_success(event: Event):
        logger.info("Subida completada")
    
    event_bus.subscribe("backup.*.started", on_backup_started, priority=100)
    event_bus.subscribe("backup.*.success", on_backup_success, priority=100)
    event_bus.subscribe("backup.*.failed", on_backup_failed, priority=100)
    event_bus.subscribe("backup.*.finished", on_backup_finished, priority=100)
  
    event_bus.subscribe("backup.*.step.compress.started", on_compress_started, priority=100)
    event_bus.subscribe("backup.*.step.compress.success", on_compress_success, priority=100)
    event_bus.subscribe("backup.*.step.upload.started", on_upload_started, priority=100)
    event_bus.subscribe("backup.*.step.upload.success", on_upload_success, priority=100)