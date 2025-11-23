import os
import subprocess
from datetime import datetime

class Tema:
    MORADO = "\033[95m"
    MORADO_CLARO = "\033[35m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
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
    
    LINE = "─" * 50
    
    @staticmethod
    def m(texto):
        return f"{Tema.MORADO}{texto}{Tema.RESET}"
    
    @staticmethod
    def mb(texto):
        return f"{Tema.BOLD}{Tema.MORADO}{texto}{Tema.RESET}"

class Display:
    @staticmethod
    def header(titulo):
        print(f"\n{Tema.LINE}")
        print(Tema.mb(titulo))
        print(f"{Tema.LINE}\n")
    
    @staticmethod
    def msg(mensaje, icono=None):
        icono = icono or Tema.CHECK
        print(f"{icono} {mensaje}")
    
    @staticmethod
    def error(mensaje, icono=None):
        icono = icono or Tema.ERROR
        print(f"{icono} {mensaje}")
    
    @staticmethod
    def warning(mensaje, icono=None):
        icono = icono or Tema.WARNING
        print(f"{icono} {mensaje}")
    
    @staticmethod
    def info(mensaje, icono=None):
        icono = icono or Tema.INFO
        print(f"{icono} {mensaje}")
    
    @staticmethod
    def lista_opciones(opciones):
        for i, opcion in enumerate(opciones, 1):
            print(Tema.m(f" {i}. {opcion}"))
    
    @staticmethod
    def lista_archivos(archivos):
        for idx, archivo in enumerate(archivos, 1):
            if isinstance(archivo, dict):
                nombre = archivo.get('nombre', archivo.get('name', 'N/A'))
                size = archivo.get('size_str', archivo.get('size', ''))
                texto = f" {idx}. {nombre} ({size})" if size else f" {idx}. {nombre}"
            else:
                texto = f" {idx}. {archivo}"
            print(Tema.m(texto))
    
    @staticmethod
    def clear():
        os.system('clear' if os.name != 'nt' else 'cls')

class InputHandler:
    @staticmethod
    def confirmar(mensaje):
        respuesta = input(Tema.m(f"{mensaje} (s/n): ")).strip().lower()
        return respuesta in ['s', 'si', 'y', 'yes']
    
    @staticmethod
    def seleccionar_numero(mensaje, min_val=0, max_val=None, permitir_x=False):
        while True:
            try:
                valor = input(Tema.m(f"{mensaje}: ")).strip().lower()
                
                if not valor:
                    return None
                
                if permitir_x and valor == 'x':
                    return 'x'
                
                numero = int(valor)
                if max_val is not None:
                    if min_val <= numero <= max_val:
                        return numero
                    else:
                        Display.warning(f"Número entre {min_val} y {max_val}")
                elif numero >= min_val:
                    return numero
                else:
                    Display.warning(f"Número mayor o igual a {min_val}")
            except ValueError:
                if permitir_x:
                    Display.warning("Ingrese número válido o 'x' para volver")
                else:
                    Display.warning("Ingrese número válido")
            except KeyboardInterrupt:
                print("\nCancelado")
                return None
    
    @staticmethod
    def seleccionar_opcion(opciones, tiene_volver=True):
        Display.lista_opciones(opciones)
        if tiene_volver:
            print(Tema.m(" x. Volver"))
        print()
        return InputHandler.seleccionar_numero(
            "Opción", 
            min_val=0 if not tiene_volver else 1, 
            max_val=len(opciones),
            permitir_x=tiene_volver
        )
    
    @staticmethod
    def input_texto(mensaje, requerido=True):
        while True:
            valor = input(Tema.m(f"{mensaje}: ")).strip()
            if valor or not requerido:
                return valor
            Display.warning("Campo requerido")
    
    @staticmethod
    def pausar():
        input(Tema.m("\nEnter para continuar..."))

