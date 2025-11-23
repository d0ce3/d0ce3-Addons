import os
import sys
import logging
from datetime import datetime

class LoggerManager:
    """Gestor centralizado de logging para todo el proyecto"""
    
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
        """Configura el logger principal"""
        self._logger = logging.getLogger('megacmd')
        self._logger.setLevel(logging.DEBUG)  # Captura TODO
        
        # Limpiar handlers existentes
        if self._logger.handlers:
            self._logger.handlers.clear()
        
        # Determinar ruta del log
        try:
            log_dir = os.path.join(os.getcwd(), 'addons')
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            self._log_file = os.path.join(log_dir, 'megacmd_full.log')
        except:
            self._log_file = 'megacmd_full.log'
        
        # Handler para archivo (siempre activo, guarda TODO)
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
        
        # Handler para consola (solo si debug está activado)
        self._console_handler = logging.StreamHandler()
        self._console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self._console_handler.setFormatter(console_formatter)
    
    def enable_debug(self):
        """Activa mensajes de debug en consola"""
        if not self._debug_enabled:
            self._debug_enabled = True
            if self._console_handler not in self._logger.handlers:
                self._logger.addHandler(self._console_handler)
            self._logger.info("Modo debug activado en consola")
    
    def disable_debug(self):
        """Desactiva mensajes de debug en consola"""
        if self._debug_enabled:
            self._debug_enabled = False
            if self._console_handler in self._logger.handlers:
                self._logger.removeHandler(self._console_handler)
            self._logger.info("Modo debug desactivado en consola")
    
    def is_debug_enabled(self):
        """Verifica si debug está activado"""
        return self._debug_enabled
    
    def get_log_file_path(self):
        """Devuelve la ruta del archivo de log"""
        return self._log_file
    
    def info(self, msg):
        """Log nivel INFO"""
        self._logger.info(msg)
    
    def warning(self, msg):
        """Log nivel WARNING"""
        self._logger.warning(msg)
    
    def error(self, msg):
        """Log nivel ERROR"""
        self._logger.error(msg)
    
    def debug(self, msg):
        """Log nivel DEBUG"""
        self._logger.debug(msg)
    
    def exception(self, msg):
        """Log con traceback completo"""
        self._logger.exception(msg)
    
    def download_logs(self, dest_path=None):
        """Prepara los logs para descarga"""
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
        """Limpia el archivo de logs"""
        try:
            if os.path.exists(self._log_file):
                with open(self._log_file, 'w') as f:
                    f.write('')
                self._logger.info("Logs limpiados")
                return True
        except Exception as e:
            self._logger.error(f"Error limpiando logs: {e}")
            return False

# Instancia global
logger_manager = LoggerManager()

# Accesos directos para compatibilidad
logger = logger_manager._logger
info = logger_manager.info
warning = logger_manager.warning
error = logger_manager.error
debug = logger_manager.debug
exception = logger_manager.exception


# ============================================================================
# FUNCIONES DE LOGGING SIMPLIFICADAS PARA BACKUPS
# ============================================================================

def log_backup_inicio():
    """Log de inicio de backup"""
    logger_manager.info("========== INICIO BACKUP ==========")

def log_backup_fin():
    """Log de fin de backup"""
    logger_manager.info("========== FIN BACKUP ==========")

def log_backup_auto_inicio():
    """Log de inicio de backup automático"""
    logger_manager.info("========== INICIO BACKUP AUTOMÁTICO ==========")

def log_backup_auto_fin():
    """Log de fin de backup automático"""
    logger_manager.info("========== FIN BACKUP AUTOMÁTICO ==========")

def log_config_carpeta(server_folder_config, base_dir, cwd, parent_dir, resolved, exists, destino):
    """Log detallado de configuración de carpetas"""
    logger_manager.info(f"Configuración - Carpeta config: {server_folder_config}")
    logger_manager.info(f"Configuración - BASE_DIR: {base_dir}")
    logger_manager.info(f"Configuración - os.getcwd(): {cwd}")
    logger_manager.info(f"Configuración - parent de BASE_DIR: {parent_dir}")
    logger_manager.info(f"Configuración - Carpeta resuelta: {resolved}")
    logger_manager.info(f"Configuración - ¿Existe? {exists}")
    logger_manager.info(f"Configuración - Destino: {destino}")

