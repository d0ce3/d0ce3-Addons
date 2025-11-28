import threading
import os
import json
import time
from datetime import datetime

config = CloudModuleLoader.load_module("config")
utils = CloudModuleLoader.load_module("utils")

backup_timer = None
backup_timer_created_at = None

TIMER_LOCK_FILE = os.path.expanduser("~/.megacmd_timer_lock")

class TimerManager:
    @staticmethod
    def is_timer_active():
        if not os.path.exists(TIMER_LOCK_FILE):
            return False
        
        try:
            with open(TIMER_LOCK_FILE, 'r') as f:
                data = json.load(f)
            
            last_activity = data.get('last_activity', 0)
            interval = data.get('interval_minutes', 3)
            elapsed = time.time() - last_activity
            
            if elapsed > (interval * 60 * 2):
                return False
            
            pid = data.get('pid', 0)
            
            try:
                os.kill(pid, 0)
                return True
            except (OSError, ProcessLookupError):
                return False
        except:
            return False
    
    @staticmethod
    def mark_timer_active(interval_minutes=3):
        try:
            with open(TIMER_LOCK_FILE, 'w') as f:
                json.dump({
                    'pid': os.getpid(),
                    'last_activity': time.time(),
                    'interval_minutes': interval_minutes
                }, f)
        except:
            pass
    
    @staticmethod
    def update_activity():
        if os.path.exists(TIMER_LOCK_FILE):
            try:
                with open(TIMER_LOCK_FILE, 'r') as f:
                    data = json.load(f)
                
                data['last_activity'] = time.time()
                
                with open(TIMER_LOCK_FILE, 'w') as f:
                    json.dump(data, f)
            except:
                pass
    
    @staticmethod
    def clear_timer_lock():
        try:
            if os.path.exists(TIMER_LOCK_FILE):
                with open(TIMER_LOCK_FILE, 'r') as f:
                    data = json.load(f)
                
                stored_pid = data.get('pid', 0)
                current_pid = os.getpid()
                
                if stored_pid == current_pid:
                    os.remove(TIMER_LOCK_FILE)
                    utils.logger.info(f"Timer lock eliminado (PID {current_pid})")
                else:
                    utils.logger.warning(f"Timer lock de otro proceso (PID {stored_pid})")
        except:
            pass

def _actualizar_configuracion_msx(activar=True):
    workspace = os.getenv("CODESPACE_VSCODE_FOLDER", "/workspace")
    config_path = os.path.join(workspace, "configuracion.json")
    backup_mode_cache = os.path.join(config.BASE_DIR, ".backup_mode_original")
    
    try:
        if not os.path.exists(config_path):
            utils.logger.warning(f"configuracion.json no encontrado en {config_path}")
            return False
        
        with open(config_path, 'r') as f:
            configuracion_msx = json.load(f)
        
        backup_mode_anterior = configuracion_msx.get('backup_mode', '')
        backup_auto_anterior = configuracion_msx.get('backup_auto', False)
        
        if activar:
            if backup_mode_anterior:
                try:
                    with open(backup_mode_cache, 'w') as f:
                        f.write(backup_mode_anterior)
                    utils.logger.info(f"Guardado backup_mode original: '{backup_mode_anterior}'")
                except Exception as e:
                    utils.logger.warning(f"No se pudo guardar backup_mode: {e}")
            
            configuracion_msx['backup_mode'] = ""
            configuracion_msx['backup_auto'] = True
            
            utils.logger.info(f"Desactivando backup nativo de MSX (era: '{backup_mode_anterior}')")
        else:
            configuracion_msx['backup_auto'] = False
            
            if os.path.exists(backup_mode_cache):
                try:
                    with open(backup_mode_cache, 'r') as f:
                        modo_original = f.read().strip()
                    
                    if modo_original:
                        configuracion_msx['backup_mode'] = modo_original
                        utils.logger.info(f"Restaurado backup_mode original: '{modo_original}'")
                    
                    os.remove(backup_mode_cache)
                except Exception as e:
                    utils.logger.warning(f"No se pudo restaurar backup_mode: {e}")
            else:
                utils.logger.info("No hay backup_mode guardado para restaurar")
            
            utils.logger.info("Autobackup desactivado en configuracion.json")
        
        with open(config_path, 'w') as f:
            json.dump(configuracion_msx, f, separators=(',', ': '), ensure_ascii=False)
        
        utils.logger.info(
            f"configuracion.json actualizado (formato compacto): "
            f"backup_mode: '{backup_mode_anterior}' -> '{configuracion_msx['backup_mode']}', "
            f"backup_auto: {backup_auto_anterior} -> {configuracion_msx['backup_auto']}"
        )
        
        return True
        
    except Exception as e:
        utils.logger.error(f"Error actualizando configuracion.json: {e}")
        import traceback
        utils.logger.error(traceback.format_exc())
        return False