class MenuBackup:
    def __init__(self, config, utils, backup, autobackup):
        self.config = config
        self.utils = utils
        self.backup = backup
        self.autobackup = autobackup
    
    def crear_backup_manual(self):
        Display.clear()
        Display.header("CREAR BACKUP")
        
        try:
            self._ejecutar_backup_manual()
        except Exception as e:
            Display.error(f"Error: {e}")
            self.utils.logger.error(f"Error en crear_backup: {e}")
            import traceback
            self.utils.logger.error(traceback.format_exc())
        
        InputHandler.pausar()
    
    def _ejecutar_backup_manual(self):
        self.utils.logger.info("========== INICIO BACKUP MANUAL ==========")
        
        if not self.utils.verificar_megacmd():
            Display.error("MegaCMD no disponible")
            return
        
        server_folder_config = self.config.CONFIG.get("server_folder", "servidor_minecraft")
        server_folder = self.backup.encontrar_carpeta_servidor(server_folder_config)
        backup_folder = self.config.CONFIG.get("backup_folder", "/backups")
        backup_prefix = self.config.CONFIG.get("backup_prefix", "MSX")
        
        if not server_folder or not os.path.exists(server_folder):
            Display.error(f"Carpeta {server_folder_config} no encontrada")
            self.utils.logger.error(f"Carpeta {server_folder_config} no encontrada")
            return
        
        print(f"{Tema.FOLDER} {server_folder}")
        print(f"{Tema.PACKAGE} Calculando tamaño...")
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(server_folder):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except:
                    pass
        
        size_mb = total_size / (1024 * 1024)
        print(f"{Tema.PACKAGE} {size_mb:.1f} MB\n")
        
        if not InputHandler.confirmar("¿Crear backup?"):
            print("Cancelado")
            return
        
        print()
        timestamp = datetime.now(self.backup.TIMEZONE_ARG).strftime("%d-%m-%Y_%H-%M")
        backup_name = f"{backup_prefix}_{timestamp}.zip"
        
        cmd = ["zip", "-r", "-q", backup_name, server_folder]
        proceso = subprocess.Popen(cmd)
        
        spinner = self.utils.Spinner("Comprimiendo")
        if not spinner.start(proceso, check_file=backup_name):
            Display.error("Error al comprimir")
            return
        
        if not os.path.exists(backup_name):
            Display.error("ZIP no creado")
            return
        
        backup_size_mb = os.path.getsize(backup_name) / (1024 * 1024)
        print(f"\n{Tema.CHECK} {backup_name} ({backup_size_mb:.1f} MB)\n")
        
        cmd_upload = ["mega-put", backup_name, backup_folder]
        proceso_upload = subprocess.Popen(cmd_upload, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        spinner_upload = self.utils.Spinner("Subiendo a MEGA")
        if not spinner_upload.start(proceso_upload):
            Display.error("Error al subir")
            try:
                os.remove(backup_name)
            except:
                pass
            return
        
        try:
            os.remove(backup_name)
        except Exception as e:
            Display.warning(f"No se pudo eliminar local: {e}")
        
        print()
        Display.msg(f"Backup creado: {backup_name}")
        self.utils.logger.info("========== FIN BACKUP MANUAL ==========")
        
        print()
        if InputHandler.confirmar("¿Limpiar backups antiguos?"):
            self.backup.limpiar_backups_antiguos()
    
    def configurar_autobackup(self):
        if not self.utils.verificar_megacmd():
            Display.error("MegaCMD no disponible")
            InputHandler.pausar()
            return
        
        while True:
            Display.clear()
            Display.header("CONFIGURAR AUTOBACKUP")
            
            autobackup_enabled = self.config.CONFIG.get("autobackup_enabled", False)
            intervalo_actual = self.config.CONFIG.get("backup_interval_minutes", 5)
            backup_folder = self.config.CONFIG.get("backup_folder", "/backups")
            server_folder = self.config.CONFIG.get("server_folder", "servidor_minecraft")
            max_backups = self.config.CONFIG.get("max_backups", 5)
            
            estado = f"{Tema.CHECK} ACTIVADO" if autobackup_enabled else f"{Tema.ERROR} DESACTIVADO"
            print(Tema.m(f"Estado: {estado}"))
            print(Tema.m(f"Intervalo: {intervalo_actual} min"))
            print(Tema.m(f"Carpeta: {server_folder}"))
            print(Tema.m(f"Destino: {backup_folder}"))
            print(Tema.m(f"Máximo: {max_backups} backups"))
            print()
            
            opciones = []
            if autobackup_enabled:
                opciones.append("Desactivar autobackup")
            else:
                opciones.append("Activar autobackup")
            
            opciones.extend([
                "Cambiar intervalo",
                "Cambiar destino",
                "Cambiar máximo backups"
            ])
            
            opcion = InputHandler.seleccionar_opcion(opciones)
            
            if opcion == 'x' or opcion is None:
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
        if estado_actual:
            self.config.set("autobackup_enabled", False)
            Display.msg("Autobackup desactivado")
            self.utils.logger.info("Autobackup desactivado")
        else:
            self.config.set("autobackup_enabled", True)
            Display.msg("Autobackup activado")
            self.utils.logger.info("Autobackup activado")
        
        print("\n⚠️ Reinicie el proceso para aplicar cambios")
        InputHandler.pausar()
    
    def _cambiar_intervalo(self, intervalo_actual):
        print(f"\n{Tema.TIMER} Actual: {intervalo_actual} min")
        nuevo_intervalo = InputHandler.seleccionar_numero(
            "Nuevo intervalo (1-60 min)",
            min_val=1,
            max_val=60
        )
        
        if nuevo_intervalo:
            self.config.set("backup_interval_minutes", nuevo_intervalo)
            Display.msg(f"Intervalo: {nuevo_intervalo} min")
            self.utils.logger.info(f"Intervalo: {nuevo_intervalo} min")
        
        InputHandler.pausar()
    
    def _cambiar_ruta_guardado(self, backup_folder):
        print(f"\n{Tema.CLOUD} Actual: {backup_folder}\n")
        
        opciones = [
            "Navegar por MEGA",
            "Escribir ruta manual"
        ]
        
        opcion = InputHandler.seleccionar_opcion(opciones)
        
        if opcion == 1:
            print(f"\n🔍 Cargando...")
            nueva_ruta = self.backup.navegar_carpetas_mega(backup_folder)
            if nueva_ruta:
                self.config.set("backup_folder", nueva_ruta)
                Display.msg(f"Destino: {nueva_ruta}")
                self.utils.logger.info(f"Destino: {nueva_ruta}")
            else:
                print("Cancelado")
        elif opcion == 2:
            nuevo_destino = InputHandler.input_texto("Nueva carpeta (ej: /backups)", requerido=False)
            if nuevo_destino:
                if not nuevo_destino.startswith("/"):
                    nuevo_destino = "/" + nuevo_destino
                self.config.set("backup_folder", nuevo_destino)
                Display.msg(f"Destino: {nuevo_destino}")
                self.utils.logger.info(f"Destino: {nuevo_destino}")
        
        InputHandler.pausar()
    
    def _cambiar_max_backups(self, max_actual):
        print(f"\n{Tema.FOLDER} Actual: {max_actual}")
        print("💡 Recomendado: 5")
        
        nuevo_max = InputHandler.seleccionar_numero(
            "Nueva cantidad (1-10)",
            min_val=1,
            max_val=10
        )
        
        if nuevo_max:
            self.config.set("max_backups", nuevo_max)
            Display.msg(f"Máximo: {nuevo_max} backups")
            self.utils.logger.info(f"Máximo: {nuevo_max}")
        
        InputHandler.pausar()

class MenuArchivos:
    def __init__(self, config, utils, backup, autobackup):
        self.config = config
        self.utils = utils
        self.backup = backup
        self.autobackup = autobackup
    
    def _pause_autobackup(self):
        if self.autobackup.is_enabled():
            self.autobackup.stop_autobackup()
            return True
        return False
    
    def _resume_autobackup(self, was_enabled):
        if was_enabled:
            self.autobackup.start_autobackup()
    
    def listar_y_descargar(self):
        was_enabled = self._pause_autobackup()
        
        try:
            Display.clear()
            Display.header("LISTAR Y DESCARGAR")
            
            if not self.utils.verificar_megacmd():
                Display.error("MegaCMD no disponible")
                return
            
            print(f"{Tema.FOLDER} Carpetas en MEGA:\n")
            
            cmd_ls_root = ["mega-ls", "-l"]
            result_root = subprocess.run(cmd_ls_root, capture_output=True, text=True)
            
            if result_root.returncode != 0:
                Display.error("No se pudo listar MEGA")
                return
            
            carpetas = []
            for line in result_root.stdout.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 2 and parts[0].startswith('d'):
                    carpetas.append(parts[-1])
            
            if not carpetas:
                carpetas = [self.config.CONFIG.get("backup_folder", "/backups")]
            
            Display.lista_archivos(carpetas)
            
            opcion = input(Tema.m("\nCarpeta (0=raíz): ")).strip()
            
            if opcion == '0':
                ruta = "/"
            else:
                try:
                    idx_sel = int(opcion) - 1
                    ruta = "/" + carpetas[idx_sel] if 0 <= idx_sel < len(carpetas) else "/"
                except:
                    ruta = "/"
            
            print(f"\n{Tema.FOLDER} {ruta}\n")
            
            cmd_ls = ["mega-ls", "-l", ruta]
            result = subprocess.run(cmd_ls, capture_output=True, text=True)
            
            if result.returncode != 0:
                Display.error("No se pudo listar")
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
                Display.warning("No hay archivos ZIP")
                return
            
            Display.lista_archivos(archivos)
            
            seleccion = InputHandler.seleccionar_numero(
                "\nArchivo a descargar (0=cancelar)",
                min_val=0,
                max_val=len(archivos)
            )
            
            if seleccion == 0 or seleccion is None:
                print("Cancelado")
                return
            
            archivo_seleccionado = archivos[seleccion - 1]['nombre']
            print(f"\n📥 {archivo_seleccionado}")
            
            full_ruta = f"{ruta}/{archivo_seleccionado}".replace('//', '/')
            cmd_get = ["mega-get", full_ruta, "."]
            proceso = subprocess.Popen(cmd_get, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            spinner = self.utils.Spinner("Descargando")
            if not spinner.start(proceso):
                Display.error("Error al descargar")
                return
            
            Display.msg(f"Descargado: {archivo_seleccionado}")
            self.utils.logger.info(f"Descargado: {archivo_seleccionado}")
            
            print()
            if InputHandler.confirmar("¿Descomprimir?"):
                self._descomprimir_backup(archivo_seleccionado)
        
        except Exception as e:
            Display.error(f"Error: {e}")
            self.utils.logger.error(f"Error en listar_y_descargar: {e}")
        finally:
            self._resume_autobackup(was_enabled)
            InputHandler.pausar()
    
    def gestionar_backups(self):
        was_enabled = self._pause_autobackup()
        
        try:
            Display.clear()
            Display.header("GESTIONAR BACKUPS")
            
            if not self.utils.verificar_megacmd():
                Display.error("MegaCMD no disponible")
                return
            
            backup_folder = self.config.CONFIG.get("backup_folder", "/backups")
            backup_prefix = self.config.CONFIG.get("backup_prefix", "MSX")
            
            print(f"{Tema.FOLDER} {backup_folder}\n")
            
            cmd = ["mega-ls", backup_folder]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                Display.error("No se pudo listar")
                return
            
            archivos = [line.strip() for line in result.stdout.split('\n') 
                       if backup_prefix in line and '.zip' in line]
            archivos.sort(reverse=True)
            
            if not archivos:
                Display.warning("No hay backups")
                return
            
            print(Tema.m(f"Total: {len(archivos)}\n"))
            Display.lista_archivos(archivos)
            
            opciones = [
                "Eliminar backup",
                "Limpiar antiguos",
                "Info cuenta"
            ]
            
            opcion = InputHandler.seleccionar_opcion(opciones)
            
            if opcion == 1:
                self._eliminar_backup(archivos, backup_folder)
            elif opcion == 2:
                if self.backup:
                    self.backup.limpiar_backups_antiguos()
                else:
                    Display.error("Módulo no disponible")
            elif opcion == 3:
                self.info_cuenta()
                return
        
        except Exception as e:
            Display.error(f"Error: {e}")
            self.utils.logger.error(f"Error: {e}")
        finally:
            self._resume_autobackup(was_enabled)
            InputHandler.pausar()
    
    def _eliminar_backup(self, archivos, backup_folder):
        num = InputHandler.seleccionar_numero(
            "\nBackup a eliminar (0=cancelar)",
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
                self.utils.logger.info(f"Eliminado: {archivo_eliminar}")
            else:
                Display.error("Error al eliminar")
                self.utils.logger.error(f"Error eliminando {archivo_eliminar}")
        else:
            print("Cancelado")
    
    def subir_archivo(self):
        was_enabled = self._pause_autobackup()
        
        try:
            Display.clear()
            Display.header("SUBIR ARCHIVO")
            
            if not self.utils.verificar_megacmd():
                Display.error("MegaCMD no disponible")
                return
            
            archivo = InputHandler.input_texto("Ruta del archivo", requerido=False)
            
            if not archivo:
                print("Cancelado")
                return
            
            if not os.path.exists(archivo):
                Display.error(f"No encontrado: {archivo}")
                return
            
            if not os.path.isfile(archivo):
                Display.error("Debe ser archivo, no directorio")
                return
            
            size = os.path.getsize(archivo)
            size_mb = size / (1024 * 1024)
            
            backup_folder = self.config.CONFIG.get("backup_folder", "/backups")
            
            print(f"\n{Tema.FILE} {os.path.basename(archivo)}")
            print(f"{Tema.PACKAGE} {size_mb:.1f} MB")
            print(f"{Tema.FOLDER} {backup_folder}\n")
            
            if not InputHandler.confirmar("¿Subir?"):
                print("Cancelado")
                return
            
            print()
            
            cmd_put = ["mega-put", archivo, backup_folder]
            proceso = subprocess.Popen(cmd_put, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            spinner = self.utils.Spinner("Subiendo")
            if not spinner.start(proceso):
                Display.error("Error al subir")
                self.utils.logger.error(f"Error subiendo {archivo}")
                return
            
            Display.msg(f"Subido: {os.path.basename(archivo)}")
            self.utils.logger.info(f"Subido: {archivo} -> {backup_folder}")
        
        except Exception as e:
            Display.error(f"Error: {e}")
            self.utils.logger.error(f"Error: {e}")
        finally:
            self._resume_autobackup(was_enabled)
            InputHandler.pausar()
    
    def info_cuenta(self):
        was_enabled = self._pause_autobackup()
        
        try:
            Display.clear()
            Display.header("INFO CUENTA")
            
            if not self.utils.verificar_megacmd():
                Display.error("MegaCMD no disponible")
                return
            
            cmd_whoami = ["mega-whoami"]
            result_whoami = subprocess.run(cmd_whoami, capture_output=True, text=True)
            
            if result_whoami.returncode == 0:
                email = result_whoami.stdout.strip()
                print(f"{Tema.EMAIL} {email}\n")
            
            cmd_quota = ["mega-df", "-h"]
            result_quota = subprocess.run(cmd_quota, capture_output=True, text=True)
            
            if result_quota.returncode == 0:
                print(f"{Tema.DISK} Espacio:\n")
                print(result_quota.stdout)
            
            backup_folder = self.config.CONFIG.get("backup_folder", "/backups")
            print(f"\n{Tema.FOLDER} Backups en {backup_folder}:")
            
            cmd_ls = ["mega-ls", backup_folder]
            result_ls = subprocess.run(cmd_ls, capture_output=True, text=True)
            
            if result_ls.returncode == 0:
                archivos = [line for line in result_ls.stdout.split('\n') if '.zip' in line]
                print(Tema.m(f" {len(archivos)} backups"))
        
        except Exception as e:
            Display.error(f"Error: {e}")
            self.utils.logger.error(f"Error: {e}")
        finally:
            self._resume_autobackup(was_enabled)
            InputHandler.pausar()
    
    def _descomprimir_backup(self, archivo):
        try:
            if not os.path.exists(archivo):
                Display.error(f"No encontrado: {archivo}")
                return
            
            server_folder = self.config.CONFIG.get("server_folder", "servidor_minecraft")
            
            print(f"\n{Tema.PACKAGE} {archivo}")
            print(f"{Tema.FOLDER} {server_folder}")
            
            if os.path.exists(server_folder):
                if not InputHandler.confirmar(f"\n⚠️ {server_folder} será reemplazada. ¿Continuar?"):
                    print("Cancelado")
                    return
                
                import shutil
                backup_old = f"{server_folder}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                print(f"\n{Tema.DISK} Respaldo: {backup_old}")
                shutil.move(server_folder, backup_old)
            
            print()
            
            cmd_unzip = ["unzip", "-q", "-o", archivo]
            proceso = subprocess.Popen(cmd_unzip)
            
            spinner = self.utils.Spinner("Descomprimiendo")
            if not spinner.start(proceso):
                Display.error("Error al descomprimir")
                return
            
            Display.msg("Descompresión completada")
            self.utils.logger.info(f"Descomprimido: {archivo}")
            
            if InputHandler.confirmar("\n¿Eliminar ZIP?"):
                os.remove(archivo)
                Display.msg(f"Eliminado: {archivo}")
        
        except Exception as e:
            Display.error(f"Error: {e}")
            self.utils.logger.error(f"Error: {e}")

def crear_menu_backup(config, utils, backup, autobackup):
    return MenuBackup(config, utils, backup, autobackup)

def crear_menu_archivos(config, utils, backup, autobackup):
    return MenuArchivos(config, utils, backup, autobackup)

__all__ = [
    'Tema',
    'Display',
    'InputHandler',
    'MenuBackup',
    'MenuArchivos',
    'crear_menu_backup',
    'crear_menu_archivos'
]
