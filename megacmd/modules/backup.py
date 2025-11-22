import os
import subprocess
from datetime import datetime

config = CloudModuleLoader.load_module("config")
utils = CloudModuleLoader.load_module("utils")

def encontrar_carpeta_servidor(nombre_carpeta="servidor_minecraft"):
    """
    Encuentra la carpeta del servidor de forma inteligente.
    Busca en múltiples ubicaciones comunes.
    """
    # Lista de ubicaciones a verificar
    ubicaciones_a_verificar = [
        # 1. Ruta absoluta directa en /workspaces
        f"/workspaces/{os.environ.get('CODESPACE_NAME', 'unknown')}/{nombre_carpeta}",
        
        # 2. Buscar en /workspaces/*/servidor_minecraft
        None,  # Se busca dinámicamente
        
        # 3. Relativo desde getcwd()
        os.path.join(os.getcwd(), nombre_carpeta),
        
        # 4. Subir un nivel desde getcwd()
        os.path.join(os.path.dirname(os.getcwd()), nombre_carpeta),
        
        # 5. En el home del usuario
        os.path.expanduser(f"~/{nombre_carpeta}"),
    ]
    
    # Verificar ubicaciones directas
    for ubicacion in ubicaciones_a_verificar:
        if ubicacion and os.path.exists(ubicacion) and os.path.isdir(ubicacion):
            utils.logger.info(f"Carpeta del servidor encontrada en: {ubicacion}")
            return ubicacion
    
    # Búsqueda dinámica en /workspaces
    try:
        if os.path.exists("/workspaces"):
            for item in os.listdir("/workspaces"):
                ruta_posible = os.path.join("/workspaces", item, nombre_carpeta)
                if os.path.exists(ruta_posible) and os.path.isdir(ruta_posible):
                    utils.logger.info(f"Carpeta del servidor encontrada en: {ruta_posible}")
                    return ruta_posible
    except:
        pass
    
    # Si no se encuentra, retornar None
    utils.logger.error(f"No se pudo encontrar la carpeta '{nombre_carpeta}'")
    return None

