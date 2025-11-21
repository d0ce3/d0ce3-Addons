import sys
import os
import importlib.util
import json

# Configuración de readline
try:
    import readline
    readline.parse_and_bind(r'"\e[3~": delete-char')
except ImportError:
    pass

# ============================================
# CONFIGURACIÓN
# ============================================
VERSION = "1.0.1"
LINKS_JSON_URL = "https://d0ce3.github.io/d0ce3-Addons/data/links.json"

# Directorio base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "__megacmd_cache__")
PACKAGE_DIR = os.path.join(CACHE_DIR, "modules")

# ============================================
# INSTALAR REQUESTS
# ============================================
def ensure_requests():
    """Asegura que requests esté instalado"""
    try:
        import requests
        return requests
    except ImportError:
        import subprocess
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-q", "requests"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
        return requests

requests = ensure_requests()

# ============================================
# GESTOR DE CONFIGURACIÓN
# ============================================
class ConfigManager:
    """Gestiona URLs desde links.json"""
    
    _config = None
    _last_check = 0
    
    @staticmethod
    def load(force=False):
        """Carga configuración desde links.json"""
        import time
        
        # Cache por 5 minutos
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
        """Obtiene URL del paquete completo"""
        config = ConfigManager.load()
        if not config:
            return None
        return config.get("package")
    
    @staticmethod
    def get_remote_version():
        """Obtiene versión remota"""
        config = ConfigManager.load()
        if not config:
            return None
        return config.get("version")

# ============================================
# GESTOR DE PAQUETES
# ============================================
class PackageManager:
    """Gestiona descarga y extracción del paquete ZIP"""
    
    @staticmethod
    def is_installed():
        """Verifica si el paquete está instalado"""
        return os.path.exists(PACKAGE_DIR) and len(os.listdir(PACKAGE_DIR)) > 0
    
    @staticmethod
    def download_and_extract():
        """Descarga y extrae el paquete completo"""
        try:
            package_url = ConfigManager.get_package_url()
            
            if not package_url:
                return False
            
            response = requests.get(package_url, timeout=60)
            
            if response.status_code != 200:
                return False
            
            # Guardar ZIP temporal
            import tempfile
            temp_zip = os.path.join(tempfile.gettempdir(), "megacmd_temp.zip")
            
            with open(temp_zip, 'wb') as f:
                f.write(response.content)
            
            # Extraer
            import zipfile
            import shutil
            
            # Limpiar directorio anterior si existe
            if os.path.exists(CACHE_DIR):
                shutil.rmtree(CACHE_DIR)
            
            os.makedirs(PACKAGE_DIR, exist_ok=True)
            
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                # Extraer archivos de la carpeta modules/
                for member in zip_ref.namelist():
                    if member.startswith('modules/') and member.endswith('.py'):
                        filename = os.path.basename(member)
                        source = zip_ref.open(member)
                        content = source.read()
                        target_path = os.path.join(PACKAGE_DIR, filename)
                        
                        with open(target_path, 'wb') as target:
                            target.write(content)
            
            # Limpiar ZIP temporal
            os.remove(temp_zip)
            
            return True
            
        except Exception as e:
            return False
    
    @staticmethod
    def ensure_installed():
        """Asegura que el paquete esté instalado"""
        if not PackageManager.is_installed():
            return PackageManager.download_and_extract()
        return True