def log_carpeta_encontrada(ubicacion):
    """Log cuando se encuentra la carpeta del servidor"""
    logger_manager.info(f"Carpeta del servidor encontrada en: {ubicacion}")

def log_carpeta_no_encontrada(nombre_carpeta):
    """Log cuando no se encuentra la carpeta"""
    logger_manager.error(f"No se pudo encontrar la carpeta '{nombre_carpeta}'")

def log_tamano_carpeta(size_mb):
    """Log del tamaño de carpeta"""
    logger_manager.info(f"Tamaño de carpeta: {size_mb:.1f} MB")

def log_nombre_backup(backup_name):
    """Log del nombre del backup"""
    logger_manager.info(f"Nombre de backup: {backup_name}")

def log_compresion_inicio():
    """Log de inicio de compresión"""
    logger_manager.info("Iniciando compresión...")

def log_compresion_error():
    """Log de error en compresión"""
    logger_manager.error("Fallo en compresión")

def log_compresion_auto_error():
    """Log de error en compresión automática"""
    logger_manager.error("Error durante compresión automática")

def log_archivo_creado(backup_name, size_mb):
    """Log de archivo creado exitosamente"""
    logger_manager.info(f"Archivo creado: {backup_name} ({size_mb:.1f} MB)")

def log_archivo_no_encontrado(backup_name):
    """Log cuando no se encuentra el archivo"""
    logger_manager.error(f"Archivo {backup_name} no encontrado")

def log_subida_inicio():
    """Log de inicio de subida a MEGA"""
    logger_manager.info("Iniciando subida a MEGA...")

def log_subida_error():
    """Log de error en subida"""
    logger_manager.error("Fallo en subida a MEGA")

def log_subida_auto_error():
    """Log de error en subida automática"""
    logger_manager.error("Error al subir backup automático a MEGA")

def log_subida_exitosa(backup_folder, backup_name):
    """Log de subida exitosa"""
    logger_manager.info(f"Backup subido exitosamente a {backup_folder}/{backup_name}")

def log_subida_auto_exitosa(backup_folder, backup_name):
    """Log de subida automática exitosa"""
    logger_manager.info(f"Backup automático subido exitosamente: {backup_folder}/{backup_name}")

def log_archivo_local_eliminado():
    """Log de eliminación de archivo local"""
    logger_manager.info("Archivo local eliminado")

def log_archivo_local_error(error):
    """Log de error al eliminar archivo local"""
    logger_manager.warning(f"Error eliminando archivo local: {error}")

def log_backup_cancelado():
    """Log de backup cancelado por usuario"""
    logger_manager.info("Backup cancelado por usuario")

def log_carpeta_no_existe(carpeta):
    """Log cuando la carpeta no existe"""
    logger_manager.error(f"Carpeta {carpeta} no encontrada")

def log_carpeta_auto_no_existe(carpeta):
    """Log cuando la carpeta no existe en backup automático"""
    logger_manager.error(f"Carpeta {carpeta} no encontrada, se cancela backup automático")

def log_error_backup(error, traceback_str):
    """Log de error general en backup"""
    logger_manager.error(f"Error en crear_backup: {error}")
    logger_manager.error(traceback_str)

def log_error_backup_auto(error, traceback_str):
    """Log de error en backup automático"""
    logger_manager.error(f"Error en backup automático: {error}")
    logger_manager.error(traceback_str)

def log_autobackup_desactivado():
    """Log cuando autobackup está desactivado"""
    logger_manager.info("Autobackup desactivado, no se ejecutará")

def log_autobackup_habilitado():
    """Log cuando se habilita autobackup"""
    logger_manager.info("Autobackup habilitado")

