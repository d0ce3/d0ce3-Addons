import sys
import os
import importlib.util
import json
import time
import atexit

try:
    import readline
    readline.parse_and_bind(r'\e[3~: delete-char')
except ImportError:
    pass

VERSION = "1.0.0"
LINKS_JSON_URL = "https://d0ce3.github.io/d0ce3-Addons/data/links.json"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "__megacmd_cache__")
PACKAGE_DIR = os.path.join(CACHE_DIR, "modules")
AUTOBACKUP_FLAG_FILE = os.path.join(CACHE_DIR, ".autobackup_init")

def ensure_requests():
    try:
        import requests
        return requests
    except ImportError:
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "requests"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
        return requests

requests = ensure_requests()

class ConfigManager:
    _config = None
    _last_check = 0

    @staticmethod
    def load(force=False):
        if not force and ConfigManager._config and (time.time() - ConfigManager._last_check) < 300:
            return ConfigManager._config
        try:
            response = requests.get(LINKS_JSON_URL, timeout=15)
            if response.status_code != 200:
                return ConfigManager._config
            config = response.json()
            ConfigManager._config = config.get("megacmd", {})
            ConfigManager._last_check = time.time()
            return ConfigManager._config
        except Exception:
            return ConfigManager._config

    @staticmethod
    def get_package_url():
        config = ConfigManager.load()
        return config.get("package") if config else None

    @staticmethod
    def get_remote_version():
        config = ConfigManager.load()
        return config.get("version") if config else None

class PackageManager:
    @staticmethod
    def is_installed():
        return os.path.exists(PACKAGE_DIR) and len(os.listdir(PACKAGE_DIR)) > 0

    @staticmethod
    def download_and_extract():
        try:
            package_url = ConfigManager.get_package_url()
            if not package_url:
                return False
            response = requests.get(package_url, timeout=60)
            if response.status_code != 200:
                return False
            import tempfile, zipfile, shutil
            temp_zip = os.path.join(tempfile.gettempdir(), "megacmd_temp.zip")
            with open(temp_zip, 'wb') as f:
                f.write(response.content)
            if os.path.exists(CACHE_DIR):
                shutil.rmtree(CACHE_DIR)
            os.makedirs(PACKAGE_DIR, exist_ok=True)
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    if member.startswith('modules/') and member.endswith('.py'):
                        filename = os.path.basename(member)
                        content = zip_ref.open(member).read()
                        with open(os.path.join(PACKAGE_DIR, filename), 'wb') as target:
                            target.write(content)
            os.remove(temp_zip)
            return True
        except Exception:
            return False

    @staticmethod
    def ensure_installed():
        return True if PackageManager.is_installed() else PackageManager.download_and_extract()

class AutobackupManager:
    @staticmethod
    def is_initialized():
        if not os.path.exists(AUTOBACKUP_FLAG_FILE):
            return False
        try:
            with open(AUTOBACKUP_FLAG_FILE, 'r') as f:
                data = json.load(f)
                init_time = data.get('init_time', 0)
                if time.time() - init_time > 7200:
                    return False
                pid = data.get('pid', 0)
                if pid != os.getpid():
                    try:
                        os.kill(pid, 0)
                        return True
                    except (OSError, ProcessLookupError):
                        return False
                return True
        except:
            return False
    
    @staticmethod
    def mark_initialized():
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(AUTOBACKUP_FLAG_FILE, 'w') as f:
                json.dump({'init_time': time.time(), 'version': VERSION, 'pid': os.getpid()}, f)
            return True
        except:
            return False
    
    @staticmethod
    def clear_flag():
        try:
            if os.path.exists(AUTOBACKUP_FLAG_FILE):
                os.remove(AUTOBACKUP_FLAG_FILE)
            return True
        except:
            return False

class ModuleLoader:
    _cache = {}

    @staticmethod
    def load_module(module_name):
        if module_name in ModuleLoader._cache:
            return ModuleLoader._cache[module_name]
        if not PackageManager.ensure_installed():
            return None
        module_file = os.path.join(PACKAGE_DIR, f"{module_name}.py")
        if not os.path.exists(module_file):
            return None
        try:
            with open(module_file, 'r', encoding='utf-8', errors='ignore') as f:
                source_code = f.read().replace('\x00', '').replace('\r\n', '\n')
            if not source_code.strip():
                return None
            spec = importlib.util.spec_from_loader(module_name, loader=None)
            module = importlib.util.module_from_spec(spec)
            module.__dict__.update({
                '__file__': module_file,
                '__name__': module_name,
                'ModuleLoader': ModuleLoader,
                'CloudModuleLoader': ModuleLoader,
                'megacmd_tool': sys.modules[__name__],
                'SCRIPT_BASE_DIR': BASE_DIR
            })
            exec(source_code, module.__dict__)
            sys.modules[module_name] = module
            ModuleLoader._cache[module_name] = module
            return module
        except Exception as e:
            print(f"⚠ Error cargando módulo {module_name}: {e}")
            return None

    @staticmethod
    def reload_all():
        print("\n" + "="*60)
        print("🔄 ACTUALIZANDO DESDE GITHUB PAGES")
        print("="*60 + "\n")
        remote_version = ConfigManager.get_remote_version()
        if remote_version:
            print(f"🔌 Versión local: {VERSION}")
            print(f"🔌 Versión remota: {remote_version}")
            print("✓ Ya estás en la última versión" if remote_version == VERSION else "⚠ Hay una nueva versión disponible")
            print()
        print("🧹 Limpiando cache de módulos...")
        ModuleLoader._cache.clear()
        for key in ['config', 'utils', 'megacmd', 'backup', 'files', 'autobackup', 'logger']:
            if key in sys.modules:
                del sys.modules[key]
                print(f" ✓ {key} limpiado")
        print("\n📥 Descargando paquete actualizado...")
        success = PackageManager.download_and_extract()
        if success:
            AutobackupManager.clear_flag()
        print("="*60)
        print("✅ ACTUALIZACIÓN COMPLETADA" if success else "❌ ERROR EN ACTUALIZACIÓN")
        print("="*60)
        return success

