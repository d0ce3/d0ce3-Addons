import threading
import os
import subprocess
import json
import time
from datetime import datetime, timedelta

config = CloudModuleLoader.load_module("config")
utils = CloudModuleLoader.load_module("utils")

backup_timer = None
backup_timer_created_at = None

TIMER_LOCK_FILE = os.path.expanduser("~/.megacmd_timer_lock")

class TimerManager:
    """Gestiona el estado del timer de manera persistente"""
    
    @staticmethod
    def is_timer_active():
        """Verifica si hay un timer activo (incluso de otra instancia del módulo)"""
        if not os.path.exists(TIMER_LOCK_FILE):
            return False
        try:
            with open(TIMER_LOCK_FILE, 'r') as f:
                data = json.load(f)
                # Verificar que no haya pasado más del doble del intervalo
                last_activity = data.get('last_activity', 0)
                interval = data.get('interval_minutes', 3)
                elapsed = time.time() - last_activity
                
                # Si pasó más del doble del intervalo, el timer probablemente murió
                if elapsed > (interval * 60 * 2):
                    return False
                
                # Verificar el PID del proceso
                pid = data.get('pid', 0)
                try:
                    # Verificar si el proceso existe
                    os.kill(pid, 0)
                    return True
                except (OSError, ProcessLookupError):
                    # El proceso no existe
                    return False
        except:
            return False
    
    @staticmethod
    def mark_timer_active(interval_minutes=3):
        """Marca que hay un timer activo"""
        try:
            with open(TIMER_LOCK_FILE, 'w') as f:
                json.dump({
                    'pid': os.getpid(),
                    'last_activity': time.time(),
                    'interval_minutes': interval_minutes,
                    'created_at': datetime.now().isoformat()
                }, f)
            return True
        except:
            return False
    
    @staticmethod
    def update_activity():
        """Actualiza el timestamp de última actividad"""
        if not os.path.exists(TIMER_LOCK_FILE):
            return False
        try:
            with open(TIMER_LOCK_FILE, 'r') as f:
                data = json.load(f)
            
            # Solo actualizar si el PID coincide
            if data.get('pid') == os.getpid():
                data['last_activity'] = time.time()
                with open(TIMER_LOCK_FILE, 'w') as f:
                    json.dump(data, f)
                return True
        except:
            pass
        return False
    
    @staticmethod
    def clear_timer():
        """Limpia el archivo de lock del timer"""
        try:
            if os.path.exists(TIMER_LOCK_FILE):
                # Solo limpiar si el PID coincide o el archivo está corrupto
                try:
                    with open(TIMER_LOCK_FILE, 'r') as f:
                        data = json.load(f)
                    if data.get('pid') == os.getpid():
                        os.remove(TIMER_LOCK_FILE)
                        return True
                except:
                    # Archivo corrupto, eliminarlo
                    os.remove(TIMER_LOCK_FILE)
                    return True
        except:
            pass
        return False

# CAMBIO IMPORTANTE: Ahora usa config.py en lugar de archivo separado
def is_enabled():
    """Verifica si el autobackup está habilitado desde config.py"""
    try:
        return config.CONFIG.get("autobackup_enabled", False)
    except:
        return False

def enable():
    """Habilita el autobackup en config.py"""
    try:
        config.set("autobackup_enabled", True)
        utils.logger.info("Autobackup habilitado")
        return True
    except Exception as e:
        utils.logger.error(f"Error habilitando autobackup: {e}")
        return False

def disable():
    """Deshabilita el autobackup en config.py"""
    try:
        config.set("autobackup_enabled", False)
        utils.logger.info("Autobackup deshabilitado")
        return True
    except Exception as e:
        utils.logger.error(f"Error deshabilitando autobackup: {e}")
        return False

def ejecutar_backup_automatico():
    global backup_timer
    try:
        # Actualizar actividad del timer
        TimerManager.update_activity()
        
        utils.logger.info("========== INICIO BACKUP AUTOMÁTICO ==========")
        utils.logger.info(f"Directorio de trabajo: {os.getcwd()}")

        if not is_enabled():
            utils.logger.info("Autobackup no está habilitado, se detiene el backup automático")
            return

        backup = CloudModuleLoader.load_module("backup")
        if backup and hasattr(backup, 'ejecutar_backup_automatico'):
            backup.ejecutar_backup_automatico()
        else:
            utils.logger.error("No se pudo cargar el módulo backup")

    except Exception as e:
        utils.logger.error(f"Error en backup automático: {e}")
        import traceback
        utils.logger.error(traceback.format_exc())
    finally:
        utils.logger.info("Backup automático finalizado")

def start_autobackup(interval_minutes=None):
    global backup_timer, backup_timer_created_at

    # Obtener intervalo de configuración si no se especifica
    if interval_minutes is None:
        interval_minutes = config.CONFIG.get("backup_interval_minutes", 3)

    # Verificar si ya hay un timer activo (incluso de otra instancia)
    if TimerManager.is_timer_active():
        utils.logger.info(f"Timer de autobackup ya activo en proceso - omitiendo (PID actual: {os.getpid()})")
        return

    # Verificar si el timer local está activo
    if backup_timer is not None and backup_timer.is_alive():
        utils.logger.info("Timer local de autobackup ya activo, no se crea uno nuevo")
        return

    now = datetime.now()
    backup_timer_created_at = now

    def timer_callback():
        global backup_timer
        ejecutar_backup_automatico()
        
        # Reprogramar solo si sigue habilitado
        if is_enabled():
            # Limpiar el timer actual antes de crear uno nuevo
            backup_timer = None
            TimerManager.clear_timer()
            start_autobackup(interval_minutes)
        else:
            utils.logger.info("Autobackup deshabilitado, no se reprograma timer")
            backup_timer = None
            TimerManager.clear_timer()

    # Marcar que se está creando un timer
    TimerManager.mark_timer_active(interval_minutes)
    
    utils.logger.info(f"Nuevo timer programado para {interval_minutes} minutos (PID: {os.getpid()})")
    utils.logger.info(f"Autobackup activado - cada {interval_minutes} minutos")
    
    backup_timer = threading.Timer(interval_minutes * 60, timer_callback)
    backup_timer.daemon = True
    backup_timer.start()

def stop_autobackup():
    global backup_timer
    if backup_timer:
        backup_timer.cancel()
        backup_timer = None
        utils.logger.info("Timer de autobackup detenido")
    
    # Limpiar el archivo de lock
    TimerManager.clear_timer()

def toggle_autobackup():
    if is_enabled():
        stop_autobackup()
        disable()
        utils.logger.info("Autobackup desactivado por usuario")
    else:
        enable()
        start_autobackup()
        utils.logger.info("Autobackup activado por usuario")

def init_on_load():
    """Inicializa el autobackup si está habilitado"""
    if is_enabled():
        utils.logger.info("Autobackup está habilitado, verificando timer...")
        
        # Verificar si ya hay un timer activo
        if not TimerManager.is_timer_active():
            utils.logger.info("No hay timer activo, iniciando autobackup...")
            start_autobackup()
        else:
            utils.logger.info("Timer ya activo en otro proceso, no se inicia uno nuevo")
    else:
        utils.logger.info("Autobackup no está habilitado")

# Registrar limpieza al salir
import atexit

def cleanup_on_exit():
    """Limpia el timer cuando el módulo se descarga"""
    global backup_timer
    if backup_timer and backup_timer.is_alive():
        backup_timer.cancel()
    TimerManager.clear_timer()

atexit.register(cleanup_on_exit)