def log_autobackup_deshabilitado():
    """Log cuando se deshabilita autobackup"""
    logger_manager.info("Autobackup deshabilitado")

def log_timer_activo(pid):
    """Log cuando el timer ya está activo"""
    logger_manager.info(f"Timer de autobackup ya activo en proceso - omitiendo (PID actual: {pid})")

def log_timer_local_activo():
    """Log cuando el timer local está activo"""
    logger_manager.info("Timer local de autobackup ya activo, no se crea uno nuevo")

def log_timer_programado(interval_minutes, pid):
    """Log cuando se programa un nuevo timer"""
    logger_manager.info(f"Nuevo timer programado para {interval_minutes} minutos (PID: {pid})")
    logger_manager.info(f"Autobackup activado - cada {interval_minutes} minutos")

def log_timer_detenido():
    """Log cuando se detiene el timer"""
    logger_manager.info("Timer de autobackup detenido")

def log_rcon_error_inicio(error):
    """Log cuando falla el mensaje RCON de inicio"""
    logger_manager.warning(f"No se pudo enviar mensaje RCON de inicio: {error}")

def log_rcon_error_fin(error):
    """Log cuando falla el mensaje RCON de fin"""
    logger_manager.warning(f"No se pudo enviar mensaje RCON de fin: {error}")

def log_limpiar_backups(max_backups):
    """Log de inicio de limpieza de backups"""
    logger_manager.info(f"Limpiando backups antiguos (mantener {max_backups})...")

def log_backups_encontrados(cantidad):
    """Log de cantidad de backups encontrados"""
    logger_manager.info(f"Backups encontrados: {cantidad}")

def log_backup_eliminado(archivo):
    """Log de backup eliminado"""
    logger_manager.info(f"Eliminado: {archivo}")

def log_error_eliminar_backup(archivo):
    """Log de error al eliminar backup"""
    logger_manager.warning(f"Error eliminando {archivo}")

def log_limpieza_completada(cantidad):
    """Log de limpieza completada"""
    logger_manager.info(f"Limpieza completada - {cantidad} backups eliminados")

def log_menu_autobackup():
    """Log de menú de configuración"""
    logger_manager.info("========== MENÚ CONFIGURAR AUTOBACKUP ==========")

def log_autobackup_activado_usuario():
    """Log cuando el usuario activa autobackup"""
    logger_manager.info("Autobackup activado por usuario")

def log_autobackup_desactivado_usuario():
    """Log cuando el usuario desactiva autobackup"""
    logger_manager.info("Autobackup desactivado por usuario")

def log_intervalo_cambiado(minutos):
    """Log de cambio de intervalo"""
    logger_manager.info(f"Intervalo cambiado a {minutos} minutos")

def log_destino_cambiado(destino):
    """Log de cambio de destino MEGA"""
    logger_manager.info(f"Destino MEGA cambiado a: {destino}")

def log_max_backups_cambiado(cantidad):
    """Log de cambio de máximo de backups"""
    logger_manager.info(f"Máximo de backups cambiado a {cantidad}")

def log_salir_config():
    """Log al salir de configuración"""
    logger_manager.info("Saliendo de configuración de autobackup")

def log_autobackup_verificando():
    """Log al verificar timer"""
    logger_manager.info("Autobackup está habilitado, verificando timer...")

def log_timer_no_activo():
    """Log cuando no hay timer activo"""
    logger_manager.info("No hay timer activo, iniciando autobackup...")

def log_timer_otro_proceso():
    """Log cuando hay timer en otro proceso"""
    logger_manager.info("Timer ya activo en otro proceso, no se inicia uno nuevo")

def log_autobackup_no_habilitado():
    """Log cuando autobackup no está habilitado"""
    logger_manager.info("Autobackup no está habilitado")

def log_error_listando_backups(error):
    """Log de error al listar backups"""
    logger_manager.error(f"Error listando backups: {error}")

def log_error_limpiar_backups(error):
    """Log de error en limpieza de backups"""
    logger_manager.error(f"Error en limpiar_backups_antiguos: {error}")