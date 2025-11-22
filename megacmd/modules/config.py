import os
import json

# Directorio base - donde se encuentra el script principal
# Esto se usa como referencia para rutas relativas
try:
    # __file__ es inyectado por ModuleLoader
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Si estamos en __megacmd_cache__/modules, subir hasta el directorio raíz del proyecto
    if BASE_DIR.endswith(os.path.join("__megacmd_cache__", "modules")):
        # Subir dos niveles: modules -> __megacmd_cache__ -> directorio raíz
        BASE_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
except NameError:
    # Fallback si __file__ no está disponible
    BASE_DIR = os.getcwd()

# Configuración por defecto
DEFAULT_CONFIG = {
    "backup_folder": "/backups",
    "server_folder": "servidor_minecraft",
    "max_backups": 5,
    "backup_interval_minutes": 5,
    "backup_prefix": "MSX"
}

# Archivo de configuración
CONFIG_FILE = os.path.join(BASE_DIR, "megacmd_config.json")

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