CloudModuleLoader = ModuleLoader

def call_module_function(module_name, function_name):
    module = ModuleLoader.load_module(module_name)
    if module and hasattr(module, function_name):
        getattr(module, function_name)()
    else:
        print(f"❌ Error: función {function_name} no disponible")
        print("💡 Intentá actualizar los módulos")
        input("\n[+] Enter para continuar...")

ejecutar_backup_manual = lambda: call_module_function("backup", "ejecutar_backup_manual")
listar_y_descargar_mega = lambda: call_module_function("files", "listar_y_descargar")
gestionar_backups_mega = lambda: call_module_function("files", "gestionar_backups")
subir_archivo_mega = lambda: call_module_function("files", "subir_archivo")
configurar_autobackup = lambda: call_module_function("backup", "configurar_autobackup")
info_cuenta_mega = lambda: call_module_function("files", "info_cuenta")
toggle_autobackup = configurar_autobackup

def actualizar_modulos():
    print("\n" + "="*60)
    print("🔄 ACTUALIZAR MÓDULOS")
    print("="*60 + "\n")
    print("Esto descargará la última versión de todos los módulos")
    print("desde GitHub Pages y limpiará el cache local.\n")
    if input("¿Continuar con la actualización? (s/n): ").strip().lower() == 's':
        success = ModuleLoader.reload_all()
        print("\n✅ Módulos actualizados correctamente" if success else "\n❌ Hubo un error durante la actualización")
        print("💡 Todas las funciones ahora usan la última versión" if success else "💡 Verificá tu conexión a internet")
    else:
        print("\n❌ Actualización cancelada\n" + "="*60 + "\n")
    input("Presioná Enter para continuar...")

def init():
    ConfigManager.load()
    if not PackageManager.ensure_installed():
        return
    
    config = ModuleLoader.load_module("config")
    if not config:
        print("⚠ No se pudo cargar módulo de configuración")
        return
    
    logger_mod = ModuleLoader.load_module("logger")
    if logger_mod:
        debug_enabled = config.CONFIG.get("debug_enabled", False)
        if debug_enabled:
            logger_mod.logger_manager.enable_debug()
            logger_mod.info("=" * 60)
            logger_mod.info("SISTEMA INICIADO CON DEBUG ACTIVADO")
            logger_mod.info("=" * 60)
        else:
            logger_mod.debug("Sistema iniciado - logs solo en archivo")
    
    if AutobackupManager.is_initialized():
        if logger_mod:
            logger_mod.debug(f"Autobackup ya inicializado - omitiendo (PID: {os.getpid()})")
        return
    
    autobackup = ModuleLoader.load_module("autobackup")
    if autobackup and hasattr(autobackup, 'init_on_load'):
        try:
            AutobackupManager.mark_initialized()
            autobackup.init_on_load()
            if logger_mod:
                logger_mod.info(f"Autobackup iniciado correctamente - PID: {os.getpid()}")
        except Exception as e:
            AutobackupManager.clear_flag()
            if logger_mod:
                logger_mod.error(f"Error inicializando autobackup: {e}")
                import traceback
                logger_mod.error(traceback.format_exc())

@atexit.register
def debug_paths():
    print(f"\n[DEBUG] BASE_DIR: {BASE_DIR}")
    print(f"[DEBUG] CACHE_DIR: {CACHE_DIR}")
    print(f"[DEBUG] PACKAGE_DIR: {PACKAGE_DIR}")
    print(f"[DEBUG] ¿Existe CACHE_DIR?: {os.path.exists(CACHE_DIR)}")
    if os.path.exists(PACKAGE_DIR):
        print(f"[DEBUG] Módulos en PACKAGE_DIR: {os.listdir(PACKAGE_DIR)}")

@atexit.register
def cleanup_on_exit():
    try:
        if os.path.exists(AUTOBACKUP_FLAG_FILE):
            with open(AUTOBACKUP_FLAG_FILE, 'r') as f:
                if json.load(f).get('pid') == os.getpid():
                    AutobackupManager.clear_flag()
    except:
        pass

init()