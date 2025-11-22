import threading
import os
import subprocess
from datetime import datetime

config = CloudModuleLoader.load_module("config")
utils = CloudModuleLoader.load_module("utils")

# Variable global para el timer
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
    import backup  # Importar aquí para evitar importación circular

    utils.logger.info("========== INICIO BACKUP AUTOMÁTICO ==========")
    utils.logger.info(f"Directorio de trabajo: {os.getcwd()}")

    try:
        if not is_enabled():
            utils.logger.info("Autobackup deshabilitado, cancelando ejecución")
            return

        print("\n" + "=" * 60)
        print("⏰ AUTO-BACKUP EJECUTÁNDOSE...")
        print("=" * 60)
        utils.logger.info("Mensaje de inicio mostrado en terminal")

        # Llama la función principal de backup manual desde backup.py
        backup.ejecutar_backup_manual()

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

    print("\n" + "=" * 60)
    print("CONFIGURAR AUTOBACKUP")
    print("=" * 60 + "\n")

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
        print("\n" + "=" * 60)
        print("CONFIGURAR INTERVALO")
        print("=" * 60 + "\n")

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
        print("\n" + "=" * 60)
        print("EJECUTAR BACKUP MANUAL")
        print("=" * 60 + "\n")

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
