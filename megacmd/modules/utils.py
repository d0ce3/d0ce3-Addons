import os
import sys
import logging
from datetime import datetime

# ============================================
# CONFIGURACIÓN DE LOGGING
# ============================================

logger = logging.getLogger('megacmd')
logger.setLevel(logging.INFO)

# Limpiar handlers existentes para evitar duplicados
if logger.handlers:
    logger.handlers.clear()

# Ruta del log
try:
    log_file = os.path.join(os.getcwd(), 'addons', 'megacmd_backup.log')
    
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
except:
    log_file = 'megacmd_backup.log'

# Handler para archivo
try:
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
except Exception as e:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# ============================================
# FUNCIONES DE UTILIDAD
# ============================================

def print_msg(mensaje, icono="✓"):
    print(f"{icono} ⎹ {mensaje}")
    logger.info(mensaje)

def print_error(mensaje):
    print(f"✖ ⎹ {mensaje}")
    logger.error(mensaje)

def print_warning(mensaje):
    print(f"⚠ ⎹ {mensaje}")
    logger.warning(mensaje)

def formato_bytes(bytes_num):
    for unidad in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f} {unidad}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} PB"

def formato_fecha(timestamp=None):
    if timestamp is None:
        dt = datetime.now()
    else:
        dt = datetime.fromtimestamp(timestamp)
    
    return dt.strftime('%d-%m-%Y_%H-%M')

def limpiar_pantalla():
    os.system('clear' if os.name != 'nt' else 'cls')

def pausar():
    input("\n[+] Enter para continuar...")

def confirmar(mensaje="¿Continuar?"):
    respuesta = input(f"{mensaje} (s/n): ").strip().lower()
    return respuesta == 's'

# ============================================
# CLASE SPINNER
# ============================================

class Spinner:
    
    def __init__(self, mensaje="Procesando"):
        self.mensaje = mensaje
        self.chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        
    def start(self, proceso, check_file=None):
        import time
        
        inicio = time.time()
        idx = 0
        
        while proceso.poll() is None:
            print(f'\r{self.chars[idx % len(self.chars)]} ⎹ {self.mensaje}...', end='', flush=True)
            idx += 1
            time.sleep(0.1)
        
        tiempo = time.time() - inicio
        returncode = proceso.wait()
        
        logger.info(f"{self.mensaje} completado en {tiempo:.1f}s - returncode: {returncode}")
        
        if check_file:
            if os.path.exists(check_file) and os.path.getsize(check_file) > 0:
                size = os.path.getsize(check_file)
                print(f'\r✓ ⎹ {self.mensaje} completado ({tiempo:.1f}s)' + ' ' * 20)
                logger.info(f"Archivo verificado: {check_file} ({formato_bytes(size)})")
                return True
            else:
                print(f'\r✖ ⎹ {self.mensaje} falló - archivo no creado' + ' ' * 20)
                logger.error(f"Archivo no encontrado o vacío: {check_file}")
                return False
        
        if returncode in [0, 2, 18]:
            print(f'\r✓ ⎹ {self.mensaje} completado ({tiempo:.1f}s)' + ' ' * 20)
            if returncode != 0:
                logger.warning(f"Proceso completado con warnings (returncode {returncode})")
            return True
        else:
            print(f'\r✖ ⎹ {self.mensaje} falló (código {returncode})' + ' ' * 20)
            logger.error(f"Proceso falló con returncode {returncode}")
            return False

# ============================================
# CLASE PROGRESS BAR
# ============================================

class ProgressBar:
    
    def __init__(self, total, mensaje="Progreso"):
        self.total = total
        self.mensaje = mensaje
        self.current = 0
        
    def update(self, current):
        self.current = current
        porcentaje = int((current / self.total) * 100)
        barra_llena = int((current / self.total) * 40)
        barra = '█' * barra_llena + '░' * (40 - barra_llena)
        
        print(f'\r{self.mensaje}: [{barra}] {porcentaje}%', end='', flush=True)
        
        if current >= self.total:
            print()
    
    def finish(self):
        self.update(self.total)

# ============================================
# VERIFICACIÓN DE COMANDOS
# ============================================

def verificar_comando(comando):
    import shutil
    return shutil.which(comando) is not None

def verificar_megacmd():
    if not verificar_comando("mega-login"):
        print_error("MegaCMD no está instalado")
        print("💡 Instalá MegaCMD desde: https://mega.nz/cmd")
        return False
    
    import subprocess
    try:
        result = subprocess.run(
            ["mega-whoami"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return True
        else:
            print_error("No hay sesión activa en MegaCMD")
            print("💡 Ejecutá: mega-login tu@email.com tu_contraseña")
            return False
            
    except Exception as e:
        logger.error(f"Error verificando MegaCMD: {e}")
        return False

# ============================================
# MANEJO DE ERRORES
# ============================================

def manejar_error(error, contexto=""):
    mensaje_error = str(error)
    
    if contexto:
        mensaje_completo = f"{contexto}: {mensaje_error}"
    else:
        mensaje_completo = mensaje_error
    
    print_error(mensaje_completo)
    logger.exception(f"Error en {contexto}" if contexto else "Error")
    
    import traceback
    logger.debug(traceback.format_exc())

# ============================================
# FUNCIONES DE ARCHIVO
# ============================================

def obtener_tamano_directorio(ruta):
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(ruta):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total += os.path.getsize(filepath)
                except:
                    pass
    except Exception as e:
        logger.warning(f"Error calculando tamaño de {ruta}: {e}")
    
    return total

def es_directorio_valido(ruta):
    return os.path.exists(ruta) and os.path.isdir(ruta)

# ============================================
# EXPORTAR FUNCIONES
# ============================================

__all__ = [
    'logger',
    'print_msg',
    'print_error',
    'print_warning',
    'formato_bytes',
    'formato_fecha',
    'limpiar_pantalla',
    'pausar',
    'confirmar',
    'Spinner',
    'ProgressBar',
    'verificar_comando',
    'verificar_megacmd',
    'manejar_error',
    'obtener_tamano_directorio',
    'es_directorio_valido'
]
