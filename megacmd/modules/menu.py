import os
import subprocess
from datetime import datetime

class Tema:
    MORADO = "\033[95m"
    MORADO_CLARO = "\033[35m"
    VERDE = "\033[92m"
    ROJO = "\033[91m"
    AMARILLO = "\033[93m"
    BLANCO = "\033[97m"
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
    
    @staticmethod
    def verde(texto):
        return f"{Tema.VERDE}{texto}{Tema.RESET}"
    
    @staticmethod
    def rojo(texto):
        return f"{Tema.ROJO}{texto}{Tema.RESET}"
    
    @staticmethod
    def amarillo(texto):
        return f"{Tema.AMARILLO}{texto}{Tema.RESET}"
    
    @staticmethod
    def blanco(texto):
        return f"{Tema.BLANCO}{texto}{Tema.RESET}"

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
                    Display.warning("Ingrese número válido o 'x' para cancelar")
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
        self.megacmd = CloudModuleLoader.load_module("megacmd")
    
    def crear_backup_manual(self):
        try:
            self.backup.ejecutar_backup_manual()
        except Exception as e:
            Display.error(f"Error: {e}")
            self.utils.logger.error(f"Error en crear_backup: {e}")
            import traceback
            self.utils.logger.error(traceback.format_exc())
            InputHandler.pausar()
    
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
            
            if autobackup_enabled:
                estado_texto = f"{Tema.CHECK} ACTIVADO"
                estado_color = Tema.verde(estado_texto)
            else:
                estado_texto = f"{Tema.ERROR} DESACTIVADO"
                estado_color = Tema.rojo(estado_texto)
            
            def len_sin_ansi(texto):
                import re
                return len(re.sub(r'\033\[[0-9;]*m', '', texto))
            
            def pad_linea(label, valor_coloreado):
                longitud_label = len(label) + 2
                longitud_valor = len_sin_ansi(valor_coloreado)
                espacios_necesarios = 46 - longitud_label - longitud_valor
                contenido = f" {Tema.m(label)}: {valor_coloreado}{' ' * espacios_necesarios} "
                return Tema.m("│") + contenido + Tema.m("│")
            
            # Imprime el cuadro con alineación perfecta
            print(Tema.m("┌" + "─" * 48 + "┐"))
            print(pad_linea("Estado", estado_color))
            print(pad_linea("Intervalo", Tema.blanco(f"{intervalo_actual} min")))
            print(pad_linea("Carpeta", Tema.blanco(server_folder)))
            print(pad_linea("Destino", Tema.blanco(backup_folder)))
            print(pad_linea("Máximo", Tema.blanco(f"{max_backups} backups")))
            print(Tema.m("└" + "─" * 48 + "┘"))
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
            # Desactivar
            if InputHandler.confirmar("¿Desactivar autobackup?"):
                self.autobackup.disable()
                Display.msg("Autobackup desactivado")
                print(Tema.amarillo("\nℹ Los backups nativos de MSX permanecen desactivados"))
                print(Tema.amarillo("  Puedes reactivarlos manualmente en configuracion.json"))
                self.utils.logger.info("Autobackup desactivado")
        else:
            # Activar - MOSTRAR ADVERTENCIA
            Display.clear()
            Display.header("⚠️ ADVERTENCIA: ACTIVAR AUTOBACKUP")
            
            print(Tema.amarillo("⚠ Al activar el sistema de autobackup:"))
            print()
            print("  1. Los backups nativos de MSX serán DESACTIVADOS")
            print("  2. El campo 'backup_mode' se limpiará (si es 'luna', quedará vacío)")
            print("  3. El campo 'backup_auto' se pondrá en false")
            print()
            print("Cambios en configuracion.json:")
            print(Tema.rojo('  "backup_mode": "luna"  ->  "backup_mode": ""'))
            print(Tema.verde('  "backup_auto": true   ->  "backup_auto": false'))
            print()
            print("ℹ Esto evita conflictos entre ambos sistemas de backup")
            print("ℹ Solo d0ce3tools gestionará los backups automáticos")
            print()
            print(Tema.LINE)
            print()
            
            if InputHandler.confirmar("¿Deseas continuar?"):
                self.autobackup.enable()
                Display.msg("\nAutobackup activado")
                Display.msg("Sistema nativo de MSX desactivado")
                self.utils.logger.info("Autobackup activado - backups nativos desactivados")
            else:
                print("\nCancelado")
        
        InputHandler.pausar()
    
    def _cambiar_intervalo(self, intervalo_actual):
        print(f"\n{Tema.TIMER} Actual: {intervalo_actual} min")
        nuevo_intervalo = InputHandler.seleccionar_numero(
            "Nuevo intervalo (1-60 min)",
            min_val=1,
            max_val=60
        )
        
        if nuevo_intervalo:
            autobackup_estaba_activo = self.config.CONFIG.get("autobackup_enabled", False)
            
            if autobackup_estaba_activo:
                print(f"\n{Tema.INFO} Reiniciando timer con nuevo intervalo...")
                self.autobackup.stop_autobackup()
            
            self.config.set("backup_interval_minutes", nuevo_intervalo)
            Display.msg(f"Intervalo: {nuevo_intervalo} min")
            self.utils.logger.info(f"Intervalo cambiado a {nuevo_intervalo} min")
            
            if autobackup_estaba_activo:
                self.autobackup.start_autobackup()
                Display.msg("Timer reiniciado correctamente")
                self.utils.logger.info("Timer reiniciado con nuevo intervalo")
        
        InputHandler.pausar()
    
    def _cambiar_ruta_guardado(self, backup_folder):
        print(f"\n{Tema.CLOUD} Actual: {backup_folder}\n")
        
        opciones = [
            "Navegar por MEGA",
            "Escribir ruta manual"
        ]
        
        opcion = InputHandler.seleccionar_opcion(opciones)
        
        if opcion == 1:
            print(f"\n📁 Cargando...")
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
        self.megacmd = CloudModuleLoader.load_module("megacmd")
    
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
            
            result_root = self.megacmd.list_files("/", detailed=True)
            
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
            
            result = self.megacmd.list_files(ruta, detailed=True)
            
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
            
            print(Tema.m(f"Total: {len(archivos)} archivos\n"))
            
            print(Tema.m("┌────┬──────────┬──────────────┬──────────┐"))
            print(Tema.m(f"│ {'#':<2} │ {'Nombre':<8} │ {'Fecha':<12} │ {'Hora':<8} │"))
            print(Tema.m("├────┼──────────┼──────────────┼──────────┤"))
            
            for idx, archivo in enumerate(archivos, 1):
                nombre_completo = archivo['nombre']
                try:
                    nombre_sin_ext = nombre_completo.replace('.zip', '')
                    partes = nombre_sin_ext.split('_')
                    if len(partes) >= 3:
                        prefijo = partes[0]
                        fecha = partes[1].replace('-', '/')
                        hora = partes[2].replace('-', ':')
                        print(Tema.m(f"│ {idx:<2} │ {prefijo:<8} │ {fecha:<12} │ {hora:<8} │"))
                    else:
                        print(Tema.m(f"│ {idx:<2} │ {nombre_completo:<32} │"))
                except:
                    print(Tema.m(f"│ {idx:<2} │ {nombre_completo:<32} │"))
            
            print(Tema.m("└────┴──────────┴──────────────┴──────────┘"))
            print()
            
            seleccion = InputHandler.seleccionar_numero(
                "Archivo a descargar (número, x=cancelar)",
                min_val=1,
                max_val=len(archivos),
                permitir_x=True
            )
            
            if seleccion == 'x' or seleccion is None:
                print("Cancelado")
                return
            
            archivo_seleccionado = archivos[seleccion - 1]['nombre']
            print(f"\n📥 {archivo_seleccionado}")
            
            full_ruta = f"{ruta}/{archivo_seleccionado}".replace('//', '/')
            
            # Simplemente usar mega-get sin especificar destino
            # Se descargará en el directorio actual (donde se ejecuta el script)
            result = self.megacmd.download_file(full_ruta)
            
            if result.returncode != 0:
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
            
            result = self.megacmd.list_files(backup_folder)
            
            if result.returncode != 0:
                Display.error("No se pudo listar")
                return
            
            archivos = [line.strip() for line in result.stdout.split('\n')
                       if backup_prefix in line and '.zip' in line]
            archivos.sort(reverse=True)
            
            if not archivos:
                Display.warning("No hay backups")
                return
            
            print(Tema.m(f"Total: {len(archivos)} backups\n"))
            
            print(Tema.m("┌──────────┬──────────────┬──────────┐"))
            print(Tema.m(f"│ {'Nombre':<8} │ {'Fecha':<12} │ {'Hora':<8} │"))
            print(Tema.m("├──────────┼──────────────┼──────────┤"))
            
            for archivo in archivos:
                try:
                    nombre_sin_ext = archivo.replace('.zip', '')
                    partes = nombre_sin_ext.split('_')
                    if len(partes) >= 3:
                        prefijo = partes[0]
                        fecha = partes[1].replace('-', '/')
                        hora = partes[2].replace('-', ':')
                        print(Tema.m(f"│ {prefijo:<8} │ {fecha:<12} │ {hora:<8} │"))
                    else:
                        print(Tema.m(f"│ {archivo:<34} │"))
                except:
                    print(Tema.m(f"│ {archivo:<34} │"))
            
            print(Tema.m("└──────────┴──────────────┴──────────┘"))
            print()
            
            opciones = [
                "Eliminar backup",
                "Limpiar backups antiguos",
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
            "\nBackup a eliminar (número, x=cancelar)",
            min_val=1,
            max_val=len(archivos),
            permitir_x=True
        )
        
        if num == 'x' or num is None:
            print("Cancelado")
            return
        
        archivo_eliminar = archivos[num - 1]
        
        if InputHandler.confirmar(f"¿Eliminar {archivo_eliminar}?"):
            result_rm = self.megacmd.remove_file(f"{backup_folder}/{archivo_eliminar}")
            
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
            
            result = self.megacmd.upload_file(archivo, backup_folder, silent=False)
            
            if result.returncode != 0:
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
            
            email = self.megacmd.get_account_email()
            
            if email:
                print(f"{Tema.EMAIL} {email}\n")
            
            result_quota = self.megacmd.get_quota()
            
            if result_quota.returncode == 0:
                print(f"{Tema.DISK} Espacio:\n")
                print(result_quota.stdout)
            
            backup_folder = self.config.CONFIG.get("backup_folder", "/backups")
            print(f"\n{Tema.FOLDER} Backups en {backup_folder}:")
            
            result_ls = self.megacmd.list_files(backup_folder)
            
            if result_ls.returncode == 0:
                archivos = [line for line in result_ls.stdout.split('\n') if '.zip' in line]
                print(Tema.m(f" {len(archivos)} backups"))
            
            print("\n" + Tema.LINE)
            if InputHandler.confirmar("\n¿Cerrar sesión en MEGA?"):
                print()
                self.megacmd.logout()
        
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
