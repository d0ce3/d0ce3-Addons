"""
Gestión de MegaCmd
"""

import subprocess
from shutil import which

from megacmd_tool import CloudModuleLoader
utils = CloudModuleLoader.load_module("utils")

def is_installed():
    """Verifica si está instalado"""
    return which("mega-login") is not None

def is_logged_in():
    """Verifica sesión"""
    ok, stdout, stderr = utils.run_command(["mega-whoami"], silent=True)
    return ok and "Not logged in" not in stdout

def install():
    """Instala MegaCmd"""
    if is_installed():
        utils.print_msg("MegaCmd ya está instalado", "✔")
        return True

    utils.clear_screen()
    utils.print_msg("=== Instalación de MegaCmd ===", "◰")
    print()

    utils.print_msg("Actualizando repositorios...", "🡻")
    subprocess.run("sudo apt-get update -qq", shell=True, capture_output=True)

    utils.print_msg("Descargando MegaCmd...", "🡻")
    subprocess.run(
        "curl -s https://mega.nz/linux/repo/xUbuntu_20.04/amd64/megacmd-xUbuntu_20.04_amd64.deb -o /tmp/megacmd.deb",
        shell=True, capture_output=True
    )

    subprocess.run("sudo dpkg -i /tmp/megacmd.deb 2>/dev/null", shell=True, capture_output=True)

    utils.print_msg("Instalando dependencias...", "🡻")
    subprocess.run("sudo apt-get install -f -y -qq", shell=True, capture_output=True)
    subprocess.run("rm -f /tmp/megacmd.deb", shell=True, capture_output=True)

    if is_installed():
        utils.print_msg("MegaCmd instalado correctamente", "✔")
        return True
    else:
        utils.print_msg("Error en la instalación", "✖")
        return False

def login():
    """Login en MEGA"""
    if is_logged_in():
        ok, stdout, stderr = utils.run_command(["mega-whoami"], silent=True)
        utils.print_msg(f"Ya hay sesión activa: {stdout.strip()}", "✔")
        return True

    utils.clear_screen()
    utils.print_msg("=== Login en MEGA ===", "◰")
    print()

    import os
    email = os.getenv("MEGA_EMAIL")
    password = os.getenv("MEGA_PASSWORD")

    if not email or not password:
        email = utils.get_input("Email")
        password = utils.get_input("Password")

    ok, stdout, stderr = utils.run_command(["mega-login", email, password])

    if ok:
        utils.print_msg("Sesión iniciada correctamente", "✔")
        return True
    else:
        utils.print_msg(f"Error al iniciar sesión: {stderr}", "✖")
        return False

def ensure_ready():
    """Verifica que esté listo"""
    if not install():
        return False
    if not login():
        return False
    return True
