"""
Sistema de autobackup automático para MegaCMD Manager
"""

import threading
import time
import os

# Cargar dependencias
config = CloudModuleLoader.load_module("config")
utils = CloudModuleLoader.load_module("utils")
backup = CloudModuleLoader.load_module("backup")

# Verificar que utils cargó correctamente
if not utils:
    import logging
    logger = logging.getLogger('megacmd')
    
    class TempUtils:
        logger = logger
        
        @staticmethod
        def print_msg(msg, icono="✓"):
            print(f"{icono} ⎹ {msg}")
        
        @staticmethod
        def print_error(msg):
            print(f"✖ ⎹ {msg}")
        
        @staticmethod
        def Spinner(msg):
            class DummySpinner:
                def __init__(self, mensaje):
                    self.mensaje = mensaje
                def start(self, proceso, check_file=None):
                    proceso.wait()
                    return True
            return DummySpinner(msg)
        
        @staticmethod
        def limpiar_pantalla():
            os.system('clear')
        
        @staticmethod
        def pausar():
            input("\n[+] Enter para continuar...")
        
        @staticmethod
        def confirmar(msg):
            return input(f"{msg} (s/n): ").strip().lower() == 's'
    
    utils = TempUtils()

# Variable global para el timer
backup_timer = None

# Archivo de control
AUTOBACKUP_FILE = os.path.expanduser("~/.megacmd_autobackup")

# ============================================
# FUNCIONES DE ESTADO
# ============================================

def is_enabled():
    """Verifica si el autobackup está habilitado"""
    try:
        if os.path.exists(AUTOBACKUP_FILE):
            with open(AUTOBACKUP_FILE, 'r') as f:
                return f.read().strip() == 'enabled'
        return False
    except:
        return False

def enable():
    """Habilita el autobackup"""
    try:
        with open(AUTOBACKUP_FILE, 'w') as f:
            f.write('enabled')
        utils.logger.info("Autobackup habilitado")
        return True
    except Exception as e:
        utils.logger.error(f"Error habilitando autobackup: {e}")
        return False

def disable():
    """Deshabilita el autobackup"""
    try:
        if os.path.exists(AUTOBACKUP_FILE):
            os.remove(AUTOBACKUP_FILE)
        utils.logger.info("Autobackup deshabilitado")
        return True
    except Exception as e:
        utils.logger.error(f"Error deshabilitando autobackup: {e}")
        return False

# ============================================
# FUNCIONES DE BACKUP
# ============================================

