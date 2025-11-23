import os
import subprocess
from datetime import datetime


config = CloudModuleLoader.load_module("config")
utils = CloudModuleLoader.load_module("utils")
backup = CloudModuleLoader.load_module("backup")
autobackup = CloudModuleLoader.load_module("autobackup")

# Cargar el nuevo módulo de menús
try:
    menu = CloudModuleLoader.load_module("menu")
    
    # Crear instancias de los menús
    menu_archivos = menu.MenuArchivos(config, utils, backup, autobackup)
    
    # Funciones wrapper para compatibilidad con código existente
    def listar_y_descargar():
        """Wrapper para compatibilidad - llama al menú correspondiente"""
        menu_archivos.listar_y_descargar()
    
    def gestionar_backups():
        """Wrapper para compatibilidad - llama al menú correspondiente"""
        menu_archivos.gestionar_backups()
    
    def subir_archivo():
        """Wrapper para compatibilidad - llama al menú correspondiente"""
        menu_archivos.subir_archivo()
    
    def info_cuenta():
        """Wrapper para compatibilidad - llama al menú correspondiente"""
        menu_archivos.info_cuenta()
    
    def descomprimir_backup(archivo):
        """Wrapper para compatibilidad - llama al método correspondiente"""
        menu_archivos._descomprimir_backup(archivo)

except Exception as e:
    utils.logger.error(f"Error cargando módulo menu: {e}")
    
    # Fallback: si el módulo menu no está disponible, crear funciones básicas
    def listar_y_descargar():
        utils.print_error("Módulo de menús no disponible")
        utils.pausar()
    
    def gestionar_backups():
        utils.print_error("Módulo de menús no disponible")
        utils.pausar()
    
    def subir_archivo():
        utils.print_error("Módulo de menús no disponible")
        utils.pausar()
    
    def info_cuenta():
        utils.print_error("Módulo de menús no disponible")
        utils.pausar()
    
    def descomprimir_backup(archivo):
        utils.print_error("Módulo de menús no disponible")
        utils.pausar()
