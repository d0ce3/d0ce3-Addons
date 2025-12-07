import os
from datetime import datetime
from core.pipeline import Pipeline, PipelineContext
from core.events import event_bus
from .core import BackupCore

def create_backup_pipeline(mode: str = "manual") -> Pipeline:
    pipeline = Pipeline(f"backup.{mode}")
    
    def load_config(ctx: PipelineContext):
        config = CloudModuleLoader.load_module("config")
        
        return {
            'server_folder_name': config.CONFIG.get("server_folder", "servidor_minecraft"),
            'backup_folder': config.CONFIG.get("backup_folder", "/backups"),
            'backup_prefix': config.CONFIG.get("backup_prefix", "MSX"),
            'max_backups': config.CONFIG.get("max_backups", 5)
        }
    
    def find_server(ctx: PipelineContext):
        folder_name = ctx.get('server_folder_name')
        server_folder = BackupCore.find_server_folder(folder_name)
        
        if not server_folder:
            raise FileNotFoundError(f"No se encontró la carpeta '{folder_name}'")
        
        return {'server_folder': server_folder}
    
    def calculate_size(ctx: PipelineContext):
        server_folder = ctx.get('server_folder')
        size_bytes = BackupCore.calculate_folder_size(server_folder)
        size_mb = size_bytes / (1024 * 1024)
        
        return {'size_bytes': size_bytes, 'size_mb': round(size_mb, 2)}
    
    def compress(ctx: PipelineContext):
        server_folder = ctx.get('server_folder')
        prefix = ctx.get('backup_prefix')
        backup_name = BackupCore.generate_backup_name(prefix)
        
        success, backup_path, error = BackupCore.compress_folder_fixed(
            server_folder,
            backup_name,
            max_attempts=3
        )
        
        if not success:
            raise RuntimeError(f"Error en compresión: {error}")
        
        backup_size_bytes = os.path.getsize(backup_path)
        backup_size_mb = backup_size_bytes / (1024 * 1024)
        
        return {
            'backup_name': backup_name,
            'backup_path': backup_path,
            'backup_size_bytes': backup_size_bytes,
            'backup_size_mb': round(backup_size_mb, 2)
        }
    
    def upload_to_mega(ctx: PipelineContext):
        backup_path = ctx.get('backup_path')
        backup_folder = ctx.get('backup_folder')
        
        megacmd = CloudModuleLoader.load_module("megacmd")
        result = megacmd.upload_file(backup_path, backup_folder, silent=False)
        
        if result.returncode != 0:
            raise RuntimeError(f"Error subiendo a MEGA: {result.stderr}")
        
        return {
            'upload_success': True,
            'remote_path': f"{backup_folder}/{ctx.get('backup_name')}"
        }
    
    def cleanup_local(ctx: PipelineContext):
        backup_path = ctx.get('backup_path')
        cleaned = BackupCore.cleanup_local_backup(backup_path)
        return {'local_cleaned': cleaned}
    
    def cleanup_old_backups(ctx: PipelineContext):
        try:
            backup_folder = ctx.get('backup_folder')
            backup_prefix = ctx.get('backup_prefix')
            max_backups = ctx.get('max_backups')
            
            megacmd = CloudModuleLoader.load_module("megacmd")
            result = megacmd.list_files(backup_folder)
            
            if result.returncode != 0:
                return {'cleanup_error': 'No se pudo listar MEGA'}
            
            backups = []
            for line in result.stdout.split('\n'):
                line = line.strip()
                if backup_prefix in line and '.zip' in line:
                    backups.append(line)
            
            def extraer_fecha(nombre_archivo):
                try:
                    partes = nombre_archivo.replace('.zip', '').split('_')
                    if len(partes) >= 3:
                        fecha_str = partes[-2]
                        hora_str = partes[-1]
                        return datetime.strptime(f"{fecha_str}_{hora_str}", "%d-%m-%Y_%H-%M")
                except:
                    pass
                return datetime.min
            
            backups.sort(key=extraer_fecha, reverse=True)
            
            current_backup = ctx.get('backup_name')
            if current_backup not in backups:
                backups.insert(0, current_backup)
            
            if len(backups) > max_backups:
                to_delete = backups[max_backups:]
                deleted_count = 0
                
                utils = CloudModuleLoader.load_module("utils")
                
                for old_backup in to_delete:
                    if old_backup == current_backup:
                        continue
                    
                    result_rm = megacmd.remove_file(f"{backup_folder}/{old_backup}")
                    if result_rm.returncode == 0:
                        deleted_count += 1
                        utils.logger.info(f"Eliminado backup antiguo: {old_backup}")
                
                return {'old_backups_deleted': deleted_count, 'deleted_files': to_delete}
            
            return {'old_backups_deleted': 0}
            
        except Exception as e:
            return {'cleanup_error': str(e)}
    
    pipeline \
        .add_step("load_config", load_config, required=True) \
        .add_step("find_server", find_server, required=True) \
        .add_step("calculate_size", calculate_size, required=False) \
        .add_step("compress", compress, required=True) \
        .add_step("upload", upload_to_mega, required=True) \
        .add_step("cleanup_local", cleanup_local, required=False) \
        .add_step("cleanup_old", cleanup_old_backups, required=False)
    
    return pipeline

def ejecutar_backup(mode: str = "manual") -> dict:
    pipeline = create_backup_pipeline(mode)
    result = pipeline.execute()
    return result

def ejecutar_backup_manual():
    return ejecutar_backup(mode="manual")

def ejecutar_backup_automatico():
    return ejecutar_backup(mode="auto")
