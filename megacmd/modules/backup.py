"""
Módulo de gestión de backups
"""

import os
import subprocess
import shutil
from shutil import which

from megacmd_tool import CloudModuleLoader
config = CloudModuleLoader.load_module("config")
utils = CloudModuleLoader.load_module("utils")
megacmd = CloudModuleLoader.load_module("megacmd")

# ============================================
# INSTALACIÓN DE HERRAMIENTAS
# ============================================

def is_zip_installed():
    return which("zip") is not None

def install_zip():
    """Instala zip"""
    if is_zip_installed():
        return True

    utils.logger.info("Instalando zip...")
    utils.print_msg("Instalando zip...", "🡻")

    ok, stdout, stderr = utils.run_command(
        ["sudo", "apt-get", "install", "-y", "-qq", "zip"]
    )

    if ok and is_zip_installed():
        utils.logger.info("zip instalado correctamente")
        utils.print_msg("zip instalado correctamente", "✔")
        return True
    else:
        utils.logger.error(f"Error al instalar zip: {stderr}")
        utils.print_msg("Error al instalar zip", "✖")
        return False

# ============================================
# GESTIÓN DE BACKUPS
# ============================================

def list_backups_in_mega(carpeta):
    """Lista backups en MEGA"""
    ok, stdout, stderr = utils.run_command(["mega-ls", carpeta])

    if not ok:
        return []

    archivos = stdout.strip().split('\n')
    prefix = config.CONFIG["backup_prefix"]
    backups = [f for f in archivos if f.startswith(f'{prefix}_') and f.endswith('.zip')]

    return backups

def sort_backups_by_date(backups):
    """Ordena backups por fecha"""
    from datetime import datetime

    def extraer_fecha(nombre):
        try:
            prefix = config.CONFIG["backup_prefix"]
            fecha_hora = nombre.replace(f'{prefix}_', '').replace('.zip', '')
            fecha, hora = fecha_hora.split('_')
            dia, mes, anio = fecha.split('-')
            hora_min = hora.replace('-', ':')
            return datetime.strptime(f"{anio}-{mes}-{dia} {hora_min}", "%Y-%m-%d %H:%M")
        except:
            return datetime.min

    return sorted(backups, key=extraer_fecha, reverse=True)

def cleanup_old_backups(max_backups=None, carpeta=None, silencioso=False):
    """Elimina backups antiguos"""
    if max_backups is None:
        max_backups = config.CONFIG["max_backups"]
    if carpeta is None:
        carpeta = config.CONFIG["backup_folder"]

    if not megacmd.is_logged_in():
        return False

    if not silencioso:
        utils.print_msg(f"Verificando backups en {carpeta}...", "🗑")

    utils.logger.info(f"Verificando backups en {carpeta}, manteniendo {max_backups}")

    backups = list_backups_in_mega(carpeta)

    if len(backups) <= max_backups:
        if not silencioso:
            utils.print_msg(f"Total de backups: {len(backups)}/{max_backups} - No hay que eliminar nada", "✔")
        utils.logger.info(f"Total de backups: {len(backups)}/{max_backups} - No se eliminó nada")
        return True

    backups_ordenados = sort_backups_by_date(backups)
    backups_a_eliminar = backups_ordenados[max_backups:]

    if not silencioso:
        utils.print_msg(f"Se eliminarán {len(backups_a_eliminar)} backup(s) antiguo(s):", "⚠")
        for backup in backups_a_eliminar:
            print(f" - {backup}")
        print()

    utils.logger.info(f"Eliminando {len(backups_a_eliminar)} backups antiguos: {backups_a_eliminar}")

    for backup in backups_a_eliminar:
        ruta_completa = f"{carpeta}/{backup}"
        ok, stdout, stderr = utils.run_command(["mega-rm", ruta_completa])

        if ok:
            utils.logger.info(f"Eliminado: {backup}")
            if not silencioso:
                utils.print_msg(f"Eliminado: {backup}", "✔")
        else:
            utils.logger.error(f"Error al eliminar {backup}: {stderr}")
            if not silencioso:
                utils.print_msg(f"Error al eliminar {backup}", "✖")

    if not silencioso:
        print()
        utils.print_msg(f"Mantenidos: {max_backups} backups más recientes", "✔")

    utils.logger.info(f"Limpieza completada - Mantenidos {max_backups} backups")
    return True

# ============================================
# LISTAR CARPETAS
# ============================================

