"""
Módulo de Menús e Interfaz de Usuario
Sistema centralizado de menús para MegaCMD Backup Tool
"""

import os
import subprocess
from datetime import datetime

# ============================================================
# CONFIGURACIÓN VISUAL
# ============================================================

class Tema:
    """Configuración visual centralizada"""
    
    # Símbolos
    CHECK = "✓"
    ERROR = "✖"
    WARNING = "⚠"
    INFO = "ℹ"
    FOLDER = "📁"
    FILE = "📄"
    PACKAGE = "📦"
    CLOUD = "☁️"
    TIMER = "⏱️"
    EMAIL = "📧"
    DISK = "💾"
    ARROW = "➥"
    BULLET = "•"
    
    # Separadores
    LINE_FULL = "=" * 60
    LINE_LIGHT = "-" * 60
    
    # Colores (ANSI) - opcionales
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    
    @staticmethod
    def usar_colores():
        """Detecta si la terminal soporta colores"""
        return os.getenv("TERM") not in ["dumb", None]


# ============================================================
# COMPONENTES BASE DE UI
# ============================================================

class Display:
    """Gestiona la visualización y formato de mensajes"""
    
    @staticmethod
    def header(titulo):
        """Muestra un encabezado de sección"""
        print("\n" + Tema.LINE_FULL)
        print(titulo.upper())
        print(Tema.LINE_FULL + "\n")
    
    @staticmethod
    def subheader(titulo):
        """Muestra un subencabezado"""
        print("\n" + Tema.LINE_LIGHT)
        print(titulo)
        print(Tema.LINE_LIGHT)
    
    @staticmethod
    def msg(mensaje, icono=None):
        """Mensaje de éxito"""
        icono = icono or Tema.CHECK
        print(f"{icono} ⎹ {mensaje}")
    
    @staticmethod
    def error(mensaje, icono=None):
        """Mensaje de error"""
        icono = icono or Tema.ERROR
        print(f"{icono} ⎹ {mensaje}")
    
    @staticmethod
    def warning(mensaje, icono=None):
        """Mensaje de advertencia"""
        icono = icono or Tema.WARNING
        print(f"{icono} ⎹ {mensaje}")
    
    @staticmethod
    def info(mensaje, icono=None):
        """Mensaje informativo"""
        icono = icono or Tema.INFO
        print(f"{icono} ⎹ {mensaje}")
    
    @staticmethod
    def lista_opciones(opciones):
        """Muestra una lista numerada de opciones"""
        print("\nOPCIONES:")
        for i, opcion in enumerate(opciones, 1):
            print(f" {i}. {opcion}")
        print()
    
    @staticmethod
    def lista_archivos(archivos, mostrar_indice=True):
        """Muestra una lista de archivos con formato"""
        for idx, archivo in enumerate(archivos, 1):
            if isinstance(archivo, dict):
                nombre = archivo.get('nombre', archivo.get('name', 'N/A'))
                size = archivo.get('size_str', archivo.get('size', ''))
                if size:
                    print(f" {idx}. {nombre} ({size})")
                else:
                    print(f" {idx}. {nombre}")
            else:
                print(f" {idx}. {archivo}")
    
    @staticmethod
    def clear():
        """Limpia la pantalla"""
        os.system('clear' if os.name != 'nt' else 'cls')


