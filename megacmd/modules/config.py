"""
Módulo de configuración compartida
"""

import json
import os

# Configuración
BASE_DIR = os.getcwd()
CONFIG_FILE = os.path.join(BASE_DIR, "megacmd_config.json")

DEFAULT_CONFIG = {
    "backup_folder": "/backups",
    "server_folder": "servidor_minecraft",
    "max_backups": 5,
    "backup_interval_minutes": 30,
    "backup_prefix": "MSX"
}

def safe_path(*parts):
    """Genera ruta absoluta desde BASE_DIR"""
    return os.path.join(BASE_DIR, *parts)

def load_config():
    """Carga configuración"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    else:
        # Crear config por defecto
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """Guarda configuración"""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

# Exportar config global
CONFIG = load_config()
