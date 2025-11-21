"""
Módulo de backups automáticos
"""

import os
import subprocess
import threading

config = CloudModuleLoader.load_module("config")
utils = CloudModuleLoader.load_module("utils")
backup = CloudModuleLoader.load_module("backup")

# Variables globales
BACKUP_CONTROL_FILE = os.path.expanduser("~/.megacmd_autobackup")
backup_timer = None
backup_en_proceso = False

# ============================================
# FUNCIONES DE CONTROL
# ============================================

def is_enabled():
    """Verifica si está activado"""
    return os.path.exists(BACKUP_CONTROL_FILE)

def is_restoration_in_process():
    """Verifica si hay restauración en proceso"""
    # Importar files para chequear estado
    files = CloudModuleLoader.load_module("files")
    return files.restauracion_en_proceso if hasattr(files, 'restauracion_en_proceso') else False

# ============================================
# EJECUCIÓN DE BACKUP
# ============================================

def ejecutar_backup_automatico():
    """Ejecuta backup automático"""
    global backup_timer, backup_en_proceso

    if backup_en_proceso:
        utils.logger.warning("Intento de backup automático mientras otro está en proceso - saltando")
        return

    if is_restoration_in_process():
        utils.logger.warning("Intento de backup automático durante restauración - saltando")
        return

    if is_enabled():
        backup_en_proceso = True
        timestamp = utils.get_argentina_time().strftime("%H:%M:%S")
        utils.logger.info("========== INICIO BACKUP AUTOMÁTICO ==========")

        try:
            os.chdir(config.BASE_DIR)
            utils.logger.info(f"Directorio de trabajo: {os.getcwd()}")

            print(f"\n[{timestamp}] ⏰ Backup automático iniciado...")
            utils.logger.info("Mensaje de inicio mostrado en terminal")

            server_folder = config.CONFIG["server_folder"]
            servidor_path = config.safe_path(server_folder)

            if not os.path.exists(servidor_path):
                utils.logger.error(f"No existe la carpeta {server_folder} - ruta buscada: {servidor_path}")
                print(f"[{timestamp}] ❌ Error: carpeta {server_folder} no encontrada")
                return

            utils.logger.info(f"Carpeta {server_folder} verificada - existe en {servidor_path}")

            if not backup.install_zip():
                utils.logger.error("No se pudo instalar/verificar zip - abortando backup")
                print(f"[{timestamp}] ❌ Error: zip no disponible")
                return

            utils.logger.info("zip verificado - disponible")

            folder = config.CONFIG["backup_folder"]
            fecha = utils.get_argentina_time().strftime("%d-%m-%Y_%H-%M")
            backup_name = f"{config.CONFIG['backup_prefix']}_{fecha}.zip"

            utils.logger.info(f"Nombre de backup: {backup_name}")
            utils.logger.info(f"Destino MEGA: {folder}")

            if os.path.exists(backup_name):
                utils.logger.warning(f"El archivo {backup_name} ya existe - saltando backup")
                print(f"[{timestamp}] ⚠️ Archivo ya existe, saltando")
                return

            # Comprimir
            utils.logger.info(f"Iniciando compresión: zip -r -q {backup_name} {server_folder}")
            cmd = ["zip", "-r", "-q", backup_name, server_folder]
            proceso = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            utils.logger.info(f"Proceso de compresión iniciado - PID: {proceso.pid}")

            spinner = utils.Spinner("Comprimiendo")

            if spinner.start(proceso):
                utils.logger.info("Compresión completada exitosamente")

                if os.path.exists(backup_name):
                    tamano_bytes = os.path.getsize(backup_name)
                    tamano_mb = tamano_bytes / (1024 * 1024)
                    utils.logger.info(f"Archivo comprimido creado: {tamano_mb:.2f} MB ({tamano_bytes} bytes)")
                else:
                    utils.logger.error("El proceso de compresión terminó pero no se creó el archivo")
                    print(f"[{timestamp}] ❌ Error: archivo no creado tras compresión")
                    return

                # Subir
                utils.logger.info(f"Iniciando subida a MEGA: {backup_name} -> {folder}")
                proceso = subprocess.Popen(
                    ["mega-put", "-c", backup_name, folder],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                utils.logger.info(f"Proceso de subida iniciado - PID: {proceso.pid}")

                spinner = utils.Spinner("Subiendo")

                if spinner.start(proceso):
                    utils.logger.info(f"Backup subido exitosamente: {backup_name}")
                    print(f"[{timestamp}] ✅ Backup completado: {backup_name}")

                    if os.path.exists(backup_name):
                        os.remove(backup_name)
                        utils.logger.info(f"Archivo local eliminado: {backup_name}")

                    try:
                        utils.logger.info("Iniciando limpieza de backups viejos")
                        backup.cleanup_old_backups(carpeta=folder, silencioso=True)
                    except Exception as e:
                        utils.logger.error(f"Error en limpieza de backups viejos: {e}")
                else:
                    utils.logger.error(f"Error al subir backup - returncode: {proceso.returncode}")
                    print(f"[{timestamp}] ❌ Error al subir")

                    if os.path.exists(backup_name):
                        os.remove(backup_name)
                        utils.logger.info(f"Archivo local eliminado tras error: {backup_name}")
            else:
                utils.logger.error(f"Error al comprimir - returncode: {proceso.returncode}")
                print(f"[{timestamp}] ❌ Error al comprimir")

        except Exception as e:
            utils.logger.exception(f"Excepción no controlada en backup automático: {e}")
            print(f"[{timestamp}] ❌ Error inesperado: {e}")

        finally:
            backup_en_proceso = False
            utils.logger.info("========== FIN BACKUP AUTOMÁTICO ==========")

    # Programar siguiente ejecución
    programar_siguiente_backup()

def programar_siguiente_backup():
    """Programa siguiente ejecución"""
    global backup_timer

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
    else:
        if backup_timer:
            try:
                backup_timer.cancel()
                utils.logger.info("Autobackup desactivado - timer cancelado")
            except:
                pass
        backup_timer = None

# ============================================
# INICIAR/DETENER
# ============================================

def start_autobackup():
    """Inicia el sistema de autobackup"""
    global backup_timer

    if backup_timer:
        try:
            backup_timer.cancel()
            utils.logger.info("Timer existente cancelado antes de iniciar nuevo")
        except:
            pass

    if is_enabled():
        interval_seconds = config.CONFIG["backup_interval_minutes"] * 60
        backup_timer = threading.Timer(interval_seconds, ejecutar_backup_automatico)
        backup_timer.daemon = True
        backup_timer.start()
        utils.logger.info(f"Sistema de autobackup iniciado - primer backup en {config.CONFIG['backup_interval_minutes']} minutos")
        utils.print_msg("Sistema de autobackup iniciado", "✔")

def enable_autobackup():
    """Activa autobackup"""
    with open(BACKUP_CONTROL_FILE, "w") as f:
        f.write("enabled")

    interval = config.CONFIG["backup_interval_minutes"]
    utils.logger.info(f"Autobackup activado - cada {interval} minutos")
    utils.print_msg(f"Autobackup activado - cada {interval} minutos", "✔")

def disable_autobackup():
    """Desactiva autobackup"""
    global backup_timer

    if os.path.exists(BACKUP_CONTROL_FILE):
        os.remove(BACKUP_CONTROL_FILE)

    if backup_timer:
        try:
            backup_timer.cancel()
        except:
            pass

    backup_timer = None
    utils.logger.info("Autobackup desactivado")
    utils.print_msg("Autobackup desactivado", "✔")

# ============================================
# TOGGLE (llamado desde addon)
# ============================================

def toggle_autobackup():
    """Activa/desactiva desde menú"""
    global backup_timer, backup_en_proceso

    utils.clear_screen()

    megacmd = CloudModuleLoader.load_module("megacmd")
    if not megacmd.ensure_ready():
        utils.print_msg("No se pudo preparar MegaCmd", "✖")
        import time
        time.sleep(3)
        return

    utils.clear_screen()
    utils.print_msg("=== Configurar Autobackup ===", "◰")
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    status = "ACTIVADO ✔" if is_enabled() else "DESACTIVADO ✖"
    utils.print_msg(f"Estado actual: {status}", "⚙")
    print()

    interval = config.CONFIG["backup_interval_minutes"]
    utils.print_msg(f"El autobackup creará backups cada {interval} minutos", "ℹ")
    utils.print_msg(f"en {config.CONFIG['backup_folder']} de tu cuenta MEGA", "ℹ")
    utils.print_msg(f"Se mantendrán solo los últimos {config.CONFIG['max_backups']} backups", "ℹ")
    print()

    if is_enabled():
        choice = utils.get_input("¿Desactivar autobackup? (s/n)").lower()

        if choice == 's':
            disable_autobackup()
    else:
        choice = utils.get_input("¿Activar autobackup? (s/n)").lower()

        if choice == 's':
            if backup_timer:
                try:
                    backup_timer.cancel()
                except:
                    pass

            backup_timer = None
            backup_en_proceso = False

            enable_autobackup()
            start_autobackup()

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    input("⏎ ⎹ Apretá enter para volver al menú de MSX")
    utils.clear_screen()
    utils.print_msg("Saliendo al menú de MSX...", "❰❮")
    import time
    time.sleep(2)

# ============================================
# INIT AL CARGAR
# ============================================

def init_on_load():
    """Inicializa al cargar el módulo"""
    if is_enabled():
        start_autobackup()
