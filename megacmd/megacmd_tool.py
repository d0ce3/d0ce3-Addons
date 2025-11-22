import sys
import os
import importlib.util
import json
import time
import atexit
import signal

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

# Archivo de flag para control de inicialización persistente
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
        import time
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
        except Exception as e:
            return ConfigManager._config

    @staticmethod
    def get_package_url():
        config = ConfigManager.load()
        if not config:
            return None
        return config.get("package")

    @staticmethod
    def get_remote_version():
        config = ConfigManager.load()
        if not config:
            return None
        return config.get("version")

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
            import tempfile
            temp_zip = os.path.join(tempfile.gettempdir(), "megacmd_temp.zip")
            with open(temp_zip, 'wb') as f:
                f.write(response.content)
            import zipfile
            import shutil
            if os.path.exists(CACHE_DIR):
                shutil.rmtree(CACHE_DIR)
            os.makedirs(PACKAGE_DIR, exist_ok=True)
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    if member.startswith('modules/') and member.endswith('.py'):
                        filename = os.path.basename(member)
                        source = zip_ref.open(member)
                        content = source.read()
                        target_path = os.path.join(PACKAGE_DIR, filename)
                        with open(target_path, 'wb') as target:
                            target.write(content)
            os.remove(temp_zip)
            return True
        except Exception as e:
            return False

    @staticmethod
    def ensure_installed():
        if not PackageManager.is_installed():
            return PackageManager.download_and_extract()
        return True

class AutobackupManager:
    """Gestiona la inicialización única del autobackup usando archivo de flag"""
    
    @staticmethod
    def is_initialized():
        """Verifica si el autobackup ya fue inicializado en esta sesión"""
        if not os.path.exists(AUTOBACKUP_FLAG_FILE):
            return False
        try:
            with open(AUTOBACKUP_FLAG_FILE, 'r') as f:
                data = json.load(f)
                # Verificar que no haya pasado más de 2 horas (sesión caducada)
                init_time = data.get('init_time', 0)
                elapsed = time.time() - init_time
                if elapsed > 7200:  # 2 horas
                    return False
                # Verificar que el PID del proceso sea válido
                pid = data.get('pid', 0)
                if pid != os.getpid():
                    # Es de otro proceso, verificar si todavía existe
                    try:
                        # En Unix, esto verifica si el proceso existe
                        os.kill(pid, 0)
                        # El proceso existe, está inicializado
                        return True
                    except (OSError, ProcessLookupError):
                        # El proceso ya no existe, podemos reinicializar
                        return False
                return True
        except:
            return False
    
    @staticmethod
    def mark_initialized():
        """Marca el autobackup como inicializado"""
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(AUTOBACKUP_FLAG_FILE, 'w') as f:
                json.dump({
                    'init_time': time.time(),
                    'version': VERSION,
                    'pid': os.getpid()
                }, f)
            return True
        except:
            return False
    
    @staticmethod
    def clear_flag():
        """Elimina el flag de inicialización"""
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
                source_code = f.read()
            source_code = source_code.replace('\x00', '')
            source_code = source_code.replace('\r\n', '\n')
            if not source_code.strip():
                return None
            spec = importlib.util.spec_from_loader(module_name, loader=None)
            module = importlib.util.module_from_spec(spec)
            # Inyectar variables necesarias
            module.__dict__['__file__'] = module_file
            module.__dict__['__name__'] = module_name
            module.__dict__['ModuleLoader'] = ModuleLoader
            module.__dict__['CloudModuleLoader'] = ModuleLoader
            module.__dict__['megacmd_tool'] = sys.modules[__name__]
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
            print(f"📌 Versión local: {VERSION}")
            print(f"📌 Versión remota: {remote_version}")
            if remote_version == VERSION:
                print("✓ Ya estás en la última versión")
            else:
                print("⚠ Hay una nueva versión disponible")
            print()
        print("🧹 Limpiando cache de módulos...")
        ModuleLoader._cache.clear()
        for key in list(sys.modules.keys()):
            if key in ['config', 'utils', 'megacmd', 'backup', 'files', 'autobackup']:
                del sys.modules[key]
                print(f" ✓ {key} limpiado")
        print()
        print("📥 Descargando paquete actualizado...")
        if PackageManager.download_and_extract():
            # Limpiar el flag de autobackup cuando se actualizan módulos
            AutobackupManager.clear_flag()
            print("="*60)
            print("✅ ACTUALIZACIÓN COMPLETADA")
            print("="*60)
            return True
        else:
            print("="*60)
            print("❌ ERROR EN ACTUALIZACIÓN")
            print("="*60)
            return False

    @staticmethod
    def clear_cache():
        ModuleLoader.reload_all()

