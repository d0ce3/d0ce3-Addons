import os
import subprocess
import time
from datetime import datetime, timedelta, timezone

TIMEZONE_ARG = timezone(timedelta(hours=-3))

config = CloudModuleLoader.load_module("config")
utils = CloudModuleLoader.load_module("utils")
megacmd = CloudModuleLoader.load_module("megacmd")

def encontrar_carpeta_servidor(nombre_carpeta="servidor_minecraft"):
    ubicaciones_a_verificar = [
        f"/workspaces/{os.environ.get('CODESPACE_NAME', 'unknown')}/{nombre_carpeta}",
        None,
        os.path.join(os.getcwd(), nombre_carpeta),
        os.path.join(os.path.dirname(os.getcwd()), nombre_carpeta),
        os.path.expanduser(f"~/{nombre_carpeta}"),
    ]
    
    for ubicacion in ubicaciones_a_verificar:
        if ubicacion and os.path.exists(ubicacion) and os.path.isdir(ubicacion):
            utils.logger.info(f"Carpeta del servidor encontrada en: {ubicacion}")
            return ubicacion
    
    try:
        if os.path.exists("/workspaces"):
            for item in os.listdir("/workspaces"):
                ruta_posible = os.path.join("/workspaces", item, nombre_carpeta)
                if os.path.exists(ruta_posible) and os.path.isdir(ruta_posible):
                    utils.logger.info(f"Carpeta del servidor encontrada en: {ruta_posible}")
                    return ruta_posible
    except:
        pass
    
    utils.logger.error(f"No se pudo encontrar la carpeta '{nombre_carpeta}'")
    return None

def comprimir_con_manejo_archivos_activos(carpeta_origen, archivo_destino, max_intentos=3):
    """
    Comprime una carpeta manejando archivos que puedan estar siendo modificados.
    
    Estrategia:
    1. Usa zip con flag -q (quiet) y -y (preserve symlinks) 
    2. Usa --filesync para manejar archivos que cambien durante compresión
    3. Implementa reintentos con espera progresiva
    4. Limpia archivos corruptos si todos los intentos fallan
    
    Returns:
        tuple: (success: bool, archivo_creado: str or None, error_msg: str or None)
    """
    parent_dir = os.path.dirname(carpeta_origen)
    folder_name = os.path.basename(carpeta_origen)
    backup_path = os.path.join(parent_dir, archivo_destino)
    
    for intento in range(1, max_intentos + 1):
        try:
            utils.logger.info(f"Intento {intento}/{max_intentos} de compresión")
            
            # Limpiar archivo previo si existe de intento anterior
            if os.path.exists(backup_path):
                try:
                    os.remove(backup_path)
                    utils.logger.info(f"Archivo previo eliminado: {backup_path}")
                except Exception as e:
                    utils.logger.warning(f"No se pudo eliminar archivo previo: {e}")
            
            # Usar flags especiales de zip para manejar archivos activos:
            # -r: recursivo
            # -q: quiet (sin output)
            # -FS: sincronización de archivos (reintenta si archivo cambió durante lectura)
            # -y: preservar symlinks
            cmd = ["zip", "-r", "-q", "-FS", "-y", archivo_destino, folder_name]
            
            utils.logger.info(f"Ejecutando: {' '.join(cmd)}")
            
            resultado = subprocess.run(
                cmd,
                cwd=parent_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=600,
                text=True
            )
            
            # Verificar resultado
            # zip retorna 0=ok, 2=warnings (archivos cambiaron pero zip ok), 18=algunos archivos no legibles
            if resultado.returncode in [0, 2, 12, 18]:
                # Verificar que el archivo existe y tiene tamaño > 0
                if os.path.exists(backup_path) and os.path.getsize(backup_path) > 1024:
                    size_mb = os.path.getsize(backup_path) / (1024 * 1024)
                    
                    if resultado.returncode != 0:
                        utils.logger.warning(
                            f"Compresión completada con warnings (código {resultado.returncode}). "
                            f"Esto es normal si archivos cambiaron durante el backup."
                        )
                    
                    utils.logger.info(f"Compresión exitosa: {archivo_destino} ({size_mb:.1f} MB)")
                    return (True, backup_path, None)
                else:
                    error = "Archivo ZIP creado pero inválido (muy pequeño o vacío)"
                    utils.logger.error(error)
                    if intento < max_intentos:
                        espera = intento * 2
                        utils.logger.info(f"Esperando {espera}s antes de reintentar...")
                        time.sleep(espera)
                        continue
                    return (False, None, error)
            else:
                error = f"zip falló con código {resultado.returncode}: {resultado.stderr}"
                utils.logger.error(error)
                
                if intento < max_intentos:
                    espera = intento * 2
                    utils.logger.info(f"Esperando {espera}s antes de reintentar...")
                    time.sleep(espera)
                    continue
                else:
                    return (False, None, error)
        
        except subprocess.TimeoutExpired:
            error = "Timeout en compresión (>10 min)"
            utils.logger.error(error)
            
            # Limpiar archivo corrupto
            if os.path.exists(backup_path):
                try:
                    os.remove(backup_path)
                    utils.logger.info("Archivo corrupto eliminado tras timeout")
                except:
                    pass
            
            if intento < max_intentos:
                espera = intento * 3
                utils.logger.info(f"Esperando {espera}s antes de reintentar tras timeout...")
                time.sleep(espera)
                continue
            else:
                return (False, None, error)
        
        except Exception as e:
            error = f"Error inesperado en compresión: {e}"
            utils.logger.error(error)
            
            if intento < max_intentos:
                espera = intento * 2
                utils.logger.info(f"Esperando {espera}s antes de reintentar...")
                time.sleep(espera)
                continue
            else:
                return (False, None, error)
    
    # Si llegamos aquí, todos los intentos fallaron
    # Limpiar cualquier archivo corrupto
    if os.path.exists(backup_path):
        try:
            os.remove(backup_path)
            utils.logger.info("Archivo corrupto eliminado tras todos los intentos")
        except Exception as e:
            utils.logger.error(f"No se pudo eliminar archivo corrupto: {e}")
    
    return (False, None, "Todos los intentos de compresión fallaron")

