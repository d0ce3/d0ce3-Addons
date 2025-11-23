import threading
import os
import subprocess
import json
import time
from datetime import datetime, timedelta, timezone

config = CloudModuleLoader.load_module("config")
utils = CloudModuleLoader.load_module("utils")
logger_mod = CloudModuleLoader.load_module("logger")

backup_timer = None
backup_timer_created_at = None
TIMER_LOCK_FILE = os.path.expanduser("~/.megacmd_timer_lock")

TIMEZONE_ARG = timezone(timedelta(hours=-3))

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
                    'interval_minutes': interval_minutes,
                    'created_at': datetime.now(TIMEZONE_ARG).isoformat()
                }, f)
            return True
        except:
            return False
    
    @staticmethod
    def update_activity():
        if not os.path.exists(TIMER_LOCK_FILE):
            return False
        
        try:
            with open(TIMER_LOCK_FILE, 'r') as f:
                data = json.load(f)
            
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
        try:
            if os.path.exists(TIMER_LOCK_FILE):
                try:
                    with open(TIMER_LOCK_FILE, 'r') as f:
                        data = json.load(f)
                    if data.get('pid') == os.getpid():
                        os.remove(TIMER_LOCK_FILE)
                        return True
                except:
                    os.remove(TIMER_LOCK_FILE)
                    return True
        except:
            pass
        return False

def is_enabled():
    try:
        return config.CONFIG.get("autobackup_enabled", False)
    except:
        return False

def enable():
    try:
        config.set("autobackup_enabled", True)
        logger_mod.log_autobackup_habilitado()
        return True
    except Exception as e:
        utils.logger.error(f"Error habilitando autobackup: {e}")
        return False

def disable():
    try:
        config.set("autobackup_enabled", False)
        logger_mod.log_autobackup_deshabilitado()
        return True
    except Exception as e:
        utils.logger.error(f"Error deshabilitando autobackup: {e}")
        return False

def encontrar_carpeta_servidor(nombre_carpeta="servidor_minecraft"):
    backup = CloudModuleLoader.load_module("backup")
    if backup and hasattr(backup, 'encontrar_carpeta_servidor'):
        return backup.encontrar_carpeta_servidor(nombre_carpeta)
    
    ubicaciones_a_verificar = [
        f"/workspaces/{os.environ.get('CODESPACE_NAME', 'unknown')}/{nombre_carpeta}",
        os.path.join(os.getcwd(), nombre_carpeta),
        os.path.join(os.path.dirname(os.getcwd()), nombre_carpeta),
        os.path.expanduser(f"~/{nombre_carpeta}"),
    ]
    
    for ubicacion in ubicaciones_a_verificar:
        if ubicacion and os.path.exists(ubicacion) and os.path.isdir(ubicacion):
            return ubicacion
    
    return None