# ============================================
# CARGADOR DE MÓDULOS
# ============================================
class ModuleLoader:
    """Carga módulos desde el paquete local"""
    
    _cache = {}
    
    @staticmethod
    def load_module(module_name):
        """Carga un módulo desde el paquete"""
        
        # Verificar cache
        if module_name in ModuleLoader._cache:
            return ModuleLoader._cache[module_name]
        
        # Asegurar que el paquete esté instalado
        if not PackageManager.ensure_installed():
            return None
        
        # Ruta del módulo
        module_file = os.path.join(PACKAGE_DIR, f"{module_name}.py")
        
        if not os.path.exists(module_file):
            return None
        
        try:
            # Leer archivo
            with open(module_file, 'r', encoding='utf-8', errors='ignore') as f:
                source_code = f.read()
            
            # Limpiar caracteres problemáticos
            source_code = source_code.replace('\x00', '')
            source_code = source_code.replace('\r\n', '\n')
            
            if not source_code.strip():
                return None
            
            # Crear módulo
            spec = importlib.util.spec_from_loader(module_name, loader=None)
            module = importlib.util.module_from_spec(spec)
            
            # Inyectar dependencias
            module.__dict__['ModuleLoader'] = ModuleLoader
            module.__dict__['CloudModuleLoader'] = ModuleLoader
            module.__dict__['megacmd_tool'] = sys.modules[__name__]
            
            # Ejecutar código del módulo
            exec(source_code, module.__dict__)
            
            # Cachear en memoria
            sys.modules[module_name] = module
            ModuleLoader._cache[module_name] = module
            
            return module
            
        except Exception as e:
            return None
    
    @staticmethod
    def reload_all():
        """Recarga todos los módulos descargando nuevo paquete"""
        print("\n" + "="*60)
        print("🔄 ACTUALIZANDO DESDE GITHUB PAGES")
        print("="*60 + "\n")
        
        # Verificar versión
        remote_version = ConfigManager.get_remote_version()
        
        if remote_version:
            print(f"📌 Versión local:  {VERSION}")
            print(f"📌 Versión remota: {remote_version}")
            
            if remote_version == VERSION:
                print("✓ Ya estás en la última versión")
            else:
                print("⚠ Hay una nueva versión disponible")
            
            print()
        
        # Limpiar cache de Python
        print("🧹 Limpiando cache de módulos...")
        ModuleLoader._cache.clear()
        
        for key in list(sys.modules.keys()):
            if key in ['config', 'utils', 'megacmd', 'backup', 'files', 'autobackup']:
                del sys.modules[key]
                print(f"  ✓ {key} limpiado")
        
        print()
        print("📥 Descargando paquete actualizado...")
        
        # Re-descargar paquete
        if PackageManager.download_and_extract():
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
        """Limpia cache para forzar recarga"""
        ModuleLoader.reload_all()

# Alias para compatibilidad
CloudModuleLoader = ModuleLoader

# ============================================
# FUNCIONES EXPORTADAS
# ============================================

def crear_backup_mega():
    """Crea backup manual"""
    backup = ModuleLoader.load_module("backup")
    if backup and hasattr(backup, 'crear_backup'):
        backup.crear_backup()
    else:
        print("❌ Error: función crear_backup no disponible")
        print("💡 Intentá actualizar los módulos")
        input("\n[+] Enter para continuar...")

def listar_y_descargar_mega():
    """Lista y descarga archivos de MEGA"""
    files = ModuleLoader.load_module("files")
    if files and hasattr(files, 'listar_y_descargar'):
        files.listar_y_descargar()
    else:
        print("❌ Error: función listar_y_descargar no disponible")
        print("💡 Intentá actualizar los módulos")
        input("\n[+] Enter para continuar...")

def gestionar_backups_mega():
    """Gestiona y limpia backups"""
    files = ModuleLoader.load_module("files")
    if files and hasattr(files, 'gestionar_backups'):
        files.gestionar_backups()
    else:
        print("❌ Error: función gestionar_backups no disponible")
        print("💡 Intentá actualizar los módulos")
        input("\n[+] Enter para continuar...")

def subir_archivo_mega():
    """Sube archivo a MEGA"""
    files = ModuleLoader.load_module("files")
    if files and hasattr(files, 'subir_archivo'):
        files.subir_archivo()
    else:
        print("❌ Error: función subir_archivo no disponible")
        print("💡 Intentá actualizar los módulos")
        input("\n[+] Enter para continuar...")

def toggle_autobackup():
    """Configura autobackup"""
    autobackup = ModuleLoader.load_module("autobackup")
    if autobackup and hasattr(autobackup, 'toggle_autobackup'):
        autobackup.toggle_autobackup()
    else:
        print("❌ Error: función toggle_autobackup no disponible")
        print("💡 Intentá actualizar los módulos")
        input("\n[+] Enter para continuar...")

def info_cuenta_mega():
    """Muestra información de cuenta MEGA"""
    files = ModuleLoader.load_module("files")
    if files and hasattr(files, 'info_cuenta'):
        files.info_cuenta()
    else:
        print("❌ Error: función info_cuenta no disponible")
        print("💡 Intentá actualizar los módulos")
        input("\n[+] Enter para continuar...")

def actualizar_modulos():
    """Actualiza todos los módulos desde GitHub Pages"""
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

# ============================================
# INICIALIZACIÓN
# ============================================

def init():
    """Inicializa el sistema silenciosamente"""
    
    # Cargar configuración (silencioso)
    ConfigManager.load()
    
    # Asegurar paquete instalado (silencioso)
    if not PackageManager.ensure_installed():
        return
    
    # Pre-cargar módulo de configuración (silencioso)
    ModuleLoader.load_module("config")
    
    # Inicializar autobackup si está activo (silencioso)
    autobackup = ModuleLoader.load_module("autobackup")
    if autobackup and hasattr(autobackup, 'init_on_load'):
        autobackup.init_on_load()

# Inicializar al cargar el módulo
init()
