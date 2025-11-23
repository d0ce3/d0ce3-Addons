import subprocess
from shutil import which

utils = CloudModuleLoader.load_module("utils")

def is_installed():
    return which("mega-login") is not None

def is_logged_in():
    try:
        result = subprocess.run(["mega-whoami"], capture_output=True, text=True, timeout=5)
        return result.returncode == 0 and "Not logged in" not in result.stdout
    except:
        return False

def mostrar_informacion_mega():
    MORADO = "\033[95m"
    VERDE = "\033[92m"
    AMARILLO = "\033[93m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    def m(texto):
        return f"{MORADO}{texto}{RESET}"
    
    def v(texto):
        return f"{VERDE}{texto}{RESET}"
    
    def a(texto):
        return f"{AMARILLO}{texto}{RESET}"
    
    while True:
        utils.limpiar_pantalla()
        
        print()
        print(m("─" * 60))
        print(f"{BOLD}{MORADO}INFORMACIÓN IMPORTANTE{RESET}")
        print(m("─" * 60))
        print()
        
        print(a("⚠️  REQUISITO PREVIO: CUENTA EN MEGA"))
        print()
        print("Para utilizar este método de backup es necesario tener")
        print("una cuenta en MEGA (servicio de almacenamiento en nube).")
        print()
        print(m("📌 Si NO tienes una cuenta en MEGA:"))
        print("   → Ingresa al siguiente link para crear una:")
        print(v("   → https://mega.nz/register"))
        print()
        print(m("📌 Si YA tienes una cuenta en MEGA:"))
        print("   → Puedes proceder con la configuración")
        print()
        print(m("💡 IMPORTANTE:"))
        print("   • La cuenta gratuita ofrece 20GB de almacenamiento")
        print("   • Necesitarás tu correo y contraseña para configurar")
        print("   • Los backups se subirán automáticamente a tu cuenta")
        print()
        print(m("─" * 60))
        
        input(m("\nPresiona Enter para continuar..."))
        
        print()
        respuesta = input(m("¿Estás seguro que comprendiste el texto anterior? (Si/No): ")).strip().lower()
        
        if respuesta in ['si', 's', 'yes', 'y']:
            print(v("\n✓ Continuando con la configuración..."))
            import time
            time.sleep(1)
            return True
        elif respuesta in ['no', 'n']:
            print(a("\n⚠️ Por favor, lee nuevamente la información..."))
            import time
            time.sleep(2)
            continue
        else:
            print(a("\n⚠️ Respuesta no válida. Por favor responde Si o No."))
            import time
            time.sleep(2)
            continue

def install():
    if is_installed():
        utils.print_msg("MegaCmd ya está instalado", "✓")
        return True
    
    utils.limpiar_pantalla()
    utils.print_msg("Instalación de MegaCmd", "🔧")
    print()
    
    utils.print_msg("Actualizando repositorios...", "📦")
    subprocess.run("sudo apt-get update -qq", shell=True, capture_output=True)
    
    utils.print_msg("Descargando MegaCmd...", "📥")
    subprocess.run(
        'curl -s https://mega.nz/linux/repo/xUbuntu_20.04/amd64/megacmd-xUbuntu_20.04_amd64.deb -o /tmp/megacmd.deb',
        shell=True,
        capture_output=True
    )
    
    subprocess.run("sudo dpkg -i /tmp/megacmd.deb 2>/dev/null", shell=True, capture_output=True)
    
    utils.print_msg("Instalando dependencias...", "⚙️")
    subprocess.run("sudo apt-get install -f -y -qq", shell=True, capture_output=True)
    
    subprocess.run("rm -f /tmp/megacmd.deb", shell=True, capture_output=True)
    
    if is_installed():
        utils.print_msg("MegaCmd instalado correctamente", "✓")
        return True
    else:
        utils.print_msg("Error en la instalación", "✖")
        return False

def carpeta_existe(ruta_carpeta):
    try:
        cmd_ls = ["mega-ls", "-l", ruta_carpeta]
        result = subprocess.run(cmd_ls, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            return output.startswith('d')
        return False
                
    except:
        return False

def login():
    if is_logged_in():
        try:
            result = subprocess.run(["mega-whoami"], capture_output=True, text=True)
            email = result.stdout.strip()
            utils.print_msg(f"Ya hay sesión activa: {email}", "✓")
        except:
            utils.print_msg("Ya hay sesión activa", "✓")
        return True
    
    utils.limpiar_pantalla()
    utils.print_msg("Login en MEGA", "🔐")
    print()
    
    import os
    email = os.getenv("MEGA_EMAIL")
    password = os.getenv("MEGA_PASSWORD")
    
    if not email or not password:
        mostrar_informacion_mega()
        
        email = input("Correo electrónico: ").strip()
        password = input("Contraseña: ").strip()
    
    try:
        result = subprocess.run(["mega-login", email, password], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            utils.print_msg("Sesión iniciada correctamente", "✓")
            utils.logger.info("Login exitoso en MEGA")
            
            print("📁 La carpeta de backups se creará automáticamente al subir el primer backup")
            
            import time
            time.sleep(1)
            utils.limpiar_pantalla()
            return True
        else:
            utils.print_msg(f"Error al iniciar sesión: {result.stderr}", "✖")
            utils.pausar()
            return False
    except subprocess.TimeoutExpired:
        utils.print_msg("Tiempo de espera agotado", "✖")
        utils.pausar()
        return False
    except Exception as e:
        utils.print_msg(f"Error: {e}", "✖")
        utils.pausar()
        return False

def ensure_ready():
    if not install():
        return False
    if not login():
        return False
    return True