def ejecutar_backup_automatico():
    """Ejecuta un backup automático"""
    global backup_timer
    
    utils.logger.info("========== INICIO BACKUP AUTOMÁTICO ==========")
    utils.logger.info(f"Directorio de trabajo: {os.getcwd()}")
    
    try:
        # Verificar que el autobackup sigue habilitado
        if not is_enabled():
            utils.logger.info("Autobackup deshabilitado, cancelando ejecución")
            return
        
        # Mostrar mensaje en terminal
        print("\n" + "="*60)
        print("⏰ AUTO-BACKUP EJECUTÁNDOSE...")
        print("="*60)
        utils.logger.info("Mensaje de inicio mostrado en terminal")
        
        # Verificar que las dependencias están disponibles
        if not config or not backup:
            utils.logger.error("Módulos necesarios no disponibles")
            print("❌ Error: módulos no cargados")
            return
        
        # Obtener configuración
        server_folder = config.CONFIG.get("server_folder", "servidor_minecraft")
        backup_folder = config.CONFIG.get("backup_folder", "/backups")
        backup_prefix = config.CONFIG.get("backup_prefix", "MSX")
        
        utils.logger.info(f"Carpeta servidor: {server_folder}")
        utils.logger.info(f"Destino MEGA: {backup_folder}")
        
        # Verificar que la carpeta del servidor existe
        if not os.path.exists(server_folder):
            utils.logger.error(f"Carpeta {server_folder} no existe")
            print(f"❌ Error: {server_folder} no encontrado")
            return
        
        utils.logger.info(f"Carpeta {server_folder} verificada - existe en {os.path.abspath(server_folder)}")
        
        # Verificar que zip está disponible
        import shutil
        if not shutil.which("zip"):
            utils.logger.error("Comando zip no disponible")
            print("❌ Error: zip no instalado")
            return
        
        utils.logger.info("zip verificado - disponible")
        
        # Crear nombre de backup
        import datetime
        timestamp = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")
        backup_name = f"{backup_prefix}_{timestamp}.zip"
        
        utils.logger.info(f"Nombre de backup: {backup_name}")
        utils.logger.info(f"Destino MEGA: {backup_folder}")
        
        # Comprimir
        import subprocess
        
        cmd = ["zip", "-r", "-q", backup_name, server_folder]
        utils.logger.info(f"Iniciando compresión: {' '.join(cmd)}")
        
        proceso = subprocess.Popen(cmd)
        utils.logger.info(f"Proceso de compresión iniciado - PID: {proceso.pid}")
        
        spinner = utils.Spinner("Comprimiendo")
        
        # Usar check_file para verificar el archivo en vez del returncode
        if not spinner.start(proceso, check_file=backup_name):
            utils.logger.error("Error al comprimir")
            print("❌ Error en compresión")
            return
        
        # Verificar tamaño del archivo
        if os.path.exists(backup_name):
            size = os.path.getsize(backup_name)
            size_mb = size / (1024 * 1024)
            utils.logger.info(f"Archivo creado: {backup_name} ({size_mb:.1f} MB)")
            print(f"✓ Archivo creado: {backup_name} ({size_mb:.1f} MB)")
        else:
            utils.logger.error(f"Archivo {backup_name} no fue creado")
            print(f"❌ Archivo no creado")
            return
        
        # Subir a MEGA
        utils.logger.info("Iniciando subida a MEGA...")
        print("Subiendo a MEGA...")
        
        cmd_upload = ["mega-put", backup_name, backup_folder]
        proceso_upload = subprocess.Popen(cmd_upload, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        spinner_upload = utils.Spinner("Subiendo")
        if not spinner_upload.start(proceso_upload):
            utils.logger.error("Error al subir a MEGA")
            print("❌ Error en subida")
            # Limpiar archivo local aunque falle la subida
            try:
                os.remove(backup_name)
                utils.logger.info(f"Archivo local {backup_name} eliminado")
            except:
                pass
            return
        
        utils.logger.info(f"Backup subido exitosamente: {backup_name}")
        print(f"✅ Backup completado: {backup_name}")
        
        # Limpiar archivo local
        try:
            os.remove(backup_name)
            utils.logger.info(f"Archivo local {backup_name} eliminado")
        except Exception as e:
            utils.logger.warning(f"No se pudo eliminar archivo local: {e}")
        
        # Limpiar backups antiguos
        try:
            max_backups = config.CONFIG.get("max_backups", 5)
            utils.logger.info(f"Limpiando backups antiguos (mantener últimos {max_backups})...")
            
            # Listar backups
            cmd_list = ["mega-ls", backup_folder]
            result = subprocess.run(cmd_list, capture_output=True, text=True)
            
            if result.returncode == 0:
                archivos = [line.strip() for line in result.stdout.split('\n') if backup_prefix in line and '.zip' in line]
                archivos.sort(reverse=True)  # Más recientes primero
                
                utils.logger.info(f"Backups encontrados: {len(archivos)}")
                
                # Eliminar los más antiguos
                if len(archivos) > max_backups:
                    a_eliminar = archivos[max_backups:]
                    utils.logger.info(f"Eliminando {len(a_eliminar)} backups antiguos")
                    
                    for archivo in a_eliminar:
                        cmd_rm = ["mega-rm", f"{backup_folder}/{archivo}"]
                        subprocess.run(cmd_rm, capture_output=True)
                        utils.logger.info(f"Eliminado: {archivo}")
                        print(f"🗑️  Eliminado backup antiguo: {archivo}")
        
        except Exception as e:
            utils.logger.warning(f"Error limpiando backups antiguos: {e}")
        
        print("="*60 + "\n")
    
    except Exception as e:
        utils.logger.error(f"Error en backup automático: {e}")
        import traceback
        utils.logger.error(traceback.format_exc())
        print(f"❌ Error: {e}")
    
    finally:
        utils.logger.info("========== FIN BACKUP AUTOMÁTICO ==========")
        
        # Programar próximo backup
        if is_enabled():
            start_autobackup()

# ============================================
# CONTROL DEL TIMER
# ============================================

def start_autobackup():
    """Inicia el sistema de autobackup"""
    global backup_timer
    
    # Cancelar timer existente si hay
    if backup_timer:
        try:
            backup_timer.cancel()
            utils.logger.info("Timer anterior cancelado")
        except:
            pass
    
    if is_enabled():
        interval_seconds = config.CONFIG["backup_interval_minutes"] * 60
        backup_timer = threading.Timer(interval_seconds, ejecutar_backup_automatico)
        backup_timer.daemon = True
        backup_timer.start()
        utils.logger.info(f"Nuevo timer programado para {config.CONFIG['backup_interval_minutes']} minutos")

def stop_autobackup():
    """Detiene el sistema de autobackup"""
    global backup_timer
    
    if backup_timer:
        backup_timer.cancel()
        backup_timer = None
        utils.logger.info("Timer de autobackup cancelado")

# ============================================
# INTERFAZ DE USUARIO
# ============================================

def toggle_autobackup():
    """Menú de configuración de autobackup"""
    
    utils.limpiar_pantalla()
    
    print("\n" + "="*60)
    print("CONFIGURAR AUTOBACKUP")
    print("="*60 + "\n")
    
    # Mostrar estado actual
    if is_enabled():
        print("Estado actual: ACTIVADO ✔")
        print(f"El autobackup creará backups cada {config.CONFIG['backup_interval_minutes']} minutos\n")
    else:
        print("Estado actual: DESACTIVADO ✖\n")
    
    # Menú
    print("1. Activar autobackup")
    print("2. Desactivar autobackup")
    print("3. Configurar intervalo")
    print("4. Ejecutar backup ahora")
    print("5. Volver\n")
    
    opcion = input("Seleccioná una opción: ").strip()
    
    if opcion == "1":
        if enable():
            start_autobackup()
            utils.print_msg("Autobackup activado correctamente")
            print(f"Se ejecutará cada {config.CONFIG['backup_interval_minutes']} minutos")
        else:
            utils.print_error("Error al activar autobackup")
    
    elif opcion == "2":
        if disable():
            stop_autobackup()
            utils.print_msg("Autobackup desactivado correctamente")
        else:
            utils.print_error("Error al desactivar autobackup")
    
    elif opcion == "3":
        print("\n" + "="*60)
        print("CONFIGURAR INTERVALO")
        print("="*60 + "\n")
        
        print(f"Intervalo actual: {config.CONFIG['backup_interval_minutes']} minutos\n")
        
        try:
            nuevo_intervalo = int(input("Nuevo intervalo (en minutos): ").strip())
            
            if nuevo_intervalo < 1:
                utils.print_error("El intervalo debe ser al menos 1 minuto")
            else:
                config.CONFIG["backup_interval_minutes"] = nuevo_intervalo
                config.guardar_config()
                
                # Reiniciar timer si está activo
                if is_enabled():
                    start_autobackup()
                
                utils.print_msg(f"Intervalo actualizado a {nuevo_intervalo} minutos")
        
        except ValueError:
            utils.print_error("Intervalo inválido")
    
    elif opcion == "4":
        print("\n" + "="*60)
        print("EJECUTAR BACKUP MANUAL")
        print("="*60 + "\n")
        
        if utils.confirmar("¿Ejecutar backup ahora?"):
            ejecutar_backup_automatico()
        else:
            print("Cancelado")
    
    utils
