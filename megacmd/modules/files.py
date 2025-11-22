"""
Módulo de gestión de archivos MEGA para MegaCMD Manager
"""

import os
import subprocess
from datetime import datetime

# Cargar dependencias
config = CloudModuleLoader.load_module("config")
utils = CloudModuleLoader.load_module("utils")
megacmd = CloudModuleLoader.load_module("megacmd")
backup = CloudModuleLoader.load_module("backup")

# Verificar que utils cargó correctamente
if not utils:
    import logging
    logger = logging.getLogger('megacmd')
    
    class TempUtils:
        logger = logger
        
        @staticmethod
        def print_msg(msg, icono="✓"):
            print(f"{icono} ⎹ {msg}")
        
        @staticmethod
        def print_error(msg):
            print(f"✖ ⎹ {msg}")
        
        @staticmethod
        def print_warning(msg):
            print(f"⚠ ⎹ {msg}")
        
        @staticmethod
        def Spinner(msg):
            class DummySpinner:
                def __init__(self, mensaje):
                    self.mensaje = mensaje
                def start(self, proceso, check_file=None):
                    proceso.wait()
                    return True
            return DummySpinner(msg)
        
        @staticmethod
        def limpiar_pantalla():
            os.system('clear')
        
        @staticmethod
        def pausar():
            input("\n[+] Enter para continuar...")
        
        @staticmethod
        def confirmar(msg):
            return input(f"{msg} (s/n): ").strip().lower() == 's'
        
        @staticmethod
        def formato_bytes(b):
            for u in ['B', 'KB', 'MB', 'GB']:
                if b < 1024:
                    return f"{b:.1f} {u}"
                b /= 1024
            return f"{b:.1f} TB"
    
    utils = TempUtils()

# ============================================
# LISTAR Y DESCARGAR
# ============================================