CloudModuleLoader = ModuleLoader

def ejecutar_backup_manual():
    backup = ModuleLoader.load_module("backup")
    if backup and hasattr(backup, 'ejecutar_backup_manual'):
        backup.ejecutar_backup_manual()
    else:
        print("❌ Error: función ejecutar_backup_manual no disponible")
        print("💡 Intentá actualizar los módulos")
        input("\n[+] Enter para continuar...")

def listar_y_descargar_mega():
    files = ModuleLoader.load_module("files")
    if files and hasattr(files, 'listar_y_descargar'):
        files.listar_y_descargar()
    else:
        print("❌ Error: función listar_y_descargar no disponible")
        print("💡 Intentá actualizar los módulos")
        input("\n[+] Enter para continuar...")

def gestionar_backups_mega():
    files = ModuleLoader.load_module("files")
    if files and hasattr(files, 'gestionar_backups'):
        files.gestionar_backups()
    else:
        print("❌ Error: función gestionar_backups no disponible")
        print("💡 Intentá actualizar los módulos")
        input("\n[+] Enter para continuar...")

def subir_archivo_mega():
    files = ModuleLoader.load_module("files")
    if files and hasattr(files, 'subir_archivo'):
        files.subir_archivo()
    else:
        print("❌ Error: función subir_archivo no disponible")
        print("💡 Intentá actualizar los módulos")
        input("\n[+] Enter para continuar...")

def toggle_autobackup():
    autobackup = ModuleLoader.load_module("autobackup")
    if autobackup and hasattr(autobackup, 'toggle_autobackup'):
        autobackup.toggle_autobackup()
    else:
        print("❌ Error: función toggle_autobackup no disponible")
        print("💡 Intentá actualizar los módulos")
        input("\n[+] Enter para continuar...")

def info_cuenta_mega():
    files = ModuleLoader.load_module("files")
    if files and hasattr(files, 'info_cuenta'):
        files.info_cuenta()
    else:
        print("❌ Error: función info_cuenta no disponible")
        print("💡 Intentá actualizar los módulos")
        input("\n[+] Enter para continuar...")

def actualizar_modulos():
    import time
    print("\n" + "="*60)
    print("🔄 ACTUALIZAR MÓDULOS")
    print("="*60 + "\n")
    print("Esto descargará la última versión de todos los módulos")
    print("desde GitHub Pages y limpiará el cache local.\n")
    confirmar = input("¿Continuar con la actualización? (s/n): ").strip().lower()
    if confirmar == 's':
        success = ModuleLoader.reload_all()
        if success:
            print("\n✅ Módulos actualizados correctamente")
            print("💡 Todas las funciones ahora usan la última versión")
        else:
            print("\n❌ Hubo un error durante la actualización")
            print("💡 Verificá tu conexión a internet")
    else:
        print("\n❌ Actualización cancelada")
        print("\n" + "="*60 + "\n")
    input("Presioná Enter para continuar...")

def init():
    """Inicialización del sistema con control de autobackup único"""
    
    # Cargar configuración
    ConfigManager.load()
    
    # Asegurar que los paquetes están instalados
    if not PackageManager.ensure_installed():
        return
    
    # Cargar módulos necesarios
    config = ModuleLoader.load_module("config")
    if not config:
        print("⚠ No se pudo cargar módulo de configuración")
        return
    
    utils = ModuleLoader.load_module("utils")
    
    # Verificar si el autobackup ya fue inicializado
    if AutobackupManager.is_initialized():
        if utils and hasattr(utils, 'logger'):
            utils.logger.debug("Autobackup ya inicializado - omitiendo (PID: {})".format(os.getpid()))
        return
    
    # Cargar e inicializar autobackup solo si no fue inicializado antes
    autobackup = ModuleLoader.load_module("autobackup")
    if autobackup and hasattr(autobackup, 'init_on_load'):
        try:
            # Marcar ANTES de inicializar para prevenir race conditions
            AutobackupManager.mark_initialized()
            autobackup.init_on_load()
            if utils and hasattr(utils, 'logger'):
                utils.logger.info("Autobackup iniciado correctamente - PID: {}".format(os.getpid()))
        except Exception as e:
            # Si falla, limpiar el flag para permitir reintentos
            AutobackupManager.clear_flag()
            if utils and hasattr(utils, 'logger'):
                utils.logger.error(f"Error inicializando autobackup: {e}")
                import traceback
                utils.logger.error(traceback.format_exc())

# Inicializar el sistema
init()