import os
import sys
import json

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    try:
        BASE_DIR = SCRIPT_BASE_DIR
    except NameError:
        try:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            if module_dir.endswith(os.path.join("__megacmd_cache__", "modules")):
                cache_dir = os.path.dirname(module_dir)
                BASE_DIR = os.path.dirname(cache_dir)
            else:
                BASE_DIR = module_dir
        except NameError:
            BASE_DIR = os.getcwd()

DEFAULT_CONFIG = {
    "backup_folder": "/backups",
    "server_folder": "servidor_minecraft",
    "max_backups": 5,
    "backup_interval_minutes": 30,
    "backup_prefix": "MSX",
    "autobackup_enabled": False,
    "debug_enabled": False
}

CONFIG_FILE = os.path.join(BASE_DIR, "megacmd_config.json")

def cargar_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
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
        return False

def get(key, default=None):
    return CONFIG.get(key, default)

def set(key, value):
    CONFIG[key] = value
    guardar_config()

CONFIG = cargar_config()