def ejecutar_backup_manual():
    utils.limpiar_pantalla()
    print("\n" + "=" * 60)
    print("CREAR BACKUP EN MEGA")
    print("=" * 60 + "\n")
    utils.logger.info("========== INICIO BACKUP MANUAL ==========")
    try:
        if not utils.verificar_megacmd():
            utils.print_error("MegaCMD no está disponible")
            utils.pausar()
            return

        # Obtener ruta y resolverla correctamente
        server_folder_config = config.CONFIG.get("server_folder", "servidor_minecraft")
        # CORRECCIÓN: Usar encontrar_carpeta_servidor en lugar de resolver_ruta_servidor
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

        # Verificar que se encontró la carpeta
        if not server_folder or not os.path.exists(server_folder):
            utils.print_error(f"La carpeta {server_folder_config} no se pudo encontrar")
            utils.logger.error(f"Carpeta {server_folder_config} no encontrada")
            utils.pausar()
            return

        print(f"📁 Carpeta: {server_folder}")
        print("📊 Calculando tamaño...")
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

        if not utils.confirmar("¿Crear backup ahora?"):
            print("Cancelado")
            utils.logger.info("Backup cancelado por usuario")
            utils.pausar()
            return

        print()
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        backup_name = f"{backup_prefix}_{timestamp}.zip"

        utils.logger.info(f"Nombre de backup: {backup_name}")
        utils.logger.info("Iniciando compresión...")

        cmd = ["zip", "-r", "-q", backup_name, server_folder]
        proceso = subprocess.Popen(cmd)
        spinner = utils.Spinner("Comprimiendo")
        if not spinner.start(proceso, check_file=backup_name):
            utils.print_error("Error al comprimir")
            utils.logger.error("Fallo en compresión")
            utils.pausar()
            return

        if not os.path.exists(backup_name):
            utils.print_error("El archivo ZIP no se creó")
            utils.logger.error(f"Archivo {backup_name} no encontrado")
            utils.pausar()
            return

        backup_size = os.path.getsize(backup_name)
        backup_size_mb = backup_size / (1024 * 1024)
        utils.logger.info(f"Archivo creado: {backup_name} ({backup_size_mb:.1f} MB)")
        print(f"✓ Archivo creado: {backup_name} ({backup_size_mb:.1f} MB)\n")

        utils.logger.info("Iniciando subida a MEGA...")

        cmd_upload = ["mega-put", backup_name, backup_folder]
        proceso_upload = subprocess.Popen(cmd_upload, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        spinner_upload = utils.Spinner("Subiendo a MEGA")
        if not spinner_upload.start(proceso_upload):
            utils.print_error("Error al subir a MEGA")
            utils.logger.error("Fallo en subida a MEGA")
            try:
                os.remove(backup_name)
                utils.logger.info("Archivo local eliminado tras error")
            except:
                pass
            utils.pausar()
            return

        utils.logger.info(f"Backup subido exitosamente a {backup_folder}/{backup_name}")
        try:
            os.remove(backup_name)
            utils.logger.info("Archivo local eliminado")
        except Exception as e:
            utils.print_warning(f"No se pudo eliminar archivo local: {e}")
            utils.logger.warning(f"Error eliminando archivo local: {e}")

        print()
        utils.print_msg(f"Backup creado exitosamente: {backup_name}")
        utils.logger.info("========== FIN BACKUP MANUAL ==========")
        print()

        if utils.confirmar("¿Limpiar backups antiguos ahora?"):
            limpiar_backups_antiguos()
    except Exception as e:
        utils.print_error(f"Error creando backup: {e}")
        utils.logger.error(f"Error en crear_backup: {e}")
        import traceback
        utils.logger.error(traceback.format_exc())
        utils.pausar()

def ejecutar_backup_automatico():
    utils.logger.info("========== INICIO BACKUP AUTOMÁTICO ==========")
    try:
        # Obtener ruta y resolverla correctamente
        server_folder_config = config.CONFIG.get("server_folder", "servidor_minecraft")
        # CORRECCIÓN: Usar encontrar_carpeta_servidor en lugar de resolver_ruta_servidor
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

        # Verificar que se encontró la carpeta
        if not server_folder or not os.path.exists(server_folder):
            utils.logger.error(f"Carpeta {server_folder_config} no encontrada, se cancela backup automático")
            return

        # logística igual a backup manual pero sin mensajes ni pausas
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

        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        backup_name = f"{backup_prefix}_{timestamp}.zip"
        utils.logger.info(f"Nombre de backup: {backup_name}")

        # compresión
        cmd = ["zip", "-r", "-q", backup_name, server_folder]
        proceso = subprocess.run(cmd)
        if proceso.returncode != 0 or not os.path.exists(backup_name):
            utils.logger.error("Error durante compresión automática")
            return

        backup_size = os.path.getsize(backup_name)
        backup_size_mb = backup_size / (1024 * 1024)
        utils.logger.info(f"Archivo creado: {backup_name} ({backup_size_mb:.1f} MB)")

        # subida a MEGA
        cmd_upload = ["mega-put", backup_name, backup_folder]
        proceso_upload = subprocess.run(cmd_upload)
        if proceso_upload.returncode != 0:
            utils.logger.error("Error al subir backup automático a MEGA")
            try:
                os.remove(backup_name)
            except:
                pass
            return

        utils.logger.info(f"Backup automático subido exitosamente: {backup_folder}/{backup_name}")

        try:
            os.remove(backup_name)
            utils.logger.info("Archivo local eliminado")
        except Exception as e:
            utils.logger.warning(f"No se pudo eliminar archivo local: {e}")

        utils.logger.info("========== FIN BACKUP AUTOMÁTICO ==========")

    except Exception as e:
        utils.logger.error(f"Error en backup automático: {str(e)}")

def limpiar_backups_antiguos():
    try:
        max_backups = config.CONFIG.get("max_backups", 5)
        backup_folder = config.CONFIG.get("backup_folder", "/backups")
        backup_prefix = config.CONFIG.get("backup_prefix", "MSX")
        utils.logger.info(f"Limpiando backups antiguos (mantener {max_backups})...")
        cmd_list = ["mega-ls", backup_folder]
        result = subprocess.run(cmd_list, capture_output=True, text=True)
        if result.returncode != 0:
            utils.logger.error("Error listando backups")
            return
        archivos = [line.strip() for line in result.stdout.split('\n') if backup_prefix in line and '.zip' in line]
        archivos.sort(reverse=True)
        utils.logger.info(f"Backups encontrados: {len(archivos)}")
        if len(archivos) <= max_backups:
            return
        a_eliminar = archivos[max_backups:]
        for archivo in a_eliminar:
            cmd_rm = ["mega-rm", f"{backup_folder}/{archivo}"]
            result_rm = subprocess.run(cmd_rm, capture_output=True, text=True)
            if result_rm.returncode == 0:
                utils.logger.info(f"Eliminado: {archivo}")
            else:
                utils.logger.warning(f"Error eliminando {archivo}")
        utils.logger.info(f"Limpieza completada - {len(a_eliminar)} backups eliminados")
    except Exception as e:
        utils.logger.error(f"Error en limpiar_backups_antiguos: {e}")