def list_folders():
    """Lista carpetas y permite seleccionar"""
    ok, stdout, stderr = utils.run_command(["mega-ls", "/"])

    if not ok:
        return config.CONFIG["backup_folder"]

    folders = [f for f in stdout.strip().split('\n') if f]

    if not folders:
        return config.CONFIG["backup_folder"]

    print()
    utils.print_msg("Carpetas disponibles en MEGA:", "📁")
    for i, folder in enumerate(folders, 1):
        print(f" {i}. /{folder}")
    print(f" 0. Raíz /")
    print()

    choice = utils.get_input(f"Seleccioná un número o escribí una ruta (default: {config.CONFIG['backup_folder']})")

    if not choice:
        return config.CONFIG["backup_folder"]
    elif choice.isdigit():
        num = int(choice)
        if num == 0:
            return "/"
        elif 1 <= num <= len(folders):
            return f"/{folders[num - 1]}"
        else:
            return config.CONFIG["backup_folder"]
    else:
        return choice

# ============================================
# CREAR BACKUP
# ============================================

def crear_backup():
    """Crea backup manual"""
    utils.clear_screen()
    utils.logger.info("=== Iniciando creación de backup manual ===")

    if not megacmd.ensure_ready():
        utils.print_msg("No se pudo preparar MegaCmd", "✖")
        import time
        time.sleep(3)
        return

    utils.clear_screen()
    utils.print_msg("=== Crear Backup ===", "◰")
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    server_folder = config.CONFIG["server_folder"]
    server_path = config.safe_path(server_folder)

    if not os.path.exists(server_path):
        utils.logger.error(f"No existe la carpeta {server_folder}")
        utils.print_msg(f"Error: No existe la carpeta {server_folder}", "✖")
        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()
        input("⏎ ⎹ Apretá enter para volver al menú de MSX")
        utils.clear_screen()
        utils.print_msg("Saliendo al menú de MSX...", "❰❮")
        import time
        time.sleep(2)
        return

    if not install_zip():
        utils.logger.error("No se pudo instalar zip")
        utils.print_msg("No se pudo instalar zip", "✖")
        import time
        time.sleep(3)
        return

    utils.print_msg(f"Se respaldará: {server_folder}", "➜")
    print()

    folder = list_folders()
    fecha = utils.get_argentina_time().strftime("%d-%m-%Y_%H-%M")
    backup_name = f"{config.CONFIG['backup_prefix']}_{fecha}.zip"

    utils.logger.info(f"Creando backup: {backup_name} en carpeta {folder}")
    print()

    # Comprimir con spinner
    cmd = ["zip", "-r", "-q", backup_name, server_folder]
    utils.logger.info(f"Ejecutando comando: {' '.join(cmd)}")

    proceso = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    spinner = utils.Spinner("Comprimiendo")

    if spinner.start(proceso):
        if os.path.exists(backup_name):
            tamano_mb = os.path.getsize(backup_name) / (1024 * 1024)
            utils.logger.info(f"Archivo creado: {backup_name} ({tamano_mb:.2f} MB)")
            utils.print_msg(f"Archivo creado: {tamano_mb:.2f} MB", "✔")
        else:
            utils.logger.warning("Archivo creado pero no se encontró en disco")
            utils.print_msg("Archivo creado", "✔")

        print()

        # Subir con spinner
        utils.logger.info(f"Subiendo {backup_name} a {folder}")
        proceso = subprocess.Popen(
            ["mega-put", "-c", backup_name, folder],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        spinner = utils.Spinner("Subiendo")

        if spinner.start(proceso):
            utils.logger.info(f"Backup subido correctamente: {backup_name}")
            utils.print_msg("Backup subido correctamente", "✔")

            os.remove(backup_name)
            utils.logger.info(f"Archivo local eliminado: {backup_name}")
            utils.print_msg("Archivo local eliminado", "✔")
            print()

            cleanup_old_backups(carpeta=folder)
        else:
            utils.logger.error(f"Error al subir backup: {backup_name}")
            utils.print_msg("Error al subir", "✖")
            if os.path.exists(backup_name):
                os.remove(backup_name)
                utils.logger.info(f"Archivo local eliminado tras error: {backup_name}")
    else:
        utils.logger.error(f"Error al comprimir backup: {backup_name}")
        utils.print_msg("Error al comprimir", "✖")

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    input("⏎ ⎹ Apretá enter para volver al menú de MSX")
    utils.clear_screen()
    utils.print_msg("Saliendo al menú de MSX...", "❰❮")
    import time
    time.sleep(2)