class InputHandler:
    """Gestiona la entrada de datos del usuario"""
    
    @staticmethod
    def confirmar(mensaje):
        """Solicita confirmación del usuario"""
        respuesta = input(f"{mensaje} (s/n): ").strip().lower()
        return respuesta in ['s', 'si', 'y', 'yes']
    
    @staticmethod
    def seleccionar_numero(mensaje, min_val=0, max_val=None):
        """Solicita un número dentro de un rango"""
        while True:
            try:
                valor = input(f"{mensaje}: ").strip()
                if not valor:
                    return None
                
                numero = int(valor)
                if max_val is not None:
                    if min_val <= numero <= max_val:
                        return numero
                    else:
                        Display.warning(f"Número debe estar entre {min_val} y {max_val}")
                elif numero >= min_val:
                    return numero
                else:
                    Display.warning(f"Número debe ser mayor o igual a {min_val}")
            except ValueError:
                Display.warning("Ingrese un número válido")
            except KeyboardInterrupt:
                print("\nCancelado")
                return None
    
    @staticmethod
    def seleccionar_opcion(mensaje, opciones):
        """Solicita seleccionar una opción de una lista"""
        print(f"\n{mensaje}")
        Display.lista_opciones(opciones)
        return InputHandler.seleccionar_numero(
            "Seleccione una opción", 
            min_val=0, 
            max_val=len(opciones)
        )
    
    @staticmethod
    def input_texto(mensaje, requerido=True):
        """Solicita entrada de texto"""
        while True:
            valor = input(f"{mensaje}: ").strip()
            if valor or not requerido:
                return valor
            Display.warning("Este campo es requerido")
    
    @staticmethod
    def pausar():
        """Pausa la ejecución esperando Enter"""
        input("\n[+] Enter para continuar...")


# ============================================================
# MENÚS PRINCIPALES
# ============================================================

