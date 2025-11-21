"""
Utilidades compartidas por todos los módulos
"""

import os
import sys
import subprocess
import time
import logging
from datetime import datetime, timezone, timedelta


config = CloudModuleLoader.load_module("config")

# ============================================
# LOGGER
# ============================================
def get_logger():
    """Obtiene logger"""
    logger = logging.getLogger("megacmd")
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        log_file = config.safe_path("addons", "megacmd_backup.log")
        os.makedirs(config.safe_path("addons"), exist_ok=True)

        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(handler)

    return logger

logger = get_logger()

# ============================================
# UI
# ============================================
def clear_screen():
    """Limpia pantalla"""
    os.system('clear')

def print_msg(text, symbol=""):
    """Imprime mensaje"""
    if symbol:
        print(f"{symbol} ⎹ {text}")
    else:
        print(text)

def get_input(prompt, symbol="➥"):
    """Obtiene input"""
    return input(f"{symbol} ⎹ {prompt} ❱ ").strip()

# ============================================
# SISTEMA
# ============================================
def get_argentina_time():
    """Obtiene hora argentina"""
    utc_now = datetime.now(timezone.utc)
    argentina_time = utc_now - timedelta(hours=3)
    return argentina_time.replace(tzinfo=None)

def run_command(cmd, silent=False):
    """Ejecuta comando"""
    result = subprocess.run(cmd, capture_output=True, text=True)

    if not silent:
        if result.stdout:
            logger.debug(f"[CMD] stdout: {result.stdout[:200]}")
        if result.stderr:
            logger.debug(f"[CMD] stderr: {result.stderr[:200]}")

    return result.returncode == 0, result.stdout, result.stderr

# ============================================
# SPINNER
# ============================================
class Spinner:
    """Spinner animado"""

    def __init__(self, mensaje="Procesando"):
        self.mensaje = mensaje
        self.animacion = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.idx = 0
        self.inicio = None

    def start(self, proceso):
        """Muestra spinner"""
        self.inicio = time.time()
        sys.stdout.write(f"{self.mensaje}... {self.animacion[self.idx]}")
        sys.stdout.flush()

        while proceso.poll() is None:
            time.sleep(0.1)
            self.idx = (self.idx + 1) % len(self.animacion)
            sys.stdout.write(f"\r{self.mensaje}... {self.animacion[self.idx]}")
            sys.stdout.flush()

        proceso.wait()
        duracion = time.time() - self.inicio
        sys.stdout.write(f"\r{self.mensaje}... ✓ ({duracion:.1f}s)\n")
        sys.stdout.flush()

        logger.info(f"{self.mensaje} completado en {duracion:.1f}s - returncode: {proceso.returncode}")

        return proceso.returncode == 0