def _ejecutar_backup():
    backup_module = CloudModuleLoader.load_module("backup")
    if backup_module:
        try:
            backup_module.ejecutar_backup_automatico()
            TimerManager.update_activity()
        except Exception as e:
            utils.logger.error(f"Error en backup automático: {e}")
    
    try:
        if backup_module:
            backup_module.limpiar_backups_antiguos()
    except Exception as e:
        utils.logger.error(f"Error limpiando backups: {e}")

def _timer_callback():
    global backup_timer, backup_timer_created_at
    
    try:
        interval_minutes = config.CONFIG.get("backup_interval_minutes", 3)
        
        TimerManager.mark_timer_active(interval_minutes)
        
        utils.logger.info(f"Timer ejecutado - Próximo en {interval_minutes} min")
        
        _ejecutar_backup()
        
        if config.CONFIG.get("autobackup_enabled", False):
            backup_timer = threading.Timer(interval_minutes * 60, _timer_callback)
            backup_timer.daemon = True
            backup_timer.start()
            backup_timer_created_at = datetime.now()
            
            TimerManager.mark_timer_active(interval_minutes)
        else:
            utils.logger.info("Autobackup desactivado, no se programa siguiente")
            backup_timer = None
            backup_timer_created_at = None
            TimerManager.clear_timer_lock()
    except Exception as e:
        utils.logger.error(f"Error en timer_callback: {e}")
        backup_timer = None
        backup_timer_created_at = None
        TimerManager.clear_timer_lock()

def start_autobackup():
    global backup_timer, backup_timer_created_at
    
    if not config.CONFIG.get("autobackup_enabled", False):
        utils.logger.info("Autobackup desactivado en config")
        return False
    
    if backup_timer and backup_timer.is_alive():
        utils.logger.info("Timer ya activo")
        return True
    
    if TimerManager.is_timer_active():
        utils.logger.warning("Timer activo en otra instancia")
        return False
    
    interval_minutes = config.CONFIG.get("backup_interval_minutes", 3)
    
    backup_timer = threading.Timer(interval_minutes * 60, _timer_callback)
    backup_timer.daemon = True
    backup_timer.start()
    backup_timer_created_at = datetime.now()
    
    TimerManager.mark_timer_active(interval_minutes)
    
    utils.logger.info(f"Timer iniciado - {interval_minutes} min")
    return True

def stop_autobackup():
    global backup_timer, backup_timer_created_at
    
    if backup_timer:
        backup_timer.cancel()
        backup_timer = None
        backup_timer_created_at = None
        
        TimerManager.clear_timer_lock()
        
        utils.logger.info("Timer detenido")
        return True
    
    return False

def enable():
    config.set("autobackup_enabled", True)
    utils.logger.info("Autobackup habilitado")
    
    if _actualizar_configuracion_msx(activar=True):
        utils.logger.info("✓ Configuración MSX actualizada (backup nativo desactivado)")
    
    return start_autobackup()

def disable():
    config.set("autobackup_enabled", False)
    utils.logger.info("Autobackup deshabilitado")
    
    if _actualizar_configuracion_msx(activar=False):
        utils.logger.info("✓ Configuración MSX actualizada")
    
    return stop_autobackup()

def toggle_autobackup():
    if config.CONFIG.get("autobackup_enabled", False):
        return disable()
    else:
        return enable()

def is_enabled():
    return config.CONFIG.get("autobackup_enabled", False)

def get_timer_info():
    global backup_timer, backup_timer_created_at
    
    if not backup_timer or not backup_timer.is_alive():
        return None
    
    if not backup_timer_created_at:
        return None
    
    interval_minutes = config.CONFIG.get("backup_interval_minutes", 3)
    tiempo_transcurrido = datetime.now() - backup_timer_created_at
    segundos_transcurridos = tiempo_transcurrido.total_seconds()
    segundos_restantes = (interval_minutes * 60) - segundos_transcurridos
    
    if segundos_restantes < 0:
        segundos_restantes = 0
    
    minutos_restantes = int(segundos_restantes // 60)
    segundos_solo = int(segundos_restantes % 60)
    
    return {
        'activo': True,
        'intervalo_minutos': interval_minutes,
        'proxima_ejecucion': f"{minutos_restantes}m {segundos_solo}s",
        'creado_en': backup_timer_created_at.strftime("%H:%M:%S")
    }

def force_backup_now():
    if not config.CONFIG.get("autobackup_enabled", False):
        utils.logger.warning("Autobackup desactivado")
        return False
    
    try:
        utils.logger.info("Forzando backup manual desde autobackup")
        _ejecutar_backup()
        return True
    except Exception as e:
        utils.logger.error(f"Error forzando backup: {e}")
        return False