def ejecutar_backup_automatico():
    global backup_timer
    
    logger_mod.log_backup_auto_inicio()
    
    try:
        TimerManager.update_activity()
        
        if not config.CONFIG.get("autobackup_enabled", False):
            logger_mod.log_autobackup_desactivado()
            return
        
        utils.print_msg("INICIANDO BACKUP AUTOMÁTICO")
        
        try:
            rcon = CloudModuleLoader.load_module("rcon")
            if rcon and hasattr(rcon, 'enviar_comando'):
                rcon.enviar_comando("say [BACKUP] Iniciando backup automático...")
        except Exception as e:
            logger_mod.log_rcon_error_inicio(e)
        
        server_folder_config = config.CONFIG.get("server_folder", "servidor_minecraft")
        server_folder = encontrar_carpeta_servidor(server_folder_config)
        backup_folder = config.CONFIG.get("backup_folder", "/backups")
        backup_prefix = config.CONFIG.get("backup_prefix", "MSX")
        
        logger_mod.log_config_carpeta(
            server_folder_config,
            config.BASE_DIR,
            os.getcwd(),
            os.path.dirname(config.BASE_DIR),
            server_folder,
            os.path.exists(server_folder) if server_folder else False,
            backup_folder
        )
        
        if not server_folder or not os.path.exists(server_folder):
            utils.print_error(f"La carpeta {server_folder_config} no existe, se cancela backup automático")
            logger_mod.log_carpeta_auto_no_existe(server_folder_config)
            
            try:
                rcon = CloudModuleLoader.load_module("rcon")
                if rcon and hasattr(rcon, 'enviar_comando'):
                    rcon.enviar_comando("say [BACKUP] ERROR: No se pudo encontrar la carpeta del servidor")
            except Exception:
                pass
            
            return
        
        utils.print_msg("Calculando tamaño de carpeta...")
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(server_folder):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except Exception:
                    pass
        
        size_mb = total_size / (1024 * 1024)
        utils.print_msg(f"Tamaño total: {size_mb:.1f} MB")
        logger_mod.log_tamano_carpeta(size_mb)
        
        timestamp = datetime.now(TIMEZONE_ARG).strftime("%d-%m-%Y_%H-%M")
        backup_name = f"{backup_prefix}_{timestamp}.zip"
        utils.print_msg(f"Archivo a crear: {backup_name}")
        logger_mod.log_nombre_backup(backup_name)
        
        utils.print_msg("Comprimiendo...")
        logger_mod.log_compresion_inicio()
        
        cmd = ["zip", "-r", "-q", backup_name, server_folder]
        proceso = subprocess.Popen(cmd)
        proceso.wait()
        
        if not os.path.exists(backup_name):
            utils.print_error("Error al crear archivo ZIP")
            logger_mod.log_compresion_auto_error()
            
            try:
                rcon = CloudModuleLoader.load_module("rcon")
                if rcon and hasattr(rcon, 'enviar_comando'):
                    rcon.enviar_comando("say [BACKUP] ERROR: Fallo al crear archivo ZIP")
            except Exception:
                pass
            
            return
        
        backup_size_mb = os.path.getsize(backup_name) / (1024 * 1024)
        utils.print_msg(f"Archivo comprimido: {backup_name} ({backup_size_mb:.1f} MB)")
        logger_mod.log_archivo_creado(backup_name, backup_size_mb)
        
        utils.print_msg("Subiendo a MEGA...")
        logger_mod.log_subida_inicio()
        
        cmd_upload = ["mega-put", "-c", backup_name, backup_folder + "/"]
        proceso_upload = subprocess.Popen(cmd_upload)
        proceso_upload.wait()
        
        if proceso_upload.returncode != 0:
            utils.print_error("Error al subir backup a MEGA")
            logger_mod.log_subida_auto_error()
            
            try:
                rcon = CloudModuleLoader.load_module("rcon")
                if rcon and hasattr(rcon, 'enviar_comando'):
                    rcon.enviar_comando("say [BACKUP] ERROR: Fallo al subir a MEGA")
            except Exception:
                pass
            
            try:
                os.remove(backup_name)
            except Exception:
                pass
            return
        
        utils.print_msg(f"Backup subido a MEGA en {backup_folder}/{backup_name}")
        logger_mod.log_subida_auto_exitosa(backup_folder, backup_name)
        
        try:
            os.remove(backup_name)
            utils.print_msg("Archivo temporal eliminado")
            logger_mod.log_archivo_local_eliminado()
        except Exception as e:
            utils.print_warning(f"No se pudo eliminar archivo temporal: {e}")
            logger_mod.log_archivo_local_error(e)
        
        backup = CloudModuleLoader.load_module("backup")
        if backup and hasattr(backup, 'limpiar_backups_antiguos'):
            backup.limpiar_backups_antiguos()
        else:
            utils.logger.warning("No se pudo importar limpiar_backups_antiguos desde backup.py")
        
        utils.print_msg("Backup automático completado")
        
        try:
            rcon = CloudModuleLoader.load_module("rcon")
            if rcon and hasattr(rcon, 'enviar_comando'):
                rcon.enviar_comando("say [BACKUP] Backup completado exitosamente")
        except Exception as e:
            logger_mod.log_rcon_error_fin(e)
        
        logger_mod.log_backup_auto_fin()
        
    except Exception as e:
        utils.print_error(f"Error en backup automático: {e}")
        import traceback
        logger_mod.log_error_backup_auto(str(e), traceback.format_exc())
        
        try:
            rcon = CloudModuleLoader.load_module("rcon")
            if rcon and hasattr(rcon, 'enviar_comando'):
                rcon.enviar_comando("say [BACKUP] ERROR: Fallo en el backup automático")
        except Exception:
            pass

def start_autobackup(interval_minutes=None):
    global backup_timer, backup_timer_created_at
    
    if interval_minutes is None:
        interval_minutes = config.CONFIG.get("backup_interval_minutes", 30)
    
    if TimerManager.is_timer_active():
        logger_mod.log_timer_activo(os.getpid())
        return
    
    if backup_timer is not None and backup_timer.is_alive():
        logger_mod.log_timer_local_activo()
        return
    
    now = datetime.now(TIMEZONE_ARG)
    backup_timer_created_at = now
    
    def timer_callback():
        global backup_timer
        ejecutar_backup_automatico()
        
        if is_enabled():
            backup_timer = None
            TimerManager.clear_timer()
            start_autobackup(interval_minutes)
        else:
            logger_mod.log_autobackup_desactivado()
            backup_timer = None
            TimerManager.clear_timer()
    
    TimerManager.mark_timer_active(interval_minutes)
    logger_mod.log_timer_programado(interval_minutes, os.getpid())
    
    backup_timer = threading.Timer(interval_minutes * 60, timer_callback)
    backup_timer.daemon = True
    backup_timer.start()

def stop_autobackup():
    global backup_timer
    
    if backup_timer:
        backup_timer.cancel()
        backup_timer = None
        logger_mod.log_timer_detenido()
    
    TimerManager.clear_timer()

def toggle_autobackup():
    if is_enabled():
        stop_autobackup()
        disable()
        logger_mod.log_autobackup_desactivado_usuario()
    else:
        enable()
        start_autobackup()
        logger_mod.log_autobackup_activado_usuario()

def configurar_autobackup():
    backup = CloudModuleLoader.load_module("backup")
    if backup and hasattr(backup, 'configurar_autobackup'):
        backup.configurar_autobackup()
    else:
        utils.print_error("No se pudo cargar el módulo de configuración")
        utils.pausar()

def init_on_load():
    if is_enabled():
        logger_mod.log_autobackup_verificando()
        
        if not TimerManager.is_timer_active():
            logger_mod.log_timer_no_activo()
            start_autobackup()
        else:
            logger_mod.log_timer_otro_proceso()
    else:
        logger_mod.log_autobackup_no_habilitado()

import atexit

def cleanup_on_exit():
    global backup_timer
    if backup_timer and backup_timer.is_alive():
        backup_timer.cancel()
    TimerManager.clear_timer()

atexit.register(cleanup_on_exit)