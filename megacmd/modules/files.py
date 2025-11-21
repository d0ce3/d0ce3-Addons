"""
Módulo de gestión de archivos en MEGA
"""

import os
import subprocess
import shutil
from shutil import which

config = CloudModuleLoader.load_module("config")
utils = CloudModuleLoader.load_module("utils")
megacmd = CloudModuleLoader.load_module("megacmd")
backup = CloudModuleLoader.load_module("backup")

# Variable global para pausar autobackup durante restauración
restauracion_en_proceso = False

# ============================================
# INSTALACIÓN DE UNRAR
# ============================================

def is_unrar_installed():
    return which("unrar") is not None

def install_unrar():
    """Instala unrar"""
    if is_unrar_installed():
        return True

    utils.logger.info("Instalando unrar...")
    utils.print_msg("Instalando unrar...", "🡻")

    ok, stdout, stderr = utils.run_command(
        ["sudo", "apt-get", "install", "-y", "-qq", "unrar"]
    )

    if ok and is_unrar_installed():
        utils.logger.info("unrar instalado correctamente")
        utils.print_msg("unrar instalado correctamente", "✔")
        return True
    else:
        utils.logger.error(f"Error al instalar unrar: {stderr}")
        utils.print_msg("Error al instalar unrar", "✖")
        return False

# ============================================
# EXTRACCIÓN SEGURA
# ============================================

