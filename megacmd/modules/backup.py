"""
Módulo de gestión de backups para MegaCMD Manager
"""

import os
import subprocess
from datetime import datetime

# Cargar dependencias
config = CloudModuleLoader.load_module("config")
utils = CloudModuleLoader.load_module("utils")
megacmd = CloudModuleLoader.load_module("megacmd")

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
        def print_warning(msg):
            print(f"⚠ ⎹ {msg}")
        
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
        
        @staticmethod
        def formato_bytes(b):
            for u in ['B', 'KB', 'MB', 'GB']:
                if b < 1024:
                    return f"{b:.1f} {u}"
                b /= 1024
            return f"{b:.1f} TB"
        
        @staticmethod
        def formato_fecha(ts=None):
            from datetime import datetime
            if ts is None:
                dt = datetime.now()
            else:
                dt = datetime.fromtimestamp(ts)
            return dt.strftime('%d-%m-%Y_%H-%M')
    
    utils = TempUtils()

# ============================================
# FUNCIÓN PRINCIPAL DE BACKUP
# ============================================

def crear_backup():
    """Crea un backup manual del servidor"""
    
    utils.limpiar_pantalla()
    
    print("\n" + "="*60)
    print("CREAR BACKUP EN MEGA")
    print("="*60 + "\n")
    
    utils.logger.info("========== INICIO BACKUP MANUAL ==========")
    
    try:
        # Verificar dependencias
        if not megacmd.verificar_megacmd():
            utils.print_error("MegaCMD no está disponible")
            utils.pausar()
            return
        
        # Obtener configuración
        server_folder = config.CONFIG.get("server_folder", "servidor_minecraft")
        backup_folder = config.CONFIG.get("backup_folder", "/backups")
        backup_prefix = config.CONFIG.get("backup_prefix", "MSX")
        
        utils.logger.info(f"Configuración - Carpeta: {server_folder}, Destino: {backup_folder}")
        
        # Verificar que la carpeta del servidor existe
        if not os.path.exists(server_folder):
            utils.print_error(f"La carpeta {server_folder} no existe")
            utils.logger.error(f"Carpeta {server_folder} no encontrada")
            utils.pausar()
            return
        
        # Calcular tamaño
        print(f"📁 Carpeta: {server_folder}")
        print("📊 Calculando tamaño...")
        
        import shutil
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(server_folder):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except:
                    pass
        
        size_mb = total_size / (1024 * 1024)
        print(f"📦 Tamaño total: {size_mb:.1f} MB\n")
        
        utils.logger.info(f"Tamaño de carpeta: {size_mb:.1f} MB")
        
        # Confirmar
        if not utils.confirmar("¿Crear backup ahora?"):
            print("Cancelado")
            utils.logger.info("Backup cancelado por usuario")
            utils.pausar()
            return
        
        print()
        
        # Crear nombre de backup
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        backup_name = f"{backup_prefix}_{timestamp}.zip"
        
        utils.logger.info(f"Nombre de backup: {backup_name}")
        
        # Comprimir
        utils.logger.info("Iniciando compresión...")
        
        cmd = ["zip", "-r", "-q", backup_name, server_folder]
        proceso = subprocess.Popen(cmd)
        
        spinner = utils.Spinner("Comprimiendo")
        
        # Usar check_file para verificar el archivo
        if not spinner.start(proceso, check_file=backup_name):
            utils.print_error("Error al comprimir")
            utils.logger.error("Fallo en compresión")
            utils.pausar()
            return
        
        # Verificar archivo creado
        if not os.path.exists(backup_name):
            utils.print_error("El archivo ZIP no se creó")
            utils.logger.error(f"Archivo {backup_name} no encontrado")
            utils.pausar()
            return
        
        backup_size = os.path.getsize(backup_name)
        backup_size_mb = backup_size / (1024 * 1024)
        
        utils.logger.info(f"Archivo creado: {backup_name} ({backup_size_mb:.1f} MB)")
        print(f"✓ Archivo creado: {backup_name} ({backup_size_mb:.1f} MB)\n")
        
        # Subir a MEGA
        utils.logger.info("Iniciando subida a MEGA...")
        
        cmd_upload = ["mega-put", backup_name, backup_folder]
        proceso_upload = subprocess.Popen(cmd_upload, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        spinner_upload = utils.Spinner("Subiendo a MEGA")
        if not spinner_upload.start(proceso_upload):
            utils.print_error("Error al subir a MEGA")
            utils.logger.error("Fallo en subida a MEGA")
            
            # Limpiar archivo local
            try:
                os.remove(backup_name)
                utils.logger.info("Archivo local eliminado tras error")
            except:
                pass
            
            utils.pausar()
            return
        
        utils.logger.info(f"Backup subido exitosamente a {backup_folder}/{backup_name}")
        
        # Limpiar archivo local
        try:
            os.remove(backup_name)
            utils.logger.info("Archivo local eliminado")
        except Exception as e:
            utils.print_warning(f"No se pudo eliminar archivo local: {e}")
            utils.logger.warning(f"Error eliminando archivo local: {e}")
        
        # Éxito
        print()
        utils.print_msg(f"Backup creado exitosamente: {backup_name}")
        utils.logger.info("========== FIN BACKUP MANUAL ==========")
        
        # Limpiar backups antiguos
        print()
        if utils.confirmar("¿Limpiar backups antiguos ahora?"):
            limpiar_backups_antiguos()
    
    except Exception as e:
        utils.print_error(f"Error creando backup: {e}")
        utils.logger.error(f"Error en crear_backup: {e}")
        import traceback
        utils.logger.error(traceback.format_exc())
    
    utils.pausar()

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def limpiar_backups_antiguos():
    """Limpia backups antiguos según configuración"""
    
    try:
        max_backups = config.CONFIG.get("max_backups", 5)
        backup_folder = config.CONFIG.get("backup_folder", "/backups")
        backup_prefix = config.CONFIG.get("backup_prefix", "MSX")
        
        utils.logger.info(f"Limpiando backups antiguos (mantener {max_backups})...")
        
        print(f"\n🧹 Limpiando backups antiguos (mantener últimos {max_backups})...")
        
        # Listar backups
        cmd_list = ["mega-ls", backup_folder]
        result = subprocess.run(cmd_list, capture_output=True, text=True)
        
        if result.returncode != 0:
            utils.print_error("No se pudo listar backups en MEGA")
            utils.logger.error("Error listando backups")
            return
        
        # Filtrar backups
        archivos = [line.strip() for line in result.stdout.split('\n') if backup_prefix in line and '.zip' in line]
        archivos.sort(reverse=True)  # Más recientes primero
        
        utils.logger.info(f"Backups encontrados: {len(archivos)}")
        print(f"📦 Backups encontrados: {len(archivos)}")
        
        if len(archivos) <= max_backups:
            utils.print_msg("No hay backups antiguos para eliminar")
            return
        
        # Eliminar antiguos
        a_eliminar = archivos[max_backups:]
        
        print(f"\n🗑️  Eliminando {len(a_eliminar)} backups antiguos:")
        
        for archivo in a_eliminar:
            print(f"   - {archivo}")
            cmd_rm = ["mega-rm", f"{backup_folder}/{archivo}"]
            result_rm = subprocess.run(cmd_rm, capture_output=True, text=True)
            
            if result_rm.returncode == 0:
                utils.logger.info(f"Eliminado: {archivo}")
            else:
                utils.logger.warning(f"Error eliminando {archivo}")
        
        utils.print_msg(f"Limpieza completada - {len(a_eliminar)} backups eliminados")
    
    except Exception as e:
        utils.print_error(f"Error limpiando backups: {e}")
        utils.logger.error(f"Error en limpiar_backups_antiguos: {e}")
