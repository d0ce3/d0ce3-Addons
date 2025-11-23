import os
import sys
from datetime import datetime

try:
    logger_module = CloudModuleLoader.load_module("logger")
    if logger_module:
        logger_manager = logger_module.logger_manager
        logger = logger_module.logger
    else:
        import logging
        logger = logging.getLogger('megacmd')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger_manager = None
except:
    import logging
    logger = logging.getLogger('megacmd')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger_manager = None

def print_msg(mensaje, icono="✓"):
    print(f"{icono} {mensaje}")
    logger.info(mensaje)

def print_error(mensaje):
    print(f"✖ {mensaje}")
    logger.error(mensaje)

def print_warning(mensaje):
    print(f"⚠ {mensaje}")
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
    return dt.strftime("%d-%m-%Y %H:%M")

def limpiar_pantalla():
    os.system('clear' if os.name != 'nt' else 'cls')

def pausar():
    input("Enter para continuar...")

def confirmar(mensaje="¿Continuar?"):
    respuesta = input(f"{mensaje} (s/n): ").strip().lower()
    return respuesta == 's'

class Spinner:
    def __init__(self, mensaje="Procesando"):
        self.mensaje = mensaje
        self.chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    
    def start(self, proceso, check_file=None):
        import time
        inicio = time.time()
        idx = 0
        
        while proceso.poll() is None:
            print(f"\r{self.chars[idx % len(self.chars)]} {self.mensaje}...", end='', flush=True)
            idx += 1
            time.sleep(0.1)
        
        tiempo = time.time() - inicio
        returncode = proceso.wait()
        logger.info(f"{self.mensaje} completado en {tiempo:.1f}s - returncode {returncode}")
        
        if check_file:
            if os.path.exists(check_file) and os.path.getsize(check_file) > 0:
                size = os.path.getsize(check_file)
                print(f"\r{self.mensaje} completado ({tiempo:.1f}s)" + " " * 20)
                logger.info(f"Archivo verificado {check_file}: {formato_bytes(size)}")
                return True
            else:
                print(f"\r{self.mensaje} falló - archivo no creado" + " " * 20)
                logger.error(f"Archivo no encontrado o vacío: {check_file}")
                return False
        
        if returncode in [0, 2, 18]:
            print(f"\r{self.mensaje} completado ({tiempo:.1f}s)" + " " * 20)
            if returncode != 0:
                logger.warning(f"Proceso completado con warnings (returncode {returncode})")
            return True
        else:
            print(f"\r{self.mensaje} falló (código {returncode})" + " " * 20)
            logger.error(f"Proceso falló con returncode {returncode}")
            return False

class ProgressBar:
    def __init__(self, total, mensaje="Progreso"):
        self.total = total
        self.mensaje = mensaje
        self.current = 0
    
    def update(self, current):
        self.current = current
        porcentaje = int((current / self.total) * 100)
        barra_llena = int((current / self.total) * 40)
        barra = "█" * barra_llena + "░" * (40 - barra_llena)
        print(f"\r{self.mensaje}: {barra} {porcentaje}%", end='', flush=True)
        
        if current >= self.total:
            print()
    
    def finish(self):
        self.update(self.total)

def verificar_comando(comando):
    import shutil
    return shutil.which(comando) is not None

def verificar_megacmd():
    try:
        megacmd = CloudModuleLoader.load_module("megacmd")
        if not megacmd:
            print_error("No se pudo cargar el módulo megacmd")
            return False
        
        if not megacmd.is_installed():
            print()
            print_msg("Instalando MegaCMD...", "🔧")
            print()
            
            if not megacmd.install():
                print_error("No se pudo instalar MegaCMD")
                print("💡 Instalá MegaCMD manualmente desde: https://mega.nz/cmd")
                pausar()
                return False
        
        if not megacmd.is_logged_in():
            if not megacmd.login():
                print_error("No se pudo iniciar sesión en MEGA")
                pausar()
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error verificando MegaCMD: {e}")
        print_error("Error al verificar MegaCMD")
        return False

def manejar_error(error, contexto=None):
    mensaje_error = str(error)
    if contexto:
        mensaje_completo = f"{contexto}: {mensaje_error}"
    else:
        mensaje_completo = mensaje_error
    
    print_error(mensaje_completo)
    logger.exception(f"Error en {contexto}" if contexto else "Error")
    
    import traceback
    logger.debug(traceback.format_exc())

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

__all__ = [
    'logger',
    'logger_manager',
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
