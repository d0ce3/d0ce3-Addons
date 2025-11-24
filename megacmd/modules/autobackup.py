import threading
import os
import subprocess
import json
import time
from datetime import datetime, timedelta, timezone

config = CloudModuleLoader.load_module("config")
utils = CloudModuleLoader.load_module("utils")
logger_mod = CloudModuleLoader.load_module("logger")
megacmd = CloudModuleLoader.load_module("megacmd")

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

def _notify_rcon_error(mensaje):
    try:
        rcon = CloudModuleLoader.load_module("rcon")
        if rcon and rcon.is_connected():
            rcon.send_command(f"say [BACKUP ERROR] {mensaje}")
    except:
        pass

def encontrar_carpeta_servidor(nombre_carpeta="servidor_minecraft"):
    ubicaciones_a_verificar = [
        f"/workspaces/{os.environ.get('CODESPACE_NAME', 'unknown')}/{nombre_carpeta}",
        None,
        os.path.join(os.getcwd(), nombre_carpeta),
        os.path.join(os.path.dirname(os.getcwd()), nombre_carpeta),
        os.path.expanduser(f"~/{nombre_carpeta}"),
    ]
    
    for ubicacion in ubicaciones_a_verificar:
        if ubicacion and os.path.exists(ubicacion) and os.path.isdir(ubicacion):
            utils.logger.info(f"Carpeta del servidor encontrada en: {ubicacion}")
            return ubicacion
    
    try:
        if os.path.exists("/workspaces"):
            for item in os.listdir("/workspaces"):
                ruta_posible = os.path.join("/workspaces", item, nombre_carpeta)
                if os.path.exists(ruta_posible) and os.path.isdir(ruta_posible):
                    utils.logger.info(f"Carpeta del servidor encontrada en: {ruta_posible}")
                    return ruta_posible
    except:
        pass
    
    utils.logger.error(f"No se pudo encontrar la carpeta '{nombre_carpeta}'")
    return None

def ejecutar_backup_automatico():
    logger_mod.log_backup_auto_inicio()
    
    try:
        if not config.CONFIG.get("autobackup_enabled", False):
            utils.logger.info("Autobackup desactivado, no se ejecutará")
            return
        
        server_folder_config = config.CONFIG.get("server_folder", "servidor_minecraft")
        server_folder = encontrar_carpeta_servidor(server_folder_config)
        backup_folder = config.CONFIG.get("backup_folder", "/backups")
        backup_prefix = config.CONFIG.get("backup_prefix", "MSX")
        
        utils.logger.info(f"Configuración - Carpeta config: {server_folder_config}")
        utils.logger.info(f"Configuración - BASEDIR: {config.BASEDIR}")
        utils.logger.info(f"Configuración - os.getcwd(): {os.getcwd()}")
        utils.logger.info(f"Configuración - parent de BASEDIR: {os.path.dirname(config.BASEDIR)}")
        utils.logger.info(f"Configuración - Carpeta resuelta: {server_folder}")
        utils.logger.info(f"Configuración - ¿Existe? {os.path.exists(server_folder) if server_folder else False}")
        utils.logger.info(f"Configuración - Destino: {backup_folder}")
        
        if not server_folder or not os.path.exists(server_folder):
            error_msg = f"Carpeta {server_folder_config} no encontrada"
            utils.logger.error(error_msg)
            _notify_rcon_error(error_msg)
            logger_mod.log_backup_auto_error(error_msg)
            return
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(server_folder):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except:
                    pass
        
        size_mb = total_size / (1024 * 1024)
        utils.logger.info(f"Tamaño de carpeta: {size_mb:.1f} MB")
        
        timestamp = datetime.now(TIMEZONE_ARG).strftime("%d-%m-%Y_%H-%M")
        backup_name = f"{backup_prefix}_{timestamp}.zip"
        
        utils.logger.info(f"Nombre de backup: {backup_name}")
        utils.logger.info("Iniciando compresión...")
        
        cmd = ["zip", "-r", "-q", backup_name, server_folder]
        proceso = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
        
        if proceso.returncode != 0 or not os.path.exists(backup_name):
            error_msg = "Error durante compresión automática"
            utils.logger.error(error_msg)
            _notify_rcon_error(error_msg)
            logger_mod.log_backup_auto_error(error_msg)
            return
        
        backup_size = os.path.getsize(backup_name)
        backup_size_mb = backup_size / (1024 * 1024)
        utils.logger.info(f"Archivo creado: {backup_name} ({backup_size_mb:.1f} MB)")
        
        utils.logger.info("Iniciando subida a MEGA...")
        
        result = megacmd.upload_file(backup_name, backup_folder, silent=True)
        
        if result.returncode != 0:
            error_msg = "Error al subir backup a MEGA"
            utils.logger.error(error_msg)
            _notify_rcon_error(error_msg)
            logger_mod.log_backup_auto_error(error_msg)
            try:
                os.remove(backup_name)
            except:
                pass
            return
        
        utils.logger.info(f"Backup automático subido exitosamente: {backup_folder}/{backup_name}")
        logger_mod.log_backup_auto_exito(backup_name, backup_size_mb)
        
        try:
            os.remove(backup_name)
            utils.logger.info("Archivo local eliminado")
        except Exception as e:
            utils.logger.warning(f"No se pudo eliminar archivo local: {e}")
        
        TimerManager.update_activity()
        
    except Exception as e:
        error_msg = f"Error en backup automático: {str(e)}"
        utils.logger.error(error_msg)
        _notify_rcon_error(error_msg)
        logger_mod.log_backup_auto_error(error_msg)

def limpiar_backups_antiguos():
    try:
        max_backups = config.CONFIG.get("max_backups", 5)
        backup_folder = config.CONFIG.get("backup_folder", "/backups")
        backup_prefix = config.CONFIG.get("backup_prefix", "MSX")
        
        utils.logger.info(f"Limpiando backups antiguos (mantener {max_backups})...")
        
        result = megacmd.list_files(backup_folder)
        
        if result.returncode != 0:
            utils.logger.error("Error listando backups")
            return
        
        archivos = [line.strip() for line in result.stdout.split('\n') 
                   if backup_prefix in line and '.zip' in line]
        archivos.sort(reverse=True)
        
        utils.logger.info(f"Backups encontrados: {len(archivos)}")
        
        if len(archivos) <= max_backups:
            return
        
        a_eliminar = archivos[max_backups:]
        
        for archivo in a_eliminar:
            result_rm = megacmd.remove_file(f"{backup_folder}/{archivo}")
            
            if result_rm.returncode == 0:
                utils.logger.info(f"Eliminado: {archivo}")
            else:
                utils.logger.warning(f"Error eliminando {archivo}")
        
        utils.logger.info(f"Limpieza completada - {len(a_eliminar)} backups eliminados")
    
    except Exception as e:
        utils.logger.error(f"Error en limpiar_backups_antiguos: {e}")

def _ejecutar_backup():
    try:
        ejecutar_backup_automatico()
    except Exception as e:
        error_msg = f"Error ejecutando backup: {e}"
        utils.logger.error(error_msg)
        _notify_rcon_error(error_msg)
    
    try:
        limpiar_backups_antiguos()
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
    return start_autobackup()

def disable():
    config.set("autobackup_enabled", False)
    utils.logger.info("Autobackup deshabilitado")
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
