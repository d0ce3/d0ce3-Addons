import os
import zipfile
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional, List
import time

TIMEZONE_ARG = timezone(timedelta(hours=-3))

class BackupCore:
    
    @staticmethod
    def generate_backup_name(prefix: str = "MSX") -> str:
        timestamp = datetime.now(TIMEZONE_ARG).strftime("%d-%m-%Y_%H-%M")
        return f"{prefix}_{timestamp}.zip"
    
    @staticmethod
    def find_server_folder(folder_name: str, search_paths: Optional[List[str]] = None) -> Optional[str]:
        if search_paths is None:
            codespace = os.environ.get('CODESPACE_NAME', 'unknown')
            search_paths = [
                f"/workspaces/{codespace}/{folder_name}",
                os.path.join(os.getcwd(), folder_name),
                os.path.join(os.path.dirname(os.getcwd()), folder_name),
                os.path.expanduser(f"~/{folder_name}"),
            ]
        
        for path in search_paths:
            if path and os.path.exists(path) and os.path.isdir(path):
                return path
        
        if os.path.exists("/workspaces"):
            try:
                for item in os.listdir("/workspaces"):
                    possible = os.path.join("/workspaces", item, folder_name)
                    if os.path.exists(possible) and os.path.isdir(possible):
                        return possible
            except:
                pass
        
        return None
    
    @staticmethod
    def calculate_folder_size(folder_path: str) -> int:
        total_size = 0
        try:
            for dirpath, _, filenames in os.walk(folder_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except:
                        pass
        except Exception:
            pass
        
        return total_size
    
    @staticmethod
    def compress_folder_fixed(source_folder: str, output_filename: str, max_attempts: int = 3) -> Tuple[bool, Optional[str], Optional[str]]:
        parent_dir = os.path.dirname(source_folder)
        folder_name = os.path.basename(source_folder)
        backup_path = os.path.join(parent_dir, output_filename)
        
        for attempt in range(1, max_attempts + 1):
            try:
                if os.path.exists(backup_path):
                    try:
                        os.remove(backup_path)
                    except:
                        pass
                
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(source_folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, source_folder)
                            arcname = os.path.join(folder_name, arcname)
                            
                            try:
                                zipf.write(file_path, arcname)
                            except Exception as e:
                                if attempt == max_attempts:
                                    import logging
                                    logging.debug(f"No se pudo agregar {file}: {e}")
                
                if os.path.exists(backup_path):
                    size = os.path.getsize(backup_path)
                    
                    if size < 1024:
                        if attempt < max_attempts:
                            time.sleep(attempt * 2)
                            continue
                        return (False, None, "ZIP muy pequeño (< 1KB)")
                    
                    try:
                        with zipfile.ZipFile(backup_path, 'r') as zipf:
                            bad_file = zipf.testzip()
                            if bad_file:
                                if attempt < max_attempts:
                                    time.sleep(attempt * 2)
                                    continue
                                return (False, None, f"ZIP corrupto: {bad_file}")
                    except zipfile.BadZipFile:
                        if attempt < max_attempts:
                            time.sleep(attempt * 2)
                            continue
                        return (False, None, "ZIP corrupto")
                    
                    return (True, backup_path, None)
                else:
                    if attempt < max_attempts:
                        time.sleep(attempt * 2)
                        continue
                    return (False, None, "No se pudo crear el archivo")
            
            except Exception as e:
                if attempt == max_attempts:
                    return (False, None, f"Error: {str(e)}")
                time.sleep(attempt * 2)
        
        if os.path.exists(backup_path):
            try:
                os.remove(backup_path)
            except:
                pass
        
        return (False, None, "Todos los intentos fallaron")
    
    @staticmethod
    def cleanup_local_backup(backup_path: str) -> bool:
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
                return True
        except Exception:
            pass
        return False