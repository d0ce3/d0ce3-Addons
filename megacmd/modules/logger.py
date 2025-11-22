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