class MenuBackup:
    """Menús relacionados con backups"""
    
    def __init__(self, config, utils, backup, autobackup):
        self.config = config
        self.utils = utils
        self.backup = backup
        self.autobackup = autobackup
    
    def crear_backup_manual(self):
        """Menú para crear backup manual"""
        Display.clear()
        Display.header("CREAR BACKUP EN MEGA")
        
        try:
            self._ejecutar_backup_manual()
        except Exception as e:
            Display.error(f"Error creando backup: {e}")
            self.utils.logger.error(f"Error en crear_backup: {e}")
            import traceback
            self.utils.logger.error(traceback.format_exc())
        
        InputHandler.pausar()
    
    def _ejecutar_backup_manual(self):
        """Lógica de ejecución de backup manual"""
        self.utils.logger.info("========== INICIO BACKUP MANUAL ==========")
        
        if not self.utils.verificar_megacmd():
            Display.error("MegaCMD no está disponible")
            InputHandler.pausar()
            return
        
        # Obtener configuración
        server_folder_config = self.config.CONFIG.get("server_folder", "servidor_minecraft")
        server_folder = self.backup.encontrar_carpeta_servidor(server_folder_config)
        backup_folder = self.config.CONFIG.get("backup_folder", "/backups")
        backup_prefix = self.config.CONFIG.get("backup_prefix", "MSX")
        
        if not server_folder or not os.path.exists(server_folder):
            Display.error(f"La carpeta {server_folder_config} no se pudo encontrar")
            self.utils.logger.error(f"Carpeta {server_folder_config} no encontrada")
            InputHandler.pausar()
            return
        
        print(f"{Tema.FOLDER} Carpeta: {server_folder}")
        print(f"{Tema.PACKAGE} Calculando tamaño...")
        
        # Calcular tamaño
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(server_folder):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except:
                    pass
        
        size_mb = total_size / (1024 * 1024)
        print(f"{Tema.PACKAGE} Tamaño total: {size_mb:.1f} MB\n")
        
        if not InputHandler.confirmar("¿Crear backup ahora?"):
            print("Cancelado")
            return
        
        print()
        
        # Ejecutar backup
        timestamp = datetime.now(self.backup.TIMEZONE_ARG).strftime("%d-%m-%Y_%H-%M")
        backup_name = f"{backup_prefix}_{timestamp}.zip"
        
        # Comprimir
        cmd = ["zip", "-r", "-q", backup_name, server_folder]
        proceso = subprocess.Popen(cmd)
        
        spinner = self.utils.Spinner("Comprimiendo")
        if not spinner.start(proceso, check_file=backup_name):
            Display.error("Error al comprimir")
            InputHandler.pausar()
            return
        
        if not os.path.exists(backup_name):
            Display.error("El archivo ZIP no se creó")
            InputHandler.pausar()
            return
        
        backup_size_mb = os.path.getsize(backup_name) / (1024 * 1024)
        print(f"\n{Tema.CHECK} Archivo creado: {backup_name} ({backup_size_mb:.1f} MB)\n")
        
        # Subir a MEGA
        cmd_upload = ["mega-put", backup_name, backup_folder]
        proceso_upload = subprocess.Popen(cmd_upload, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        spinner_upload = self.utils.Spinner("Subiendo a MEGA")
        if not spinner_upload.start(proceso_upload):
            Display.error("Error al subir a MEGA")
            try:
                os.remove(backup_name)
            except:
                pass
            InputHandler.pausar()
            return
        
        # Limpiar archivo local
        try:
            os.remove(backup_name)
        except Exception as e:
            Display.warning(f"No se pudo eliminar archivo local: {e}")
        
        print()
        Display.msg(f"Backup creado exitosamente: {backup_name}")
        self.utils.logger.info("========== FIN BACKUP MANUAL ==========")
        
        print()
        if InputHandler.confirmar("¿Limpiar backups antiguos ahora?"):
            self.backup.limpiar_backups_antiguos()
    
    def configurar_autobackup(self):
        """Menú de configuración de autobackup"""
        if not self.utils.verificar_megacmd():
            Display.error("MegaCMD no está disponible")
            InputHandler.pausar()
            return
        
        while True:
            Display.clear()
            Display.header("CONFIGURAR AUTOBACKUP")
            
            # Obtener configuración actual
            autobackup_enabled = self.config.CONFIG.get("autobackup_enabled", False)
            intervalo_actual = self.config.CONFIG.get("backup_interval_minutes", 5)
            backup_folder = self.config.CONFIG.get("backup_folder", "/backups")
            server_folder = self.config.CONFIG.get("server_folder", "servidor_minecraft")
            max_backups = self.config.CONFIG.get("max_backups", 5)
            
            # Mostrar configuración actual
            print("📋 CONFIGURACIÓN ACTUAL:")
            estado = f"{Tema.CHECK} ACTIVADO" if autobackup_enabled else f"{Tema.ERROR} DESACTIVADO"
            print(f" Estado: {estado}")
            print(f" Intervalo: cada {intervalo_actual} minutos")
            print(f" Carpeta servidor: {server_folder}")
            print(f" Destino MEGA: {backup_folder}")
            print(f" Máximo backups: {max_backups}")
            print()
            
            # Menú de opciones
            opciones = []
            if autobackup_enabled:
                opciones.append("Desactivar autobackup")
            else:
                opciones.append("Activar autobackup")
            
            opciones.extend([
                "Cambiar intervalo de autobackup",
                "Cambiar ruta de guardado",
                "Cambiar backups máximos",
                "Volver"
            ])
            
            opcion = InputHandler.seleccionar_opcion("Seleccione una opción", opciones)
            
            if opcion is None or opcion == len(opciones):
                break
            elif opcion == 1:
                self._toggle_autobackup(autobackup_enabled)
            elif opcion == 2:
                self._cambiar_intervalo(intervalo_actual)
            elif opcion == 3:
                self._cambiar_ruta_guardado(backup_folder)
            elif opcion == 4:
                self._cambiar_max_backups(max_backups)
    
    def _toggle_autobackup(self, estado_actual):
        """Activa/desactiva el autobackup"""
        if estado_actual:
            self.config.set("autobackup_enabled", False)
            Display.msg("Autobackup desactivado")
            self.utils.logger.info("Autobackup desactivado por usuario")
        else:
            self.config.set("autobackup_enabled", True)
            Display.msg("Autobackup activado")
            self.utils.logger.info("Autobackup activado por usuario")
        
        print("\n⚠️ Nota: Reinicie el proceso de autobackup para aplicar los cambios")
        InputHandler.pausar()
    
    def _cambiar_intervalo(self, intervalo_actual):
        """Cambia el intervalo de autobackup"""
        print(f"\n{Tema.TIMER} Intervalo actual: {intervalo_actual} minutos")
        nuevo_intervalo = InputHandler.seleccionar_numero(
            "Nuevo intervalo en minutos (1-60)",
            min_val=1,
            max_val=60
        )
        
        if nuevo_intervalo:
            self.config.set("backup_interval_minutes", nuevo_intervalo)
            Display.msg(f"Intervalo cambiado a {nuevo_intervalo} minutos")
            self.utils.logger.info(f"Intervalo cambiado a {nuevo_intervalo} minutos")
        
        InputHandler.pausar()
    
    def _cambiar_ruta_guardado(self, backup_folder):
        """Cambia la ruta de guardado en MEGA"""
        print(f"\n{Tema.CLOUD} Destino MEGA actual: {backup_folder}\n")
        
        opciones = [
            "Navegar por MEGA",
            "Escribir ruta manualmente",
            "Cancelar"
        ]
        
        opcion = InputHandler.seleccionar_opcion("¿Cómo desea seleccionar la carpeta destino?", opciones)
        
        if opcion == 1:
            print(f"\n🔍 Cargando carpetas MEGA...")
            nueva_ruta = self.backup.navegar_carpetas_mega(backup_folder)
            if nueva_ruta:
                self.config.set("backup_folder", nueva_ruta)
                Display.msg(f"Carpeta cambiada a: {nueva_ruta}")
                self.utils.logger.info(f"Destino MEGA cambiado a: {nueva_ruta}")
            else:
                print("Navegación cancelada")
        elif opcion == 2:
            nuevo_destino = InputHandler.input_texto("Nueva carpeta MEGA (ej: /backups)", requerido=False)
            if nuevo_destino:
                if not nuevo_destino.startswith("/"):
                    nuevo_destino = "/" + nuevo_destino
                self.config.set("backup_folder", nuevo_destino)
                Display.msg(f"Carpeta cambiada a: {nuevo_destino}")
                self.utils.logger.info(f"Destino MEGA cambiado a: {nuevo_destino}")
        
        InputHandler.pausar()
    
    def _cambiar_max_backups(self, max_actual):
        """Cambia el número máximo de backups"""
        print(f"\n{Tema.FOLDER} Máximo de backups actual: {max_actual}")
        print("💡 Recomendado: 5 backups")
        
        nuevo_max = InputHandler.seleccionar_numero(
            "Nueva cantidad máxima (1-10)",
            min_val=1,
            max_val=10
        )
        
        if nuevo_max:
            self.config.set("max_backups", nuevo_max)
            Display.msg(f"Máximo de backups cambiado a {nuevo_max}")
            self.utils.logger.info(f"Máximo de backups cambiado a {nuevo_max}")
        
        InputHandler.pausar()


class MenuArchivos:
    """Menús relacionados con gestión de archivos"""
    
    def __init__(self, config, utils, backup, autobackup):
        self.config = config
        self.utils = utils
        self.backup = backup
        self.autobackup = autobackup
    
    def _pause_autobackup(self):
        """Pausa el autobackup temporalmente"""
        if self.autobackup.is_enabled():
            self.autobackup.stop_autobackup()
            return True
        return False
    
    def _resume_autobackup(self, was_enabled):
        """Reanuda el autobackup si estaba habilitado"""
        if was_enabled:
            self.autobackup.start_autobackup()
    
    def listar_y_descargar(self):
        """Menú para listar y descargar archivos de MEGA"""
        was_enabled = self._pause_autobackup()
        
        try:
            Display.clear()
            Display.header("LISTAR Y DESCARGAR DE MEGA")
            
            if not self.utils.verificar_megacmd():
                Display.error("MegaCMD no está disponible")
                InputHandler.pausar()
                return
            
            print(f"{Tema.FOLDER} Listar carpetas en MEGA raíz:\n")
            
            # Listar carpetas
            cmd_ls_root = ["mega-ls", "-l"]
            result_root = subprocess.run(cmd_ls_root, capture_output=True, text=True)
            
            if result_root.returncode != 0:
                Display.error("No se pudo listar la raíz en MEGA")
                InputHandler.pausar()
                return
            
            carpetas = []
            for line in result_root.stdout.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 2 and parts[0].startswith('d'):
                    nombre = parts[-1]
                    carpetas.append(nombre)
            
            if not carpetas:
                carpetas = [self.config.CONFIG.get("backup_folder", "/backups")]
            
            print("Carpetas disponibles:")
            Display.lista_archivos(carpetas)
            
            opcion = input("\nElegí carpeta para listar archivos (0 para raiz): ").strip()
            
            if opcion == '0':
                ruta = "/"
            else:
                try:
                    idx_sel = int(opcion) - 1
                    if 0 <= idx_sel < len(carpetas):
                        ruta = "/" + carpetas[idx_sel]
                    else:
                        ruta = "/"
                except:
                    ruta = "/"
            
            print(f"\nListando archivos en: {ruta}\n")
            
            # Listar archivos
            cmd_ls = ["mega-ls", "-l", ruta]
            result = subprocess.run(cmd_ls, capture_output=True, text=True)
            
            if result.returncode != 0:
                Display.error("No se pudo listar archivos")
                InputHandler.pausar()
                return
            
            archivos = []
            for linea in result.stdout.strip().split('\n'):
                if '.zip' in linea:
                    partes = linea.split()
                    if len(partes) >= 2:
                        nombre = partes[-1]
                        try:
                            size_str = partes[0]
                            archivos.append({'nombre': nombre, 'size_str': size_str})
                        except:
                            archivos.append({'nombre': nombre, 'size_str': 'N/A'})
            
            if not archivos:
                Display.warning("No hay archivos ZIP en MEGA")
                InputHandler.pausar()
                return
            
            print("Archivos disponibles:\n")
            Display.lista_archivos(archivos)
            
            seleccion = InputHandler.seleccionar_numero(
                "\nNúmero de archivo a descargar (0 para cancelar)",
                min_val=0,
                max_val=len(archivos)
            )
            
            if seleccion == 0 or seleccion is None:
                print("Cancelado")
                InputHandler.pausar()
                return
            
            archivo_seleccionado = archivos[seleccion - 1]['nombre']
            print(f"\n📥 Descargando: {archivo_seleccionado}")
            
            full_ruta = f"{ruta}/{archivo_seleccionado}".replace('//', '/')
            cmd_get = ["mega-get", full_ruta, "."]
            proceso = subprocess.Popen(cmd_get, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            spinner = self.utils.Spinner("Descargando")
            if not spinner.start(proceso):
                Display.error("Error al descargar")
                InputHandler.pausar()
                return
            
            Display.msg(f"Descargado: {archivo_seleccionado}")
            self.utils.logger.info(f"Archivo descargado: {archivo_seleccionado}")
            
            print()
            if InputHandler.confirmar("¿Descomprimir ahora?"):
                self._descomprimir_backup(archivo_seleccionado)
        
        except Exception as e:
            Display.error(f"Error: {e}")
            self.utils.logger.error(f"Error en listar_y_descargar: {e}")
        finally:
            self._resume_autobackup(was_enabled)
            InputHandler.pausar()
    
    def gestionar_backups(self):
        """Menú para gestionar backups existentes"""
        was_enabled = self._pause_autobackup()
        
        try:
            Display.clear()
            Display.header("GESTIONAR BACKUPS EN MEGA")
            
            if not self.utils.verificar_megacmd():
                Display.error("MegaCMD no está disponible")
                return
            
            backup_folder = self.config.CONFIG.get("backup_folder", "/backups")
            backup_prefix = self.config.CONFIG.get("backup_prefix", "MSX")
            
            print(f"{Tema.FOLDER} Listando backups en: {backup_folder}\n")
            
            cmd = ["mega-ls", backup_folder]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                Display.error("No se pudo listar backups")
                return
            
            archivos = [line.strip() for line in result.stdout.split('\n') 
                       if backup_prefix in line and '.zip' in line]
            archivos.sort(reverse=True)
            
            if not archivos:
                Display.warning("No hay backups en MEGA")
                return
            
            print(f"Backups encontrados: {len(archivos)}\n")
            Display.lista_archivos(archivos)
            
            opciones = [
                "Eliminar backup específico",
                "Limpiar backups antiguos",
                "Ver información de cuenta",
                "Volver"
            ]
            
            opcion = InputHandler.seleccionar_opcion("", opciones)
            
            if opcion == 1:
                self._eliminar_backup(archivos, backup_folder)
            elif opcion == 2:
                if self.backup:
                    self.backup.limpiar_backups_antiguos()
                else:
                    Display.error("Módulo backup no disponible")
            elif opcion == 3:
                self.info_cuenta()
                return
        
        except Exception as e:
            Display.error(f"Error: {e}")
            self.utils.logger.error(f"Error en gestionar_backups: {e}")
        finally:
            self._resume_autobackup(was_enabled)
            InputHandler.pausar()
    
    def _eliminar_backup(self, archivos, backup_folder):
        """Elimina un backup específico"""
        num = InputHandler.seleccionar_numero(
            "\nNúmero de backup a eliminar (0 para cancelar)",
            min_val=0,
            max_val=len(archivos)
        )
        
        if num == 0 or num is None:
            print("Cancelado")
            return
        
        archivo_eliminar = archivos[num - 1]
        
        if InputHandler.confirmar(f"¿Eliminar {archivo_eliminar}?"):
            cmd_rm = ["mega-rm", f"{backup_folder}/{archivo_eliminar}"]
            result_rm = subprocess.run(cmd_rm, capture_output=True, text=True)
            
            if result_rm.returncode == 0:
                Display.msg(f"Eliminado: {archivo_eliminar}")
                self.utils.logger.info(f"Backup eliminado: {archivo_eliminar}")
            else:
                Display.error("Error al eliminar")
                self.utils.logger.error(f"Error eliminando {archivo_eliminar}")
        else:
            print("Cancelado")
    
    def subir_archivo(self):
        """Menú para subir archivo a MEGA"""
        was_enabled = self._pause_autobackup()
        
        try:
            Display.clear()
            Display.header("SUBIR ARCHIVO A MEGA")
            
            if not self.utils.verificar_megacmd():
                Display.error("MegaCMD no está disponible")
                return
            
            archivo = InputHandler.input_texto("Ruta del archivo a subir", requerido=False)
            
            if not archivo:
                print("Cancelado")
                return
            
            if not os.path.exists(archivo):
                Display.error(f"Archivo no encontrado: {archivo}")
                return
            
            if not os.path.isfile(archivo):
                Display.error("La ruta debe ser un archivo, no un directorio")
                return
            
            size = os.path.getsize(archivo)
            size_mb = size / (1024 * 1024)
            
            backup_folder = self.config.CONFIG.get("backup_folder", "/backups")
            
            print(f"\n{Tema.FILE} Archivo: {os.path.basename(archivo)}")
            print(f"{Tema.PACKAGE} Tamaño: {size_mb:.1f} MB")
            print(f"{Tema.FOLDER} Destino: {backup_folder}\n")
            
            if not InputHandler.confirmar("¿Subir archivo?"):
                print("Cancelado")
                return
            
            print()
            
            cmd_put = ["mega-put", archivo, backup_folder]
            proceso = subprocess.Popen(cmd_put, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            spinner = self.utils.Spinner("Subiendo")
            if not spinner.start(proceso):
                Display.error("Error al subir archivo")
                self.utils.logger.error(f"Error subiendo {archivo}")
                return
            
            Display.msg(f"Archivo subido: {os.path.basename(archivo)}")
            self.utils.logger.info(f"Archivo subido: {archivo} -> {backup_folder}")
        
        except Exception as e:
            Display.error(f"Error: {e}")
            self.utils.logger.error(f"Error en subir_archivo: {e}")
        finally:
            self._resume_autobackup(was_enabled)
            InputHandler.pausar()
    
    def info_cuenta(self):
        """Muestra información de la cuenta MEGA"""
        was_enabled = self._pause_autobackup()
        
        try:
            Display.clear()
            Display.header("INFORMACIÓN DE CUENTA MEGA")
            
            if not self.utils.verificar_megacmd():
                Display.error("MegaCMD no está disponible")
                return
            
            # Usuario
            cmd_whoami = ["mega-whoami"]
            result_whoami = subprocess.run(cmd_whoami, capture_output=True, text=True)
            
            if result_whoami.returncode == 0:
                email = result_whoami.stdout.strip()
                print(f"{Tema.EMAIL} Usuario: {email}\n")
            
            # Cuota
            cmd_quota = ["mega-df", "-h"]
            result_quota = subprocess.run(cmd_quota, capture_output=True, text=True)
            
            if result_quota.returncode == 0:
                print(f"{Tema.DISK} Espacio en cuenta:\n")
                print(result_quota.stdout)
            
            # Backups
            backup_folder = self.config.CONFIG.get("backup_folder", "/backups")
            print(f"\n{Tema.FOLDER} Backups en {backup_folder}:")
            
            cmd_ls = ["mega-ls", backup_folder]
            result_ls = subprocess.run(cmd_ls, capture_output=True, text=True)
            
            if result_ls.returncode == 0:
                archivos = [line for line in result_ls.stdout.split('\n') if '.zip' in line]
                print(f" {len(archivos)} backups almacenados")
        
        except Exception as e:
            Display.error(f"Error: {e}")
            self.utils.logger.error(f"Error en info_cuenta: {e}")
        finally:
            self._resume_autobackup(was_enabled)
            InputHandler.pausar()
    
    def _descomprimir_backup(self, archivo):
        """Descomprime un archivo de backup"""
        try:
            if not os.path.exists(archivo):
                Display.error(f"Archivo no encontrado: {archivo}")
                return
            
            server_folder = self.config.CONFIG.get("server_folder", "servidor_minecraft")
            
            print(f"\n{Tema.PACKAGE} Descomprimiendo: {archivo}")
            print(f"{Tema.FOLDER} Destino: {server_folder}")
            
            if os.path.exists(server_folder):
                if not InputHandler.confirmar(f"\n⚠️ La carpeta {server_folder} será reemplazada. ¿Continuar?"):
                    print("Cancelado")
                    return
                
                import shutil
                backup_old = f"{server_folder}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                print(f"\n{Tema.DISK} Respaldando carpeta actual a: {backup_old}")
                shutil.move(server_folder, backup_old)
            
            print()
            
            cmd_unzip = ["unzip", "-q", "-o", archivo]
            proceso = subprocess.Popen(cmd_unzip)
            
            spinner = self.utils.Spinner("Descomprimiendo")
            if not spinner.start(proceso):
                Display.error("Error al descomprimir")
                return
            
            Display.msg("Descompresión completada")
            self.utils.logger.info(f"Backup descomprimido: {archivo}")
            
            if InputHandler.confirmar("\n¿Eliminar archivo ZIP?"):
                os.remove(archivo)
                Display.msg(f"Eliminado: {archivo}")
        
        except Exception as e:
            Display.error(f"Error descomprimiendo: {e}")
            self.utils.logger.error(f"Error en descomprimir_backup: {e}")


# ============================================================
# FUNCIONES DE COMPATIBILIDAD
# ============================================================
# Estas funciones mantienen compatibilidad con código existente

def crear_menu_backup(config, utils, backup, autobackup):
    """Factory function para crear instancia de MenuBackup"""
    return MenuBackup(config, utils, backup, autobackup)

def crear_menu_archivos(config, utils, backup, autobackup):
    """Factory function para crear instancia de MenuArchivos"""
    return MenuArchivos(config, utils, backup, autobackup)


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    'Tema',
    'Display',
    'InputHandler',
    'MenuBackup',
    'MenuArchivos',
    'crear_menu_backup',
    'crear_menu_archivos'
]
