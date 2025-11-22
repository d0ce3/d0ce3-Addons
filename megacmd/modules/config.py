import os
import json

# Directorio base - donde se encuentra el script principal
# Esto se usa como referencia para rutas relativas
try:
    # __file__ es inyectado por ModuleLoader
    # Ejemplo: /workspaces/Dregoro/servidor_minecraft/__megacmd_cache__/modules/config.py
    module_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Si estamos en __megacmd_cache__/modules, subir hasta el directorio raíz del proyecto
    if module_dir.endswith(os.path.join("__megacmd_cache__", "modules")):
        # modules -> __megacmd_cache__ -> directorio del script (servidor_minecraft)
        cache_dir = os.path.dirname(module_dir)  # __megacmd_cache__
        script_dir = os.path.dirname(cache_dir)  # servidor_minecraft
        
        # Verificar si megacmd_tool.py está en este directorio
        if os.path.exists(os.path.join(script_dir, "megacmd_tool.py")):
            # Este ES el directorio del script, usar este como base
            BASE_DIR = script_dir
        else:
            # El script debe estar un nivel arriba
            BASE_DIR = os.path.dirname(script_dir)
    else:
        # Caso normal: usar el directorio del módulo
        BASE_DIR = module_dir
        
except NameError:
    # Fallback si __file__ no está disponible
    BASE_DIR = os.getcwd()

# Log para debug (se puede comentar después)
import sys
if hasattr(sys, 'stderr'):
    print(f"[CONFIG DEBUG] BASE_DIR establecido en: {BASE_DIR}", file=sys.stderr)

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