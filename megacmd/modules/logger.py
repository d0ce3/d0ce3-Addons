import os
import sys
import logging
from datetime import datetime

ADDONS_DIR = os.path.expanduser('~/.d0ce3_addons')
os.makedirs(ADDONS_DIR, exist_ok=True)

class LoggerManager:
    _instance = None
    _logger = None
    _debug_enabled = False
    _log_file = None
    _console_handler = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._setup_logger()
    
    def _setup_logger(self):
        self._logger = logging.getLogger('megacmd')
        self._logger.setLevel(logging.DEBUG)
        
        if self._logger.handlers:
            self._logger.handlers.clear()
        
        try:
            config = CloudModuleLoader.load_module("config")
            debug_enabled = config.CONFIG.get("debug_enabled", False) if config else False
            base_dir = config.BASE_DIR if config else os.getcwd()
        except:
            debug_enabled = False
            base_dir = os.getcwd()
        
        try:
            if debug_enabled:
                log_dir = os.path.join(base_dir, 'addons')
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir, exist_ok=True)
                self._log_file = os.path.join(log_dir, 'megacmd_full.log')
            else:
                self._log_file = os.path.join(ADDONS_DIR, '.megacmd.log')
        except:
            self._log_file = os.path.join(ADDONS_DIR, '.megacmd.log')
        
        try:
            file_handler = logging.FileHandler(self._log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] [%(module)s:%(funcName)s:%(lineno)d] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self._logger.addHandler(file_handler)
        except Exception as e:
            print(f"Error creando archivo de log: {e}", file=sys.stderr)
        
        self._console_handler = logging.StreamHandler()
        self._console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self._console_handler.setFormatter(console_formatter)
    
    def enable_debug(self):
        was_enabled = self._debug_enabled
        if not self._debug_enabled:
            self._debug_enabled = True
            if self._console_handler not in self._logger.handlers:
                self._logger.addHandler(self._console_handler)
        if not was_enabled and self._debug_enabled:
            self._logger.info("Modo debug activado en consola")
    
    def disable_debug(self):
        was_enabled = self._debug_enabled
        if self._debug_enabled:
            self._debug_enabled = False
            if self._console_handler in self._logger.handlers:
                self._logger.removeHandler(self._console_handler)
        if was_enabled and not self._debug_enabled:
            self._logger.info("Modo debug desactivado en consola")
    
    def is_debug_enabled(self):
        return self._debug_enabled
    
    def get_log_file_path(self):
        return self._log_file
    
    def info(self, msg):
        self._logger.info(msg)
    
    def warning(self, msg):
        self._logger.warning(msg)
    
    def error(self, msg):
        self._logger.error(msg)
    
    def debug(self, msg):
        self._logger.debug(msg)
    
    def exception(self, msg):
        self._logger.exception(msg)
    
    def download_logs(self, dest_path=None):
        if dest_path is None:
            dest_path = f"megacmd_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        try:
            import shutil
            if os.path.exists(self._log_file):
                shutil.copy2(self._log_file, dest_path)
                return dest_path
            else:
                return None
        except Exception as e:
            self._logger.error(f"Error copiando logs: {e}")
            return None
    
    def clear_logs(self):
        try:
            if os.path.exists(self._log_file):
                with open(self._log_file, 'w') as f:
                    f.write('')
                self._logger.info("Logs limpiados")
                return True
        except Exception as e:
            self._logger.error(f"Error limpiando logs: {e}")
            return False

logger_manager = LoggerManager()
logger = logger_manager._logger

info = logger_manager.info
warning = logger_manager.warning
error = logger_manager.error
debug = logger_manager.debug
exception = logger_manager.exception

def log_backup_inicio():
    logger_manager.info("========== INICIO BACKUP ==========")

def log_backup_fin():
    logger_manager.info("========== FIN BACKUP ==========")

def log_backup_auto_inicio():
    logger_manager.info("========== INICIO BACKUP AUTOMÁTICO ==========")

def log_backup_auto_fin():
    logger_manager.info("========== FIN BACKUP AUTOMÁTICO ==========")

def log_backup_auto_exito(backup_name, size_mb):
    logger_manager.info(f"Backup automático exitoso: {backup_name} ({size_mb:.1f} MB)")

def log_backup_auto_error(error_msg):
    logger_manager.error(f"Error en backup automático: {error_msg}")

def log_config_carpeta(server_folder_config, base_dir, cwd, parent_dir, resolved, exists, destino):
    logger_manager.info(f"Configuración - Carpeta config: {server_folder_config}")
    logger_manager.info(f"Configuración - BASE_DIR: {base_dir}")
    logger_manager.info(f"Configuración - os.getcwd(): {cwd}")
    logger_manager.info(f"Configuración - parent de BASE_DIR: {parent_dir}")
    logger_manager.info(f"Configuración - Carpeta resuelta: {resolved}")
    logger_manager.info(f"Configuración - ¿Existe? {exists}")
    logger_manager.info(f"Configuración - Destino: {destino}")

def log_carpeta_encontrada(ubicacion):
    logger_manager.info(f"Carpeta del servidor encontrada en: {ubicacion}")

def log_carpeta_no_encontrada(nombre_carpeta):
    logger_manager.error(f"No se pudo encontrar la carpeta '{nombre_carpeta}'")

