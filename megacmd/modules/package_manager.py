import os
import tempfile
import zipfile
import shutil

# Variables globales que se setean desde d0ce3_tools.py
CACHE_DIR = None
PACKAGE_DIR = None
LINKS_JSON_URL = None

def set_directories(cache_dir, package_dir, links_url):
    global CACHE_DIR, PACKAGE_DIR, LINKS_JSON_URL
    CACHE_DIR = cache_dir
    PACKAGE_DIR = package_dir
    LINKS_JSON_URL = links_url

def get_package_url():
    try:
        import requests
        response = requests.get(LINKS_JSON_URL, timeout=15)
        if response.status_code != 200:
            return None
        
        config = response.json()
        return config.get("megacmd", {}).get("package")
    except Exception:
        return None

class PackageManager:
    
    @staticmethod
    def is_installed():
        if not PACKAGE_DIR:
            return False
        return os.path.exists(PACKAGE_DIR) and len(os.listdir(PACKAGE_DIR)) > 0
    
    @staticmethod
    def download_and_extract():
        try:
            # Obtener URL del paquete
            package_url = get_package_url()
            if not package_url:
                return False
            
            # Descargar paquete
            import requests
            response = requests.get(package_url, timeout=60)
            if response.status_code != 200:
                return False
            
            # Guardar ZIP temporal
            temp_zip = os.path.join(tempfile.gettempdir(), "megacmd_temp.zip")
            with open(temp_zip, 'wb') as f:
                f.write(response.content)
            
            # Limpiar directorio anterior si existe
            if os.path.exists(CACHE_DIR):
                shutil.rmtree(CACHE_DIR)
            
            # Crear directorio de módulos
            os.makedirs(PACKAGE_DIR, exist_ok=True)
            
            # Extraer solo archivos .py de la carpeta modules/
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    if member.startswith('modules/') and member.endswith('.py'):
                        filename = os.path.basename(member)
                        content = zip_ref.open(member).read()
                        target_path = os.path.join(PACKAGE_DIR, filename)
                        with open(target_path, 'wb') as target:
                            target.write(content)
            
            # Limpiar archivo temporal
            os.remove(temp_zip)
            
            return True
            
        except Exception as e:
            # Log silencioso - el error se maneja en nivel superior
            return False
    
    @staticmethod
    def ensure_installed():
        if PackageManager.is_installed():
            return True
        return PackageManager.download_and_extract()
    
    @staticmethod
    def reload_modules():
        return PackageManager.download_and_extract()
    
    @staticmethod
    def get_installed_modules():
        if not PackageManager.is_installed():
            return []
        
        try:
            modules = []
            for filename in os.listdir(PACKAGE_DIR):
                if filename.endswith('.py') and not filename.startswith('__'):
                    module_name = filename[:-3]  # Remover .py
                    modules.append(module_name)
            return sorted(modules)
        except Exception:
            return []
    
    @staticmethod
    def get_cache_size():
        if not os.path.exists(CACHE_DIR):
            return 0
        
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(CACHE_DIR):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except:
                        pass
        except:
            pass
        
        return total_size
    
    @staticmethod
    def clear_cache():
        try:
            if os.path.exists(CACHE_DIR):
                shutil.rmtree(CACHE_DIR)
            return True
        except Exception:
            return False

# Funciones de utilidad exportadas
def format_size(bytes_num):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} TB"

__all__ = [
    'PackageManager',
    'set_directories',
    'get_package_url',
    'format_size'
]