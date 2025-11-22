import threading
import os
import subprocess
from datetime import datetime, timedelta

config = CloudModuleLoader.load_module("config")
utils = CloudModuleLoader.load_module("utils")

backup_timer = None
backup_timer_created_at = None  # Marca de tiempo para control de creación

AUTOBACKUP_FILE = os.path.expanduser("~/.megacmd_autobackup")

def is_enabled():
    try:
        if os.path.exists(AUTOBACKUP_FILE):
            with open(AUTOBACKUP_FILE, 'r') as f:
                return f.read().strip() == 'enabled'
        return False
    except:
        return False

def enable():
    try:
        with open(AUTOBACKUP_FILE, 'w') as f:
            f.write('enabled')
        utils.logger.info("Autobackup habilitado")
        return True
    except Exception as e:
        utils.logger.error(f"Error habilitando autobackup: {e}")
        return False

def disable():
    try:
        if os.path.exists(AUTOBACKUP_FILE):
            os.remove(AUTOBACKUP_FILE)
        utils.logger.info("Autobackup deshabilitado")
        return True
    except Exception as e:
        utils.logger.error(f"Error deshabilitando autobackup: {e}")
        return False

def ejecutar_backup_automatico():
    global backup_timer
    try:
        utils.logger.info("========== INICIO BACKUP AUTOMÁTICO ==========")
        utils.logger.info(f"Directorio de trabajo: {os.getcwd()}")
        utils.logger.info("Mensaje de inicio mostrado en terminal")

        if not is_enabled():
            utils.logger.info("Autobackup no está habilitado, se detiene el backup automático")
            return

        import backup
        backup.ejecutar_backup_automatico()

    except Exception as e:
        utils.logger.error(f"Error en backup automático: {e}")
    finally:
        utils.logger.info("Backup automático finalizado")

def start_autobackup(interval_minutes=3):
    global backup_timer, backup_timer_created_at

    now = datetime.now()

    if backup_timer is not None:
        elapsed = now - backup_timer_created_at
        if elapsed < timedelta(minutes=interval_minutes):
            utils.logger.info(f"[SALTEAR] Timer de autobackup ya activo, creado hace {elapsed}")
            return
        else:
            utils.logger.info("Timer anterior expirado, cancelando y creando uno nuevo")
            backup_timer.cancel()
            backup_timer = None

    def timer_callback():
        global backup_timer
        ejecutar_backup_automatico()
        if is_enabled():
            start_autobackup(interval_minutes)
        else:
            utils.logger.info("Autobackup deshabilitado, no se reprograma timer")
            backup_timer = None

    utils.logger.info(f"Nuevo timer programado para {interval_minutes} minutos")
    utils.logger.info(f"Autobackup activado - cada {interval_minutes} minutos")
    backup_timer = threading.Timer(interval_minutes * 60, timer_callback)
    backup_timer_created_at = now
    backup_timer.daemon = True
    backup_timer.start()

def stop_autobackup():
    global backup_timer
    if backup_timer:
        backup_timer.cancel()
        backup_timer = None
        utils.logger.info("Timer de autobackup detenido")

def toggle_autobackup():
    if is_enabled():
        stop_autobackup()
        disable()
    else:
        enable()
        start_autobackup()

def init_on_load():
    if is_enabled() and backup_timer is None:
        start_autobackup()
