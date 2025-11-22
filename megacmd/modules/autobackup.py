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

def encontrar_carpeta_servidor(nombre_carpeta="servidor_minecraft"):
    """Encuentra la carpeta del servidor de forma inteligente"""
    # Importar desde backup si existe
    backup = CloudModuleLoader.load_module("backup")
    if backup and hasattr(backup, 'encontrar_carpeta_servidor'):
        return backup.encontrar_carpeta_servidor(nombre_carpeta)
    
    # Fallback básico
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

# ============================================================================
# MEJORA 1: Función ejecutar_backup_automatico() mejorada de ejecutar_backup_auto_simple.py
# ============================================================================
def ejecutar_backup_automatico():
    """Ejecuta el backup automático con logging detallado"""
    global backup_timer
    
    utils.logger.info("========== INICIO BACKUP AUTOMÁTICO ==========")
    
    try:
        # Actualizar actividad del timer
        TimerManager.update_activity()
        
        if not config.CONFIG.get("autobackup_enabled", False):
            utils.logger.info("Autobackup desactivado, no se ejecutará")
            return
        
        server_folder_config = config.CONFIG.get("server_folder", "servidor_minecraft")
        server_folder = encontrar_carpeta_servidor(server_folder_config)
        backup_folder = config.CONFIG.get("backup_folder", "/backups")
        backup_prefix = config.CONFIG.get("backup_prefix", "MSX")
        
        utils.logger.info(f"Configuración - Carpeta config: {server_folder_config}")
        utils.logger.info(f"Configuración - BASE_DIR: {config.BASE_DIR}")
        utils.logger.info(f"Configuración - os.getcwd(): {os.getcwd()}")
        utils.logger.info(f"Configuración - parent de BASE_DIR: {os.path.dirname(config.BASE_DIR)}")
        utils.logger.info(f"Configuración - Carpeta resuelta: {server_folder}")
        utils.logger.info(f"Configuración - ¿Existe? {os.path.exists(server_folder) if server_folder else False}")
        utils.logger.info(f"Configuración - Destino: {backup_folder}")
        
        if not server_folder or not os.path.exists(server_folder):
            utils.logger.error(f"Carpeta {server_folder_config} no encontrada, se cancela backup automático")
            return
        
        # Calcular tamaño
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
        
        # Crear nombre del backup
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        backup_name = f"{backup_prefix}_{timestamp}.zip"
        utils.logger.info(f"Nombre de backup: {backup_name}")
        
        # Comprimir
        utils.logger.info("Iniciando compresión...")
        cmd = ["zip", "-r", "-q", backup_name, server_folder]
        proceso = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if proceso.returncode != 0 or not os.path.exists(backup_name):
            utils.logger.error("Error durante compresión automática")
            return
        
        backup_size = os.path.getsize(backup_name)
        backup_size_mb = backup_size / (1024 * 1024)
        utils.logger.info(f"Archivo creado: {backup_name} ({backup_size_mb:.1f} MB)")
        
        # Subir a MEGA
        utils.logger.info("Iniciando subida a MEGA...")
        cmd_upload = ["mega-put", "-q", backup_name, backup_folder]
        proceso_upload = subprocess.run(cmd_upload, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if proceso_upload.returncode != 0:
            utils.logger.error("Error al subir backup automático a MEGA")
            try:
                os.remove(backup_name)
            except:
                pass
            return
        
        utils.logger.info(f"Backup automático subido exitosamente: {backup_folder}/{backup_name}")
        
        # Eliminar archivo local
        try:
            os.remove(backup_name)
            utils.logger.info("Archivo local eliminado")
        except Exception as e:
            utils.logger.warning(f"No se pudo eliminar archivo local: {e}")
        
        utils.logger.info("========== FIN BACKUP AUTOMÁTICO ==========")
        
    except Exception as e:
        utils.logger.error(f"Error en backup automático: {str(e)}")
        import traceback
        utils.logger.error(traceback.format_exc())

def start_autobackup(interval_minutes=None):
    """Inicia el timer de autobackup"""
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
    """Detiene el timer de autobackup"""
    global backup_timer
    
    if backup_timer:
        backup_timer.cancel()
        backup_timer = None
        utils.logger.info("Timer de autobackup detenido")
    
    # Limpiar el archivo de lock
    TimerManager.clear_timer()

def toggle_autobackup():
    """Alterna el estado del autobackup"""
    if is_enabled():
        stop_autobackup()
        disable()
        utils.logger.info("Autobackup desactivado por usuario")
    else:
        enable()
        start_autobackup()
        utils.logger.info("Autobackup activado por usuario")

# ============================================================================
# MEJORA 2: Función configurar_autobackup() de configurar_autobackup_mejorado.py
# ============================================================================
def configurar_autobackup():
    """
    Menú interactivo para configurar el autobackup
    """
    # Verificar MegaCMD
    if not utils.verificar_megacmd():
        utils.print_error("MegaCMD no está disponible")
        utils.pausar()
        return
    
    while True:
        utils.limpiar_pantalla()
        print("\n" + "=" * 60)
        print("CONFIGURAR AUTOBACKUP")
        print("=" * 60 + "\n")
        
        # Obtener configuración actual
        autobackup_enabled = config.CONFIG.get("autobackup_enabled", False)
        intervalo_actual = config.CONFIG.get("backup_interval_minutes", 5)
        backup_folder = config.CONFIG.get("backup_folder", "/backups")
        server_folder = config.CONFIG.get("server_folder", "servidor_minecraft")
        max_backups = config.CONFIG.get("max_backups", 5)
        
        # Mostrar configuración actual
        print("📋 CONFIGURACIÓN ACTUAL:")
        print(f"   Estado: {'✓ ACTIVADO' if autobackup_enabled else '✗ DESACTIVADO'}")
        print(f"   Intervalo: cada {intervalo_actual} minutos")
        print(f"   Carpeta servidor: {server_folder}")
        print(f"   Destino MEGA: {backup_folder}")
        print(f"   Máximo backups: {max_backups}")
        print()
        
        utils.logger.info("========== MENÚ CONFIGURAR AUTOBACKUP ==========")
        
        # Menú de opciones
        print("OPCIONES:")
        if autobackup_enabled:
            print("   1. Desactivar autobackup")
        else:
            print("   1. Activar autobackup")
        
        print("   2. Cambiar intervalo de autobackup")
        print("   3. Cambiar ruta de guardado")
        print("   4. Cambiar backups máximos")
        print("   0. Volver")
        print()
        
        opcion = input("Seleccione una opción: ").strip()
        
        if opcion == "1":
            # Activar/Desactivar
            if autobackup_enabled:
                config.CONFIG["autobackup_enabled"] = False
                config.guardar_config()
                stop_autobackup()
                utils.print_msg("Autobackup desactivado")
                utils.logger.info("Autobackup desactivado por usuario")
            else:
                config.CONFIG["autobackup_enabled"] = True
                config.guardar_config()
                utils.print_msg("Autobackup activado")
                utils.logger.info("Autobackup activado por usuario")
                print("\n⚠️  Nota: Reinicie el addon para aplicar los cambios")
            
            utils.pausar()
        
        elif opcion == "2":
            # Cambiar intervalo
            print(f"\n⏱️  Intervalo actual: {intervalo_actual} minutos")
            while True:
                try:
                    nuevo_intervalo = input("   Nuevo intervalo en minutos (1-60): ").strip()
                    if not nuevo_intervalo:
                        break
                    
                    nuevo_intervalo = int(nuevo_intervalo)
                    if 1 <= nuevo_intervalo <= 60:
                        config.CONFIG["backup_interval_minutes"] = nuevo_intervalo
                        config.guardar_config()
                        utils.print_msg(f"Intervalo cambiado a {nuevo_intervalo} minutos")
                        utils.logger.info(f"Intervalo cambiado a {nuevo_intervalo} minutos")
                        break
                    else:
                        utils.print_warning("Intervalo debe estar entre 1 y 60 minutos")
                except ValueError:
                    utils.print_warning("Ingrese un número válido")
                except KeyboardInterrupt:
                    print("\nCancelado")
                    break
            
            utils.pausar()
        
        elif opcion == "3":
            # Cambiar ruta de guardado
            print(f"\n☁️  Destino MEGA actual: {backup_folder}\n")
            nuevo_destino = input("   Nueva carpeta MEGA (ej: /backups): ").strip()
            if nuevo_destino:
                if not nuevo_destino.startswith("/"):
                    nuevo_destino = "/" + nuevo_destino
                
                config.CONFIG["backup_folder"] = nuevo_destino
                config.guardar_config()
                utils.print_msg(f"Carpeta cambiada a: {nuevo_destino}")
                utils.logger.info(f"Destino MEGA cambiado a: {nuevo_destino}")
            
            utils.pausar()
        
        elif opcion == "4":
            # Cambiar máximo de backups
            print(f"\n🗂️  Máximo de backups actual: {max_backups}")
            print("💡 Recomendado: 5 backups")
            while True:
                try:
                    nuevo_max = input("   Nueva cantidad máxima (1-20): ").strip()
                    if not nuevo_max:
                        break
                    
                    nuevo_max = int(nuevo_max)
                    if 1 <= nuevo_max <= 20:
                        config.CONFIG["max_backups"] = nuevo_max
                        config.guardar_config()
                        utils.print_msg(f"Máximo de backups cambiado a {nuevo_max}")
                        utils.logger.info(f"Máximo de backups cambiado a {nuevo_max}")
                        break
                    else:
                        utils.print_warning("Cantidad debe estar entre 1 y 20")
                except ValueError:
                    utils.print_warning("Ingrese un número válido")
                except KeyboardInterrupt:
                    print("\nCancelado")
                    break
            
            utils.pausar()
        
        elif opcion == "0":
            utils.logger.info("Saliendo de configuración de autobackup")
            break
        
        else:
            utils.print_warning("Opción inválida")
            utils.pausar()

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