def log_tamano_carpeta(size_mb):
    logger_manager.info(f"Tamaño de carpeta: {size_mb:.1f} MB")

def log_nombre_backup(backup_name):
    logger_manager.info(f"Nombre de backup: {backup_name}")

def log_compresion_inicio():
    logger_manager.info("Iniciando compresión...")

def log_compresion_error():
    logger_manager.error("Fallo en compresión")

def log_compresion_auto_error():
    logger_manager.error("Error durante compresión automática")

def log_archivo_creado(backup_name, size_mb):
    logger_manager.info(f"Archivo creado: {backup_name} ({size_mb:.1f} MB)")

def log_archivo_no_encontrado(backup_name):
    logger_manager.error(f"Archivo {backup_name} no encontrado")

def log_subida_inicio():
    logger_manager.info("Iniciando subida a MEGA...")

def log_subida_error():
    logger_manager.error("Fallo en subida a MEGA")

def log_subida_auto_error():
    logger_manager.error("Error al subir backup automático a MEGA")

def log_subida_exitosa(backup_folder, backup_name):
    logger_manager.info(f"Backup subido exitosamente a {backup_folder}/{backup_name}")

def log_subida_auto_exitosa(backup_folder, backup_name):
    logger_manager.info(f"Backup automático subido exitosamente: {backup_folder}/{backup_name}")

def log_archivo_local_eliminado():
    logger_manager.info("Archivo local eliminado")

def log_archivo_local_error(error):
    logger_manager.warning(f"Error eliminando archivo local: {error}")

def log_backup_cancelado():
    logger_manager.info("Backup cancelado por usuario")

def log_carpeta_no_existe(carpeta):
    logger_manager.error(f"Carpeta {carpeta} no encontrada")

def log_carpeta_auto_no_existe(carpeta):
    logger_manager.error(f"Carpeta {carpeta} no encontrada, se cancela backup automático")

def log_error_backup(error, traceback_str):
    logger_manager.error(f"Error en crear_backup: {error}")
    logger_manager.error(traceback_str)

def log_error_backup_auto(error, traceback_str):
    logger_manager.error(f"Error en backup automático: {error}")
    logger_manager.error(traceback_str)

def log_autobackup_desactivado():
    logger_manager.info("Autobackup desactivado, no se ejecutará")

def log_autobackup_habilitado():
    logger_manager.info("Autobackup habilitado")

def log_autobackup_deshabilitado():
    logger_manager.info("Autobackup deshabilitado")

def log_timer_activo(pid):
    logger_manager.info(f"Timer de autobackup ya activo en proceso - omitiendo (PID actual: {pid})")

def log_timer_local_activo():
    logger_manager.info("Timer local de autobackup ya activo, no se crea uno nuevo")

def log_timer_programado(interval_minutes, pid):
    logger_manager.info(f"Nuevo timer programado para {interval_minutes} minutos (PID: {pid})")
    logger_manager.info(f"Autobackup activado - cada {interval_minutes} minutos")

def log_timer_detenido():
    logger_manager.info("Timer de autobackup detenido")

def log_rcon_error_inicio(error):
    logger_manager.warning(f"No se pudo enviar mensaje RCON de inicio: {error}")

def log_rcon_error_fin(error):
    logger_manager.warning(f"No se pudo enviar mensaje RCON de fin: {error}")

def log_limpiar_backups(max_backups):
    logger_manager.info(f"Limpiando backups antiguos (mantener {max_backups})...")

def log_backups_encontrados(cantidad):
    logger_manager.info(f"Backups encontrados: {cantidad}")

def log_backup_eliminado(archivo):
    logger_manager.info(f"Eliminado: {archivo}")

def log_error_eliminar_backup(archivo):
    logger_manager.warning(f"Error eliminando {archivo}")

def log_limpieza_completada(cantidad):
    logger_manager.info(f"Limpieza completada - {cantidad} backups eliminados")

def log_menu_autobackup():
    logger_manager.info("========== MENÚ CONFIGURAR AUTOBACKUP ==========")

def log_autobackup_activado_usuario():
    logger_manager.info("Autobackup activado por usuario")

def log_autobackup_desactivado_usuario():
    logger_manager.info("Autobackup desactivado por usuario")

def log_intervalo_cambiado(minutos):
    logger_manager.info(f"Intervalo cambiado a {minutos} minutos")

def log_destino_cambiado(destino):
    logger_manager.info(f"Destino MEGA cambiado a: {destino}")

def log_max_backups_cambiado(cantidad):
    logger_manager.info(f"Máximo de backups cambiado a {cantidad}")

def log_salir_config():
    logger_manager.info("Saliendo de configuración de autobackup")

def log_autobackup_verificando():
    logger_manager.info("Autobackup está habilitado, verificando timer...")

def log_timer_no_activo():
    logger_manager.info("No hay timer activo, iniciando autobackup...")

def log_timer_otro_proceso():
    logger_manager.info("Timer ya activo en otro proceso, no se inicia uno nuevo")

def log_autobackup_no_habilitado():
    logger_manager.info("Autobackup no está habilitado")

def log_error_listando_backups(error):
    logger_manager.error(f"Error listando backups: {error}")

def log_error_limpiar_backups(error):
    logger_manager.error(f"Error en limpiar_backups_antiguos: {error}")
    