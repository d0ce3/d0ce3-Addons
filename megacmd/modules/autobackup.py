import threading
import os
import subprocess
from datetime import datetime

config = CloudModuleLoader.load_module("config")
utils = CloudModuleLoader.load_module("utils")
backup = CloudModuleLoader.load_module("backup")

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

backup_timer = None
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
    utils.logger.info("========== INICIO BACKUP AUTOMÁTICO ==========")
    utils.logger.info(f"Directorio de trabajo: {os.getcwd()}")

    try:
        if not is_enabled():
            utils.logger.info("Autobackup deshabilitado, cancelando ejecución")
            return

        print("\n" + "="*60)
        print("⏰ AUTO-BACKUP EJECUTÁNDOSE...")
        print("="*60)
        utils.logger.info("Mensaje de inicio mostrado en terminal")

        if not config or not backup:
            utils.logger.error("Módulos necesarios no disponibles")
            print("❌ Error: módulos no cargados")
            return

        server_folder = config.CONFIG.get("server_folder", "servidor_minecraft")
        backup_folder = config.CONFIG.get("backup_folder", "/backups")
        backup_prefix = config.CONFIG.get("backup_prefix", "MSX")

        utils.logger.info(f"Configuración - Carpeta: {server_folder}, Destino: {backup_folder}")

        if os.path.basename(os.getcwd()) == server_folder:
            compress_target = "."
            utils.logger.info(f"Ejecutando desde dentro del servidor: {os.getcwd()}")
        elif os.path.exists(server_folder):
            compress_target = server_folder
            utils.logger.info(f"Carpeta {server_folder} encontrada en {os.getcwd()}")
        else:
            utils.logger.error(f"Carpeta {server_folder} no existe en {os.getcwd()}")
            print(f"❌ Error: {server_folder} no encontrado")
            return

        import shutil
        if not shutil.which("zip"):
            utils.logger.error("Comando zip no disponible")
            print("❌ Error: zip no instalado")
            return

        utils.logger.info("zip verificado - disponible")

        import datetime
        timestamp = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")
        backup_name = f"{backup_prefix}_{timestamp}.zip"

        utils.logger.info(f"Nombre de backup: {backup_name}")
        utils.logger.info(f"Target de compresión: {compress_target}")

        import subprocess
        cmd = ["zip", "-r", "-q", backup_name, compress_target]
        utils.logger.info(f"Comando: {' '.join(cmd)}")

        proceso = subprocess.Popen(cmd)
        utils.logger.info(f"Proceso iniciado - PID: {proceso.pid}")

        spinner = utils.Spinner("Comprimiendo")

        if not spinner.start(proceso, check_file=backup_name):
            utils.logger.error("Error al comprimir")
            print("❌ Error en compresión")
            return

        if os.path.exists(backup_name):
            size = os.path.getsize(backup_name)
            size_mb = size / (1024 * 1024)
            utils.logger.info(f"Archivo creado: {backup_name} ({size_mb:.1f} MB)")
            print(f"✓ Archivo creado: {backup_name} ({size_mb:.1f} MB)")
        else:
            utils.logger.error(f"Archivo {backup_name} no fue creado")
            print(f"❌ Archivo no creado")
            return

        utils.logger.info("Iniciando subida a MEGA...")
        print("Subiendo a MEGA...")

        cmd_upload = ["mega-put", backup_name, backup_folder]
        proceso_upload = subprocess.Popen(cmd_upload, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        spinner_upload = utils.Spinner("Subiendo")
        if not spinner_upload.start(proceso_upload):
            utils.logger.error("Error al subir a MEGA")
            print("❌ Error en subida")
            try:
                os.remove(backup_name)
                utils.logger.info(f"Archivo local {backup_name} eliminado")
            except:
                pass
            return

        utils.logger.info(f"Backup subido exitosamente: {backup_name}")
        print(f"✅ Backup completado: {backup_name}")

        try:
            os.remove(backup_name)
            utils.logger.info(f"Archivo local {backup_name} eliminado")
        except Exception as e:
            utils.logger.warning(f"No se pudo eliminar archivo local: {e}")

        try:
            max_backups = config.CONFIG.get("max_backups", 5)
            utils.logger.info(f"Limpiando backups antiguos (mantener últimos {max_backups})...")

            cmd_list = ["mega-ls", backup_folder]
            result = subprocess.run(cmd_list, capture_output=True, text=True)

            if result.returncode == 0:
                archivos = [line.strip() for line in result.stdout.split('\n') if backup_prefix in line and '.zip' in line]
                archivos.sort(reverse=True)

                utils.logger.info(f"Backups encontrados: {len(archivos)}")

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

        if is_enabled():
            start_autobackup()

def start_autobackup():
    global backup_timer

    if backup_timer:
        backup_timer.cancel()
        backup_timer = None

    if is_enabled():
        interval_seconds = config.CONFIG["backup_interval_minutes"] * 60
        backup_timer = threading.Timer(interval_seconds, ejecutar_backup_automatico)
        backup_timer.daemon = True
        backup_timer.start()
        utils.logger.info(f"Nuevo timer programado para {config.CONFIG['backup_interval_minutes']} minutos")

def stop_autobackup():
    global backup_timer

    if backup_timer:
        backup_timer.cancel()
        backup_timer = None
        utils.logger.info("Timer de autobackup cancelado")

def toggle_autobackup():
    utils.limpiar_pantalla()

    print("\n" + "="*60)
    print("CONFIGURAR AUTOBACKUP")
    print("="*60 + "\n")

    if is_enabled():
        print("Estado actual: ACTIVADO ✔")
        print(f"El autobackup creará backups cada {config.CONFIG['backup_interval_minutes']} minutos\n")
    else:
        print("Estado actual: DESACTIVADO ✖\n")

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

    utils.pausar()

def init_on_load():
    global backup_timer
    if is_enabled() and backup_timer is None:
        start_autobackup()
        utils.logger.info(f"Autobackup activado - cada {config.CONFIG['backup_interval_minutes']} minutos")