def listar_carpetas_mega(ruta="/"):
    try:
        result = megacmd.list_files(ruta)
        
        if result.returncode != 0:
            utils.logger.error(f"Error listando carpetas en MEGA: {result.stderr}")
            return None
        
        carpetas = []
        lineas = result.stdout.strip().split('\n')
        for linea in lineas:
            nombre = linea.strip()
            if nombre and nombre != '..' and nombre != '.':
                carpetas.append(nombre)
        
        return carpetas
        
    except Exception as e:
        utils.logger.error(f"Error listando carpetas MEGA: {e}")
        return None

def navegar_carpetas_mega(ruta_inicial="/"):
    ruta_actual = ruta_inicial
    
    while True:
        utils.limpiar_pantalla()
        print("\n" + "=" * 60)
        print("SELECCIONAR CARPETA EN MEGA")
        print("=" * 60)
        print(f"📂 {ruta_actual}\n")
        
        carpetas = listar_carpetas_mega(ruta_actual)
        
        if carpetas is None:
            utils.print_error("No se pudo obtener la lista de carpetas")
            utils.pausar()
            return None
        
        if not carpetas:
            print("(Carpeta vacía)\n")
        else:
            for i, carpeta in enumerate(carpetas, 1):
                print(f" {i}. 📁 {carpeta}")
        
        print("\n" + "-" * 60)
        print("[número] Entrar | [0] Subir | [s] Seleccionar | [c] Cancelar")
        print("-" * 60)
        
        opcion = input("\n> ").strip().lower()
        
        if opcion == 'c':
            return None
        elif opcion == 's':
            return ruta_actual
        elif opcion == '0':
            if ruta_actual != "/":
                ruta_actual = os.path.dirname(ruta_actual)
                if not ruta_actual:
                    ruta_actual = "/"
        else:
            try:
                indice = int(opcion)
                if 1 <= indice <= len(carpetas):
                    carpeta_seleccionada = carpetas[indice - 1]
                    if ruta_actual == "/":
                        ruta_actual = f"/{carpeta_seleccionada}"
                    else:
                        ruta_actual = f"{ruta_actual}/{carpeta_seleccionada}"
                else:
                    utils.print_warning("Número inválido")
                    utils.pausar()
            except ValueError:
                utils.print_warning("Opción inválida")
                utils.pausar()

