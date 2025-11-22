import os
import json

# Configuración por defecto
DEFAULT_CONFIG = {
    "backup_folder": "/backups",
    "server_folder": "servidor_minecraft",
    "max_backups": 5,
    "backup_interval_minutes": 5,
    "backup_prefix": "MSX"
}

# Archivo de configuración
CONFIG_FILE = "megacmd_config.json"

# ============================================
# FUNCIONES
# ============================================

def cargar_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Actualizar con valores por defecto si faltan claves
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except:
            return DEFAULT_CONFIG.copy()
    else:
        guardar_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

def guardar_config(config=None):
    try:
        if config is None:
            config = CONFIG
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Error guardando configuración: {e}")
        return False

def get(key, default=None):
    return CONFIG.get(key, default)

def set(key, value):
    CONFIG[key] = value
    guardar_config()

# Cargar configuración al importar
CONFIG = cargar_config()