def extract_safe(zip_path):
    """Extrae backup validando contenido"""
    temp_dir = "temp_extract"

    try:
        # Crear directorio temporal
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)

        utils.logger.info(f"Extrayendo {zip_path} en directorio temporal")

        # Extraer
        result = subprocess.run(
            ["unzip", "-o", zip_path, "-d", temp_dir],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            utils.logger.error(f"Error al extraer: {result.stderr}")
            return False, "Error al extraer archivo"

        # Validar contenido
        expected = config.CONFIG["server_folder"]
        extracted_path = os.path.join(temp_dir, expected)

        if not os.path.exists(extracted_path):
            utils.logger.error(f"El backup no contiene '{expected}'")
            shutil.rmtree(temp_dir)
            return False, f"El backup no contiene '{expected}'"

        # Preguntar si reemplazar
        if os.path.exists(expected):
            replace = utils.get_input(f"¿Reemplazar carpeta {expected} actual? (s/n)").lower()

            if replace != 's':
                shutil.rmtree(temp_dir)
                utils.logger.info("Usuario canceló reemplazo")
                return False, "Usuario canceló reemplazo"

            utils.print_msg("Eliminando carpeta actual...", "🗑")
            shutil.rmtree(expected)
            utils.logger.info(f"Carpeta {expected} eliminada para reemplazo")

        # Mover a ubicación final
        shutil.move(extracted_path, ".")
        utils.logger.info(f"Carpeta {expected} movida a ubicación final")

        # Limpiar temp
        shutil.rmtree(temp_dir)

        return True, "Extracción exitosa"

    except Exception as e:
        utils.logger.exception(f"Error en extracción segura: {e}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return False, str(e)

# ============================================
# LISTAR Y DESCARGAR
# ============================================

def listar_y_descargar():
    """Lista y descarga archivos"""
    global restauracion_en_proceso

    utils.clear_screen()

    if not megacmd.ensure_ready():
        utils.print_msg("No se pudo preparar MegaCmd", "✖")
        import time
        time.sleep(3)
        return

    utils.clear_screen()
    utils.print_msg("=== Listar y Descargar Archivos ===", "◰")
    print()

    ok, stdout, stderr = utils.run_command(["mega-ls", "/"])

    if not ok:
        utils.print_msg("Error al listar carpetas", "✖")
        import time
        time.sleep(3)
        return

    folders = [f for f in stdout.strip().split('\n') if f]

    if not folders:
        utils.print_msg("No hay carpetas en la raíz", "⚠")
        import time
        time.sleep(3)
        return

    utils.print_msg("Carpetas disponibles:", "📁")
    for i, folder in enumerate(folders, 1):
        print(f" {i}. /{folder}")
    print(f" 0. Raíz /")
    print()

    choice = utils.get_input("Seleccioná un número o escribí una ruta")

    if not choice:
        utils.print_msg("No se seleccionó ninguna carpeta", "⚠")
        import time
        time.sleep(2)
        return

    if choice.isdigit():
        num = int(choice)
        if num == 0:
            path = "/"
        elif 1 <= num <= len(folders):
            path = f"/{folders[num - 1]}"
        else:
            utils.print_msg("Opción inválida", "✖")
            import time
            time.sleep(3)
            return
    else:
        path = choice

    print()
    utils.print_msg(f"Contenido de {path}", "📂")
    print()

    ok, stdout, stderr = utils.run_command(["mega-ls", path])

    if not ok:
        utils.print_msg(f"Error: {stderr}", "✖")
        import time
        time.sleep(3)
        return

    files = [f for f in stdout.strip().split('\n') if f]

    if not files:
        utils.print_msg("La carpeta está vacía", "⚠")
        import time
        time.sleep(3)
        return

    utils.print_msg("Archivos encontrados:", "📄")
    for i, file in enumerate(files, 1):
        print(f" {i}. {file}")
    print()

    download_choice = utils.get_input("¿Descargar un archivo? (número/n para volver)").lower()

    if download_choice == 'n' or download_choice == '':
        return

    if download_choice.isdigit():
        file_num = int(download_choice)

        if 1 <= file_num <= len(files):
            selected_file = files[file_num - 1]
            remote_path = f"{path}/{selected_file}" if path != "/" else f"/{selected_file}"
            local_path = "."

            print()
            utils.print_msg(f"Descargando {selected_file}...", "🡻")
            utils.logger.info(f"Descargando {selected_file} desde {remote_path} a {local_path}")

            ok, stdout, stderr = utils.run_command(["mega-get", remote_path, local_path])

            if ok:
                utils.print_msg("Descarga completada", "✔")
                utils.logger.info(f"Archivo descargado: {selected_file}")

                if selected_file.endswith('.zip') or selected_file.endswith('.rar'):
                    extract_choice = utils.get_input("¿Extraer el archivo? (s/n)").lower()

                    if extract_choice == 's':
                        restauracion_en_proceso = True
                        utils.logger.info("Restauración iniciada - autobackup pausado temporalmente")

                        file_path = selected_file
                        print()

                        try:
                            if selected_file.endswith('.zip'):
                                success, message = extract_safe(file_path)

                                if success:
                                    utils.print_msg(message, "✔")
                                    if os.path.exists(file_path):
                                        os.remove(file_path)
                                        utils.print_msg("Archivo comprimido eliminado", "✔")
                                        utils.logger.info(f"Archivo zip eliminado: {file_path}")
                                else:
                                    utils.print_msg(f"Error: {message}", "✖")
                                    if os.path.exists(file_path):
                                        os.remove(file_path)
                                        utils.print_msg("Archivo comprimido eliminado", "✔")

                            elif selected_file.endswith('.rar'):
                                if not is_unrar_installed():
                                    utils.print_msg("unrar no está instalado. Instalando...", "⚠")
                                    if not install_unrar():
                                        utils.print_msg("No se pudo instalar unrar", "✖")
                                        import time
                                        time.sleep(3)
                                        return

                                utils.print_msg(f"Extrayendo {selected_file}...", "⎙")
                                ok, stdout, stderr = utils.run_command(["unrar", "x", "-o+", file_path, "."])

                                if ok:
                                    utils.print_msg("Archivo extraído correctamente", "✔")
                                    utils.logger.info(f"Archivo extraído: {selected_file}")

                                    if os.path.exists(file_path):
                                        os.remove(file_path)
                                        utils.print_msg("Archivo comprimido eliminado", "✔")
                                        utils.logger.info(f"Archivo rar eliminado: {file_path}")
                                else:
                                    utils.print_msg("Error al extraer", "✖")
                                    utils.logger.error(f"Error al extraer {selected_file}: {stderr}")

                        finally:
                            restauracion_en_proceso = False
                            utils.logger.info("Restauración finalizada - autobackup reanudado")
                else:
                    utils.print_msg(f"Archivo descargado en: ./{selected_file}", "ℹ")
            else:
                utils.print_msg(f"Error: {stderr}", "✖")
                utils.logger.error(f"Error al descargar {selected_file}: {stderr}")
        else:
            utils.print_msg("Número inválido", "✖")
    else:
        utils.print_msg("Opción inválida", "✖")

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    input("⏎ ⎹ Apretá enter para volver al menú de MSX")
    utils.clear_screen()
    utils.print_msg("Saliendo al menú de MSX...", "❰❮")
    import time
    time.sleep(2)

# ============================================
# GESTIONAR BACKUPS
# ============================================

def gestionar_backups():
    """Gestionar y limpiar backups"""
    utils.clear_screen()

    if not megacmd.ensure_ready():
        utils.print_msg("No se pudo preparar MegaCmd", "✖")
        import time
        time.sleep(3)
        return

    utils.clear_screen()
    utils.print_msg("=== Gestionar Backups ===", "◰")
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    ok, stdout, stderr = utils.run_command(["mega-ls", "/"])

    if not ok:
        utils.print_msg("Error al listar carpetas", "✖")
        import time
        time.sleep(3)
        return

    folders = [f for f in stdout.strip().split('\n') if f]

    if folders:
        utils.print_msg("Carpetas disponibles:", "📁")
        for i, folder in enumerate(folders, 1):
            print(f" {i}. /{folder}")
        print(f" 0. Raíz /")
        print()

        choice = utils.get_input(f"Seleccioná carpeta para limpiar (default: {config.CONFIG['backup_folder']})")

        if not choice:
            carpeta = config.CONFIG["backup_folder"]
        elif choice.isdigit():
            num = int(choice)
            if num == 0:
                carpeta = "/"
            elif 1 <= num <= len(folders):
                carpeta = f"/{folders[num - 1]}"
            else:
                carpeta = config.CONFIG["backup_folder"]
        else:
            carpeta = choice
    else:
        carpeta = config.CONFIG["backup_folder"]

    print()

    backups = backup.list_backups_in_mega(carpeta)

    if not backups:
        utils.print_msg(f"No hay backups {config.CONFIG['backup_prefix']} en {carpeta}", "⚠")
        print()
    else:
        backups_ordenados = backup.sort_backups_by_date(backups)
        utils.print_msg(f"Backups encontrados en {carpeta}: {len(backups)}", "📦")
        print()

        mostrar = min(10, len(backups_ordenados))
        for i, bkp in enumerate(backups_ordenados[:mostrar], 1):
            print(f" {i}. {bkp}")

        if len(backups_ordenados) > 10:
            print(f" ... y {len(backups_ordenados) - 10} más")

        print()

        max_input = utils.get_input(f"¿Cuántos backups mantener? (default: {config.CONFIG['max_backups']})")

        try:
            max_backups = int(max_input) if max_input else config.CONFIG["max_backups"]
            if max_backups < 1:
                max_backups = config.CONFIG["max_backups"]
        except:
            max_backups = config.CONFIG["max_backups"]

        print()
        backup.cleanup_old_backups(max_backups, carpeta)

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    input("⏎ ⎹ Apretá enter para volver al menú de MSX")
    utils.clear_screen()
    utils.print_msg("Saliendo al menú de MSX...", "❰❮")
    import time
    time.sleep(2)

# ============================================
# SUBIR ARCHIVO
# ============================================

def subir_archivo():
    """Subir archivo a MEGA"""
    utils.clear_screen()

    if not megacmd.ensure_ready():
        utils.print_msg("No se pudo preparar MegaCmd", "✖")
        import time
        time.sleep(3)
        return

    utils.clear_screen()
    utils.print_msg("=== Subir Archivo a MEGA ===", "◰")
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    local_path = utils.get_input("Archivo local (ruta completa)")

    if not local_path or not os.path.exists(local_path):
        utils.print_msg("Archivo no encontrado", "✖")
        import time
        time.sleep(3)
        return

    remote_path = backup.list_folders()

    print()
    utils.print_msg(f"Subiendo {os.path.basename(local_path)}...", "🡻")

    ok, stdout, stderr = utils.run_command(["mega-put", local_path, remote_path])

    if ok:
        utils.print_msg("Archivo subido correctamente", "✔")
    else:
        utils.print_msg(f"Error: {stderr}", "✖")

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    input("⏎ ⎹ Apretá enter para volver al menú de MSX")
    utils.clear_screen()
    utils.print_msg("Saliendo al menú de MSX...", "❰❮")
    import time
    time.sleep(2)

# ============================================
# INFO CUENTA
# ============================================

def info_cuenta():
    """Mostrar información de cuenta"""
    utils.clear_screen()

    if not megacmd.ensure_ready():
        utils.print_msg("No se pudo preparar MegaCmd", "✖")
        import time
        time.sleep(3)
        return

    utils.clear_screen()
    utils.print_msg("=== Información de Cuenta MEGA ===", "◰")
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    ok, stdout, stderr = utils.run_command(["mega-whoami"])
    print(f"Usuario: {stdout.strip()}")
    print()

    ok, stdout, stderr = utils.run_command(["mega-df"])
    if ok:
        print(stdout)

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    input("⏎ ⎹ Apretá enter para volver al menú de MSX")
    utils.clear_screen()
    utils.print_msg("Saliendo al menú de MSX...", "❰❮")
    import time
    time.sleep(2)