def ejecutar_backup_manual():
    utils.limpiar_pantalla()
    print("\n" + "=" * 60)
    print("CREAR BACKUP EN MEGA")
    print("=" * 60 + "\n")
    
    utils.logger.info("========== INICIO BACKUP MANUAL ==========")
    
    try:
        if not utils.verificar_megacmd():
            utils.print_error("MegaCMD no está disponible")
            utils.pausar()
            return
        
        server_folder_config = config.CONFIG.get("server_folder", "servidor_minecraft")
        server_folder = encontrar_carpeta_servidor(server_folder_config)
        backup_folder = config.CONFIG.get("backup_folder", "/backups")
        backup_prefix = config.CONFIG.get("backup_prefix", "MSX")
        
        utils.logger.info(f"Configuración - Carpeta config: {server_folder_config}")
        utils.logger.info(f"Configuración - BASE_DIR: {config.BASE_DIR}")
        utils.logger.info(f"Configuración - os.getcwd(): {os.getcwd()}")
        utils.logger.info(f"Configuración - parent de BASE_DIR: {os.path.dirname(config.BASE_DIR)}")
        utils.logger.info(f"Configuración - Carpeta resuelta: {server_folder}")
        utils.logger.info(f"Configuración - ¿Existe? {os.path.exists(server_folder) if server_folder else False}")
        utils.logger.info(f"Configuración - Destino: {backup_folder}")
        
        if not server_folder or not os.path.exists(server_folder):
            utils.print_error(f"La carpeta {server_folder_config} no se pudo encontrar")
            utils.logger.error(f"Carpeta {server_folder_config} no encontrada")
            utils.pausar()
            return
        
        print(f"📁 Carpeta: {server_folder}")
        print("📊 Calculando tamaño...")
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(server_folder):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except:
                    pass
        
        size_mb = total_size / (1024 * 1024)
        print(f"📦 Tamaño total: {size_mb:.1f} MB\n")
        
        utils.logger.info(f"Tamaño de carpeta: {size_mb:.1f} MB")
        
        if not utils.confirmar("¿Crear backup ahora?"):
            print("Cancelado")
            utils.logger.info("Backup cancelado por usuario")
            utils.pausar()
            return
        
        print()
        
        timestamp = datetime.now(TIMEZONE_ARG).strftime("%d-%m-%Y_%H-%M")
        backup_name = f"{backup_prefix}_{timestamp}.zip"
        
        utils.logger.info(f"Nombre de backup: {backup_name}")
        utils.logger.info("Iniciando compresión con manejo de archivos activos...")
        
        print("⏳ Comprimiendo (puede tomar varios minutos)...")
        print("💡 Esto es normal si el servidor está en uso")
        
        # Usar la nueva función con reintentos
        exito, backup_path, error = comprimir_con_manejo_archivos_activos(
            server_folder, 
            backup_name,
            max_intentos=3
        )
        
        if not exito:
            utils.print_error(f"Error al comprimir: {error}")
            utils.logger.error(f"Fallo en compresión: {error}")
            utils.pausar()
            return
        
        backup_size = os.path.getsize(backup_path)
        backup_size_mb = backup_size / (1024 * 1024)
        
        print(f"✓ Archivo creado: {backup_name} ({backup_size_mb:.1f} MB)\n")
        
        utils.logger.info("Iniciando subida a MEGA...")
        
        proceso_upload = subprocess.Popen(
            ["mega-put", "-c", backup_name, backup_folder + "/"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(backup_path)
        )
        
        spinner_upload = utils.Spinner("Subiendo a MEGA")
        if not spinner_upload.start(proceso_upload):
            utils.print_error("Error al subir a MEGA")
            utils.logger.error("Fallo en subida a MEGA")
            try:
                os.remove(backup_path)
                utils.logger.info("Archivo local eliminado tras error")
            except:
                pass
            utils.pausar()
            return
        
        utils.logger.info(f"Backup subido exitosamente a {backup_folder}/{backup_name}")
        
        try:
            os.remove(backup_path)
            utils.logger.info("Archivo local eliminado")
        except Exception as e:
            utils.print_warning(f"No se pudo eliminar archivo local: {e}")
            utils.logger.warning(f"Error eliminando archivo local: {e}")
        
        print()
        utils.print_msg(f"Backup creado exitosamente: {backup_name}")
        utils.logger.info("========== FIN BACKUP MANUAL ==========")
        
        print()
        if utils.confirmar("¿Limpiar backups antiguos ahora?"):
            limpiar_backups_antiguos()
    
    except Exception as e:
        utils.print_error(f"Error creando backup: {e}")
        utils.logger.error(f"Error en crear_backup: {e}")
        import traceback
        utils.logger.error(traceback.format_exc())
    
    utils.pausar()

def ejecutar_backup_automatico():
    logger_mod = CloudModuleLoader.load_module("logger")
    logger_mod.log_backup_auto_inicio()
    
    print("\n" + "="*60)
    print("| INICIANDO BACKUP AUTOMÁTICO")
    print("="*60)
    
    try:
        if not config.CONFIG.get("autobackup_enabled", False):
            utils.logger.info("Autobackup desactivado, no se ejecutará")
            return
        
        server_folder_config = config.CONFIG.get("server_folder", "servidor_minecraft")
        server_folder = encontrar_carpeta_servidor(server_folder_config)
        backup_folder = config.CONFIG.get("backup_folder", "/backups")
        backup_prefix = config.CONFIG.get("backup_prefix", "MSX")
        
        utils.logger.info(f"Configuración - Carpeta config: {server_folder_config}")
        utils.logger.info(f"Configuración - BASE_DIR: {config.BASE_DIR}")
        utils.logger.info(f"Configuración - os.getcwd(): {os.getcwd()}")
        utils.logger.info(f"Configuración - parent de BASE_DIR: {os.path.dirname(config.BASE_DIR)}")
        utils.logger.info(f"Configuración - Carpeta resuelta: {server_folder}")
        utils.logger.info(f"Configuración - ¿Existe? {os.path.exists(server_folder) if server_folder else False}")
        utils.logger.info(f"Configuración - Destino: {backup_folder}")
        
        if not server_folder or not os.path.exists(server_folder):
            error_msg = f"Carpeta {server_folder_config} no encontrada"
            utils.logger.error(error_msg)
            print(f"| ERROR: {error_msg}")
            logger_mod.log_backup_auto_error(error_msg)
            
            try:
                rcon = CloudModuleLoader.load_module("rcon")
                if rcon and rcon.is_connected():
                    rcon.send_command(f"say [BACKUP ERROR] {error_msg}")
            except:
                pass
            
            return
        
        print("| Calculando tamaño de carpeta...")
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(server_folder):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except:
                    pass
        
        size_mb = total_size / (1024 * 1024)
        print(f"| Tamaño total: {size_mb:.1f} MB")
        utils.logger.info(f"Tamaño de carpeta: {size_mb:.1f} MB")
        
        timestamp = datetime.now(TIMEZONE_ARG).strftime("%d-%m-%Y_%H-%M")
        backup_name = f"{backup_prefix}_{timestamp}.zip"
        
        print(f"| Archivo a crear: {backup_name}")
        print("| Comprimiendo (con manejo de archivos activos)...")
        utils.logger.info(f"Nombre de backup: {backup_name}")
        utils.logger.info("Iniciando compresión automática con reintentos...")
        
        # Usar la nueva función con reintentos automáticos
        exito, backup_path, error = comprimir_con_manejo_archivos_activos(
            server_folder,
            backup_name,
            max_intentos=3
        )
        
        if not exito:
            error_msg = f"Error en compresión automática: {error}"
            utils.logger.error(error_msg)
            print(f"| ERROR: {error_msg}")
            logger_mod.log_backup_auto_error(error_msg)
            
            try:
                rcon = CloudModuleLoader.load_module("rcon")
                if rcon and rcon.is_connected():
                    rcon.send_command(f"say [BACKUP ERROR] Compresión falló")
            except:
                pass
            
            return
        
        backup_size = os.path.getsize(backup_path)
        backup_size_mb = backup_size / (1024 * 1024)
        print(f"| Comprimido: {backup_size_mb:.1f} MB")
        utils.logger.info(f"Archivo creado: {backup_name} ({backup_size_mb:.1f} MB)")
        
        print(f"| Subiendo a MEGA ({backup_folder})...")
        utils.logger.info("Iniciando subida a MEGA...")
        
        result = megacmd.upload_file(backup_path, backup_folder, silent=False)
        
        if result.returncode != 0:
            error_msg = "Error al subir backup automático a MEGA"
            utils.logger.error(error_msg)
            print(f"| ERROR: {error_msg}")
            logger_mod.log_backup_auto_error(error_msg)
            
            try:
                rcon = CloudModuleLoader.load_module("rcon")
                if rcon and rcon.is_connected():
                    rcon.send_command(f"say [BACKUP ERROR] Subida a MEGA falló")
            except:
                pass
            
            try:
                os.remove(backup_path)
                utils.logger.info("Archivo local eliminado tras error de subida")
            except:
                pass
            return
        
        print(f"| Subido exitosamente a {backup_folder}/{backup_name}")
        utils.logger.info(f"Backup automático subido exitosamente: {backup_folder}/{backup_name}")
        logger_mod.log_backup_auto_exito(backup_name, backup_size_mb)
        
        try:
            os.remove(backup_path)
            utils.logger.info("Archivo local eliminado")
        except Exception as e:
            utils.logger.warning(f"No se pudo eliminar archivo local: {e}")
        
        print("="*60 + "\n")
        
    except Exception as e:
        error_msg = f"Error en backup automático: {str(e)}"
        utils.logger.error(error_msg)
        print(f"| ERROR: {error_msg}")
        
        try:
            logger_mod.log_backup_auto_error(error_msg)
        except:
            pass
        
        try:
            rcon = CloudModuleLoader.load_module("rcon")
            if rcon and rcon.is_connected():
                rcon.send_command(f"say [BACKUP ERROR] {error_msg}")
        except:
            pass

def limpiar_backups_antiguos():
    try:
        max_backups = config.CONFIG.get("max_backups", 5)
        backup_folder = config.CONFIG.get("backup_folder", "/backups")
        backup_prefix = config.CONFIG.get("backup_prefix", "MSX")
        
        utils.logger.info(f"Limpiando backups antiguos (mantener {max_backups})...")
        
        result = megacmd.list_files(backup_folder)
        
        if result.returncode != 0:
            utils.logger.error("Error listando backups")
            return
        
        archivos = [line.strip() for line in result.stdout.split('\n') 
                   if backup_prefix in line and '.zip' in line]
        archivos.sort(reverse=True)
        
        utils.logger.info(f"Backups encontrados: {len(archivos)}")
        
        if len(archivos) <= max_backups:
            return
        
        a_eliminar = archivos[max_backups:]
        
        for archivo in a_eliminar:
            result_rm = megacmd.remove_file(f"{backup_folder}/{archivo}")
            
            if result_rm.returncode == 0:
                utils.logger.info(f"Eliminado: {archivo}")
            else:
                utils.logger.warning(f"Error eliminando {archivo}")
        
        utils.logger.info(f"Limpieza completada - {len(a_eliminar)} backups eliminados")
    
    except Exception as e:
        utils.logger.error(f"Error en limpiar_backups_antiguos: {e}")