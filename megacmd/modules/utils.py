"""
Utilidades compartidas para MegaCMD Manager
"""

import os
import sys
import logging
from datetime import datetime

# ============================================
# CONFIGURACIÓN DE LOGGING
# ============================================

# Configurar logger
logger = logging.getLogger('megacmd')
logger.setLevel(logging.INFO)

# Ruta del log - usar directorio actual ya que __file__ puede no estar definido
try:
    # Intentar determinar la mejor ruta para el log
    log_file = os.path.join(os.getcwd(), 'addons', 'megacmd_backup.log')
    
    # Asegurar que el directorio existe
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
except:
    # Si falla, usar directorio actual
    log_file = 'megacmd_backup.log'

# Handler para archivo
try:
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Formato del log
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    
    # Agregar handler
    logger.addHandler(file_handler)
except Exception as e:
    # Fallback a consola si no se puede crear archivo
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# ============================================
# FUNCIONES DE UTILIDAD
# ============================================

def print_msg(mensaje, icono="✓"):
    """
    Imprime mensaje con icono
    
    Args:
        mensaje: Texto a mostrar
        icono: Icono a usar (por defecto ✓)
    """
    print(f"{icono} ⎹ {mensaje}")
    logger.info(mensaje)

def print_error(mensaje):
    """
    Imprime mensaje de error
    
    Args:
        mensaje: Texto del error
    """
    print(f"✖ ⎹ {mensaje}")
    logger.error(mensaje)

def print_warning(mensaje):
    """
    Imprime mensaje de advertencia
    
    Args:
        mensaje: Texto de advertencia
    """
    print(f"⚠ ⎹ {mensaje}")
    logger.warning(mensaje)

def formato_bytes(bytes_num):
    """
    Convierte bytes a formato legible
    
    Args:
        bytes_num: Número de bytes
        
    Returns:
        String formateado (ej: "45.3 MB")
    """
    for unidad in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f} {unidad}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} PB"

def formato_fecha(timestamp=None):
    """
    Formatea fecha/hora
    
    Args:
        timestamp: Unix timestamp (None = ahora)
        
    Returns:
        String con formato DD-MM-YYYY_HH-MM
    """
    if timestamp is None:
        dt = datetime.now()
    else:
        dt = datetime.fromtimestamp(timestamp)
    
    return dt.strftime('%d-%m-%Y_%H-%M')

def limpiar_pantalla():
    """Limpia la pantalla de la terminal"""
    os.system('clear' if os.name != 'nt' else 'cls')

def pausar():
    """Pausa esperando Enter del usuario"""
    input("\n[+] Enter para continuar...")

def confirmar(mensaje="¿Continuar?"):
    """
    Solicita confirmación al usuario
    
    Args:
        mensaje: Pregunta a mostrar
        
    Returns:
        True si el usuario confirma (s), False en caso contrario
    """
    respuesta = input(f"{mensaje} (s/n): ").strip().lower()
    return respuesta == 's'

# ============================================
# CLASE SPINNER
# ============================================

class Spinner:
    """Spinner animado para procesos largos"""
    
    def __init__(self, mensaje="Procesando"):
        self.mensaje = mensaje
        self.chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        
    def start(self, proceso, check_file=None):
        """
        Inicia spinner y espera proceso
        
        Args:
            proceso: Proceso subprocess
            check_file: (Opcional) Archivo que debe existir para considerar éxito
                       Si se especifica, se verifica el archivo en vez del returncode
        
        Returns:
            True si el proceso fue exitoso, False en caso contrario
        """
        import time
        
        inicio = time.time()
        idx = 0
        
        # Spinner animado mientras el proceso corre
        while proceso.poll() is None:
            print(f'\r{self.chars[idx % len(self.chars)]} ⎹ {self.mensaje}...', end='', flush=True)
            idx += 1
            time.sleep(0.1)
        
        tiempo = time.time() - inicio
        returncode = proceso.wait()
        
        logger.info(f"{self.mensaje} completado en {tiempo:.1f}s - returncode: {returncode}")
        
        # Estrategia 1: Si se especificó archivo a verificar
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
        
        # Estrategia 2: Verificar returncode
        # Para ZIP, aceptar códigos comunes:
        # 0 = éxito total
        # 2 = warnings (archivos menores saltados)
        # 18 = algunos archivos no accesibles durante compresión (normal en servidores activos)
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
    """Barra de progreso para procesos con porcentaje"""
    
    def __init__(self, total, mensaje="Progreso"):
        self.total = total
        self.mensaje = mensaje
        self.current = 0
        
    def update(self, current):
        """Actualiza la barra de progreso"""
        self.current = current
        porcentaje = int((current / self.total) * 100)
        barra_llena = int((current / self.total) * 40)
        barra = '█' * barra_llena + '░' * (40 - barra_llena)
        
        print(f'\r{self.mensaje}: [{barra}] {porcentaje}%', end='', flush=True)
        
        if current >= self.total:
            print()  # Nueva línea al completar
    
    def finish(self):
        """Completa la barra de progreso"""
        self.update(self.total)

# ============================================
# VERIFICACIÓN DE COMANDOS
# ============================================

def verificar_comando(comando):
    """
    Verifica si un comando está disponible en el sistema
    
    Args:
        comando: Nombre del comando a verificar
        
    Returns:
        True si el comando existe, False en caso contrario
    """
    import shutil
    return shutil.which(comando) is not None

def verificar_megacmd():
    """
    Verifica si MegaCMD está instalado y configurado
    
    Returns:
        True si está disponible, False en caso contrario
    """
    if not verificar_comando("mega-login"):
        print_error("MegaCMD no está instalado")
        print("💡 Instalá MegaCMD desde: https://mega.nz/cmd")
        return False
    
    # Verificar si hay sesión activa
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
    """
    Maneja y registra un error
    
    Args:
        error: Excepción o mensaje de error
        contexto: Contexto donde ocurrió el error
    """
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
    """
    Calcula el tamaño total de un directorio
    
    Args:
        ruta: Ruta del directorio
        
    Returns:
        Tamaño en bytes
    """
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(ruta):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total += os.path.getsize(filepath)
                except:
                    pass  # Ignorar archivos inaccesibles
    except Exception as e:
        logger.warning(f"Error calculando tamaño de {ruta}: {e}")
    
    return total

def es_directorio_valido(ruta):
    """
    Verifica si una ruta es un directorio válido
    
    Args:
        ruta: Ruta a verificar
        
    Returns:
        True si es un directorio válido, False en caso contrario
    """
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