def listar_y_descargar():
    """Lista archivos en MEGA y permite descargar"""
    
    utils.limpiar_pantalla()
    
    print("\n" + "="*60)
    print("LISTAR Y DESCARGAR DE MEGA")
    print("="*60 + "\n")
    
    utils.logger.info("Listando archivos en MEGA")
    
    try:
        # Verificar MegaCMD
        if not megacmd.verificar_megacmd():
            utils.print_error("MegaCMD no está disponible")
            utils.pausar()
            return
        
        backup_folder = config.CONFIG.get("backup_folder", "/backups")
        
        # Listar archivos
        print(f"📁 Listando archivos en: {backup_folder}\n")
        
        cmd = ["mega-ls", "-l", backup_folder]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            utils.print_error("No se pudo listar archivos")
            utils.logger.error(f"Error listando MEGA: {result.stderr}")
            utils.pausar()
            return
        
        # Parsear archivos
        lineas = result.stdout.strip().split('\n')
        archivos = []
        
        for linea in lineas:
            if '.zip' in linea:
                partes = linea.split()
                if len(partes) >= 2:
                    nombre = partes[-1]
                    # Intentar obtener tamaño
                    try:
                        size_str = partes[0]
                        archivos.append({
                            'nombre': nombre,
                            'size_str': size_str
                        })
                    except:
                        archivos.append({
                            'nombre': nombre,
                            'size_str': 'N/A'
                        })
        
        if not archivos:
            utils.print_warning("No hay archivos ZIP en MEGA")
            utils.pausar()
            return
        
        # Mostrar archivos
        print("Archivos disponibles:\n")
        for idx, archivo in enumerate(archivos, 1):
            print(f"{idx}. {archivo['nombre']} ({archivo['size_str']})")
        
        print(f"\n{len(archivos)} archivos encontrados\n")
        
        # Seleccionar archivo
        try:
            seleccion = input("Número de archivo a descargar (0 para cancelar): ").strip()
            
            if seleccion == '0':
                print("Cancelado")
                utils.pausar()
                return
            
            idx = int(seleccion) - 1
            
            if idx < 0 or idx >= len(archivos):
                utils.print_error("Número inválido")
                utils.pausar()
                return
            
            archivo_seleccionado = archivos[idx]['nombre']
            
            print(f"\n📥 Descargando: {archivo_seleccionado}")
            
            # Descargar
            cmd_get = ["mega-get", f"{backup_folder}/{archivo_seleccionado}", "."]
            proceso = subprocess.Popen(cmd_get, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            spinner = utils.Spinner("Descargando")
            if not spinner.start(proceso):
                utils.print_error("Error al descargar")
                utils.logger.error(f"Error descargando {archivo_seleccionado}")
                utils.pausar()
                return
            
            utils.print_msg(f"Descargado: {archivo_seleccionado}")
            utils.logger.info(f"Archivo descargado: {archivo_seleccionado}")
            
            # Preguntar si descomprimir
            print()
            if utils.confirmar("¿Descomprimir ahora?"):
                descomprimir_backup(archivo_seleccionado)
        
        except ValueError:
            utils.print_error("Entrada inválida")
    
    except Exception as e:
        utils.print_error(f"Error: {e}")
        utils.logger.error(f"Error en listar_y_descargar: {e}")
    
    utils.pausar()

# ============================================
# GESTIONAR BACKUPS
# ============================================

def gestionar_backups():
    """Gestiona y limpia backups en MEGA"""
    
    utils.limpiar_pantalla()
    
    print("\n" + "="*60)
    print("GESTIONAR BACKUPS EN MEGA")
    print("="*60 + "\n")
    
    utils.logger.info("Gestionando backups")
    
    try:
        # Verificar MegaCMD
        if not megacmd.verificar_megacmd():
            utils.print_error("MegaCMD no está disponible")
            utils.pausar()
            return
        
        backup_folder = config.CONFIG.get("backup_folder", "/backups")
        backup_prefix = config.CONFIG.get("backup_prefix", "MSX")
        
        # Listar backups
        print(f"📁 Listando backups en: {backup_folder}\n")
        
        cmd = ["mega-ls", backup_folder]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            utils.print_error("No se pudo listar backups")
            utils.pausar()
            return
        
        # Filtrar backups
        archivos = [line.strip() for line in result.stdout.split('\n') if backup_prefix in line and '.zip' in line]
        archivos.sort(reverse=True)
        
        if not archivos:
            utils.print_warning("No hay backups en MEGA")
            utils.pausar()
            return
        
        print(f"Backups encontrados: {len(archivos)}\n")
        
        for idx, archivo in enumerate(archivos, 1):
            print(f"{idx}. {archivo}")
        
        print(f"\nOpciones:")
        print("1. Eliminar backup específico")
        print("2. Limpiar backups antiguos")
        print("3. Ver información de cuenta")
        print("4. Volver\n")
        
        opcion = input("Seleccioná una opción: ").strip()
        
        if opcion == "1":
            # Eliminar específico
            try:
                num = int(input("\nNúmero de backup a eliminar (0 para cancelar): ").strip())
                
                if num == 0:
                    print("Cancelado")
                    utils.pausar()
                    return
                
                if num < 1 or num > len(archivos):
                    utils.print_error("Número inválido")
                    utils.pausar()
                    return
                
                archivo_eliminar = archivos[num - 1]
                
                if utils.confirmar(f"¿Eliminar {archivo_eliminar}?"):
                    cmd_rm = ["mega-rm", f"{backup_folder}/{archivo_eliminar}"]
                    result_rm = subprocess.run(cmd_rm, capture_output=True, text=True)
                    
                    if result_rm.returncode == 0:
                        utils.print_msg(f"Eliminado: {archivo_eliminar}")
                        utils.logger.info(f"Backup eliminado: {archivo_eliminar}")
                    else:
                        utils.print_error("Error al eliminar")
                        utils.logger.error(f"Error eliminando {archivo_eliminar}")
                else:
                    print("Cancelado")
            
            except ValueError:
                utils.print_error("Entrada inválida")
        
        elif opcion == "2":
            # Limpiar antiguos
            if backup:
                backup.limpiar_backups_antiguos()
            else:
                utils.print_error("Módulo backup no disponible")
        
        elif opcion == "3":
            # Info cuenta
            info_cuenta()
            return
    
    except Exception as e:
        utils.print_error(f"Error: {e}")
        utils.logger.error(f"Error en gestionar_backups: {e}")
    
    utils.pausar()

# ============================================
# SUBIR ARCHIVO
# ============================================

def subir_archivo():
    """Sube un archivo a MEGA"""
    
    utils.limpiar_pantalla()
    
    print("\n" + "="*60)
    print("SUBIR ARCHIVO A MEGA")
    print("="*60 + "\n")
    
    utils.logger.info("Subiendo archivo a MEGA")
    
    try:
        # Verificar MegaCMD
        if not megacmd.verificar_megacmd():
            utils.print_error("MegaCMD no está disponible")
            utils.pausar()
            return
        
        # Pedir ruta del archivo
        archivo = input("Ruta del archivo a subir: ").strip()
        
        if not archivo:
            print("Cancelado")
            utils.pausar()
            return
        
        if not os.path.exists(archivo):
            utils.print_error(f"Archivo no encontrado: {archivo}")
            utils.pausar()
            return
        
        # Verificar que es un archivo
        if not os.path.isfile(archivo):
            utils.print_error("La ruta debe ser un archivo, no un directorio")
            utils.pausar()
            return
        
        # Tamaño
        size = os.path.getsize(archivo)
        size_mb = size / (1024 * 1024)
        
        print(f"\n📄 Archivo: {os.path.basename(archivo)}")
        print(f"📦 Tamaño: {size_mb:.1f} MB")
        
        # Destino
        backup_folder = config.CONFIG.get("backup_folder", "/backups")
        print(f"📁 Destino: {backup_folder}\n")
        
        if not utils.confirmar("¿Subir archivo?"):
            print("Cancelado")
            utils.pausar()
            return
        
        print()
        
        # Subir
        cmd_put = ["mega-put", archivo, backup_folder]
        proceso = subprocess.Popen(cmd_put, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        spinner = utils.Spinner("Subiendo")
        if not spinner.start(proceso):
            utils.print_error("Error al subir archivo")
            utils.logger.error(f"Error subiendo {archivo}")
            utils.pausar()
            return
        
        utils.print_msg(f"Archivo subido: {os.path.basename(archivo)}")
        utils.logger.info(f"Archivo subido: {archivo} -> {backup_folder}")
    
    except Exception as e:
        utils.print_error(f"Error: {e}")
        utils.logger.error(f"Error en subir_archivo: {e}")
    
    utils.pausar()

# ============================================
# INFORMACIÓN DE CUENTA
# ============================================

def info_cuenta():
    """Muestra información de la cuenta MEGA"""
    
    utils.limpiar_pantalla()
    
    print("\n" + "="*60)
    print("INFORMACIÓN DE CUENTA MEGA")
    print("="*60 + "\n")
    
    try:
        # Verificar MegaCMD
        if not megacmd.verificar_megacmd():
            utils.print_error("MegaCMD no está disponible")
            utils.pausar()
            return
        
        # Whoami
        cmd_whoami = ["mega-whoami"]
        result_whoami = subprocess.run(cmd_whoami, capture_output=True, text=True)
        
        if result_whoami.returncode == 0:
            email = result_whoami.stdout.strip()
            print(f"📧 Usuario: {email}\n")
        
        # Quota
        cmd_quota = ["mega-df", "-h"]
        result_quota = subprocess.run(cmd_quota, capture_output=True, text=True)
        
        if result_quota.returncode == 0:
            print("💾 Espacio en cuenta:\n")
            print(result_quota.stdout)
        
        # Backups en carpeta
        backup_folder = config.CONFIG.get("backup_folder", "/backups")
        
        print(f"\n📁 Backups en {backup_folder}:")
        
        cmd_ls = ["mega-ls", backup_folder]
        result_ls = subprocess.run(cmd_ls, capture_output=True, text=True)
        
        if result_ls.returncode == 0:
            archivos = [line for line in result_ls.stdout.split('\n') if '.zip' in line]
            print(f"   {len(archivos)} backups almacenados")
    
    except Exception as e:
        utils.print_error(f"Error: {e}")
        utils.logger.error(f"Error en info_cuenta: {e}")
    
    utils.pausar()

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def descomprimir_backup(archivo):
    """Descomprime un backup descargado"""
    
    try:
        if not os.path.exists(archivo):
            utils.print_error(f"Archivo no encontrado: {archivo}")
            return
        
        server_folder = config.CONFIG.get("server_folder", "servidor_minecraft")
        
        print(f"\n📦 Descomprimiendo: {archivo}")
        print(f"📁 Destino: {server_folder}")
        
        # Backup de carpeta actual si existe
        if os.path.exists(server_folder):
            if not utils.confirmar(f"\n⚠️  La carpeta {server_folder} será reemplazada. ¿Continuar?"):
                print("Cancelado")
                return
            
            import shutil
            backup_old = f"{server_folder}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"\n💾 Respaldando carpeta actual a: {backup_old}")
            shutil.move(server_folder, backup_old)
        
        print()
        
        # Descomprimir
        cmd_unzip = ["unzip", "-q", "-o", archivo]
        proceso = subprocess.Popen(cmd_unzip)
        
        spinner = utils.Spinner("Descomprimiendo")
        if not spinner.start(proceso):
            utils.print_error("Error al descomprimir")
            return
        
        utils.print_msg("Descompresión completada")
        utils.logger.info(f"Backup descomprimido: {archivo}")
        
        # Limpiar ZIP
        if utils.confirmar("\n¿Eliminar archivo ZIP?"):
            os.remove(archivo)
            utils.print_msg(f"Eliminado: {archivo}")
    
    except Exception as e:
        utils.print_error(f"Error descomprimiendo: {e}")
        utils.logger.error(f"Error en descomprimir_backup: {e}")
