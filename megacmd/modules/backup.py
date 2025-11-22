import os
import subprocess
from datetime import datetime

config = CloudModuleLoader.load_module("config")
utils = CloudModuleLoader.load_module("utils")

def encontrar_carpeta_servidor(nombre_carpeta="servidor_minecraft"):
    """
    Encuentra la carpeta del servidor de forma inteligente.
    Busca en múltiples ubicaciones comunes.
    """
    # Lista de ubicaciones a verificar
    ubicaciones_a_verificar = [
        # 1. Ruta absoluta directa en /workspaces
        f"/workspaces/{os.environ.get('CODESPACE_NAME', 'unknown')}/{nombre_carpeta}",
        
        # 2. Buscar en /workspaces/*/servidor_minecraft
        None,  # Se busca dinámicamente
        
        # 3. Relativo desde getcwd()
        os.path.join(os.getcwd(), nombre_carpeta),
        
        # 4. Subir un nivel desde getcwd()
        os.path.join(os.path.dirname(os.getcwd()), nombre_carpeta),
        
        # 5. En el home del usuario
        os.path.expanduser(f"~/{nombre_carpeta}"),
    ]
    
    # Verificar ubicaciones directas
    for ubicacion in ubicaciones_a_verificar:
        if ubicacion and os.path.exists(ubicacion) and os.path.isdir(ubicacion):
            utils.logger.info(f"Carpeta del servidor encontrada en: {ubicacion}")
            return ubicacion
    
    # Búsqueda dinámica en /workspaces
    try:
        if os.path.exists("/workspaces"):
            for item in os.listdir("/workspaces"):
                ruta_posible = os.path.join("/workspaces", item, nombre_carpeta)
                if os.path.exists(ruta_posible) and os.path.isdir(ruta_posible):
                    utils.logger.info(f"Carpeta del servidor encontrada en: {ruta_posible}")
                    return ruta_posible
    except:
        pass
    
    # Si no se encuentra, retornar None
    utils.logger.error(f"No se pudo encontrar la carpeta '{nombre_carpeta}'")
    return None

def listar_carpetas_mega(ruta="/"):
    """
    Lista las carpetas disponibles en MEGA en la ruta especificada.
    Retorna una lista de nombres de carpetas.
    """
    try:
        cmd = ["mega-ls", ruta]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            utils.logger.error(f"Error listando carpetas en MEGA: {result.stderr}")
            return None
        
        # Obtener solo nombres de carpetas (sin detalles)
        carpetas = []
        lineas = result.stdout.strip().split('\n')
        
        for linea in lineas:
            nombre = linea.strip()
            if nombre and nombre != '..' and nombre != '.':
                carpetas.append(nombre)
        
        return carpetas
    except subprocess.TimeoutExpired:
        utils.print_error("Tiempo de espera agotado al consultar MEGA")
        return None
    except Exception as e:
        utils.logger.error(f"Error listando carpetas MEGA: {e}")
        return None

def navegar_carpetas_mega(ruta_inicial="/"):
    """
    Permite navegar por las carpetas de MEGA de forma interactiva y simplificada.
    Retorna la ruta seleccionada o None si se cancela.
    """
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
                print(f"   {i}. 📁 {carpeta}")
        
        print("\n" + "-" * 60)
        print("[número] Entrar  |  [0] Subir  |  [s] Seleccionar  |  [c] Cancelar")
        print("-" * 60)
        
        opcion = input("\n> ").strip().lower()
        
        if opcion == 'c':
            return None
        elif opcion == 's':
            return ruta_actual
        elif opcion == '0':
            # Subir un nivel
            if ruta_actual != "/":
                ruta_actual = os.path.dirname(ruta_actual)
                if not ruta_actual:
                    ruta_actual = "/"
        else:
            # Intentar entrar a una carpeta
            try:
                indice = int(opcion)
                if 1 <= indice <= len(carpetas):
                    carpeta_seleccionada = carpetas[indice - 1]
                    # Construir nueva ruta
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

        # Obtener ruta y resolverla correctamente
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
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        backup_name = f"{backup_prefix}_{timestamp}.zip"

        utils.logger.info(f"Nombre de backup: {backup_name}")
        utils.logger.info("Iniciando compresión...")

        cmd = ["zip", "-r", "-q", backup_name, server_folder]
        proceso = subprocess.Popen(cmd)
        spinner = utils.Spinner("Comprimiendo")
        if not spinner.start(proceso, check_file=backup_name):
            utils.print_error("Error al comprimir")
            utils.logger.error("Fallo en compresión")
            utils.pausar()
            return

        if not os.path.exists(backup_name):
            utils.print_error("El archivo ZIP no se creó")
            utils.logger.error(f"Archivo {backup_name} no encontrado")
            utils.pausar()
            return

        backup_size = os.path.getsize(backup_name)
        backup_size_mb = backup_size / (1024 * 1024)
        utils.logger.info(f"Archivo creado: {backup_name} ({backup_size_mb:.1f} MB)")
        print(f"✓ Archivo creado: {backup_name} ({backup_size_mb:.1f} MB)\n")

        utils.logger.info("Iniciando subida a MEGA...")

        cmd_upload = ["mega-put", backup_name, backup_folder]
        proceso_upload = subprocess.Popen(cmd_upload, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        spinner_upload = utils.Spinner("Subiendo a MEGA")
        if not spinner_upload.start(proceso_upload):
            utils.print_error("Error al subir a MEGA")
            utils.logger.error("Fallo en subida a MEGA")
            try:
                os.remove(backup_name)
                utils.logger.info("Archivo local eliminado tras error")
            except:
                pass
            utils.pausar()
            return

        utils.logger.info(f"Backup subido exitosamente a {backup_folder}/{backup_name}")
        try:
            os.remove(backup_name)
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
    utils.logger.info("========== INICIO BACKUP AUTOMÁTICO ==========")
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
            utils.logger.error(f"Carpeta {server_folder_config} no encontrada, se cancela backup automático")
            return

        total_size = 0
        for dirpath, dirnames, filenames in os.walk(server_folder):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except:
                    pass
        size_mb = total_size / (1024 * 1024)
        utils.logger.info(f"Tamaño de carpeta: {size_mb:.1f} MB")

        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        backup_name = f"{backup_prefix}_{timestamp}.zip"
        utils.logger.info(f"Nombre de backup: {backup_name}")

        cmd = ["zip", "-r", "-q", backup_name, server_folder]
        proceso = subprocess.run(cmd)
        if proceso.returncode != 0 or not os.path.exists(backup_name):
            utils.logger.error("Error durante compresión automática")
            return

        backup_size = os.path.getsize(backup_name)
        backup_size_mb = backup_size / (1024 * 1024)
        utils.logger.info(f"Archivo creado: {backup_name} ({backup_size_mb:.1f} MB)")

        cmd_upload = ["mega-put", backup_name, backup_folder]
        proceso_upload = subprocess.run(cmd_upload)
        if proceso_upload.returncode != 0:
            utils.logger.error("Error al subir backup automático a MEGA")
            try:
                os.remove(backup_name)
            except:
                pass
            return

        utils.logger.info(f"Backup automático subido exitosamente: {backup_folder}/{backup_name}")

        try:
            os.remove(backup_name)
            utils.logger.info("Archivo local eliminado")
        except Exception as e:
            utils.logger.warning(f"No se pudo eliminar archivo local: {e}")

        utils.logger.info("========== FIN BACKUP AUTOMÁTICO ==========")

    except Exception as e:
        utils.logger.error(f"Error en backup automático: {str(e)}")

def limpiar_backups_antiguos():
    try:
        max_backups = config.CONFIG.get("max_backups", 5)
        backup_folder = config.CONFIG.get("backup_folder", "/backups")
        backup_prefix = config.CONFIG.get("backup_prefix", "MSX")
        utils.logger.info(f"Limpiando backups antiguos (mantener {max_backups})...")
        cmd_list = ["mega-ls", backup_folder]
        result = subprocess.run(cmd_list, capture_output=True, text=True)
        if result.returncode != 0:
            utils.logger.error("Error listando backups")
            return
        archivos = [line.strip() for line in result.stdout.split('\n') if backup_prefix in line and '.zip' in line]
        archivos.sort(reverse=True)
        utils.logger.info(f"Backups encontrados: {len(archivos)}")
        if len(archivos) <= max_backups:
            return
        a_eliminar = archivos[max_backups:]
        for archivo in a_eliminar:
            cmd_rm = ["mega-rm", f"{backup_folder}/{archivo}"]
            result_rm = subprocess.run(cmd_rm, capture_output=True, text=True)
            if result_rm.returncode == 0:
                utils.logger.info(f"Eliminado: {archivo}")
            else:
                utils.logger.warning(f"Error eliminando {archivo}")
        utils.logger.info(f"Limpieza completada - {len(a_eliminar)} backups eliminados")
    except Exception as e:
        utils.logger.error(f"Error en limpiar_backups_antiguos: {e}")

def configurar_autobackup():
    """
    Configura el autobackup de forma interactiva y simplificada.
    """
    utils.limpiar_pantalla()
    print("\n" + "=" * 60)
    print("CONFIGURAR AUTOBACKUP")
    print("=" * 60 + "\n")
    
    # Verificar MegaCMD
    if not utils.verificar_megacmd():
        utils.print_error("MegaCMD no está disponible")
        utils.pausar()
        return
    
    # Mostrar configuración actual
    autobackup_enabled = config.CONFIG.get("autobackup_enabled", False)
    intervalo_actual = config.CONFIG.get("backup_interval_minutes", 5)
    backup_folder = config.CONFIG.get("backup_folder", "/backups")
    server_folder = config.CONFIG.get("server_folder", "servidor_minecraft")
    max_backups = config.CONFIG.get("max_backups", 5)
    backup_prefix = config.CONFIG.get("backup_prefix", "MSX")
    
    print("📋 CONFIGURACIÓN ACTUAL:")
    print(f"   Estado: {'✓ ACTIVADO' if autobackup_enabled else '✗ DESACTIVADO'}")
    print(f"   Intervalo: cada {intervalo_actual} minutos")
    print(f"   Carpeta servidor: {server_folder}")
    print(f"   Destino MEGA: {backup_folder}")
    print(f"   Prefijo backup: {backup_prefix}")
    print(f"   Máximo backups: {max_backups}")
    print()
    
    utils.logger.info("========== CONFIGURAR AUTOBACKUP ==========")
    
    # Preguntar si activar/desactivar
    if autobackup_enabled:
        if utils.confirmar("¿Desactivar autobackup?"):
            config.set("autobackup_enabled", False)
            utils.print_msg("Autobackup desactivado")
            utils.logger.info("Autobackup desactivado por usuario")
            utils.pausar()
            return
        else:
            print("\nAutobackup sigue activado. Puede modificar la configuración:\n")
    else:
        if not utils.confirmar("¿Activar autobackup?"):
            print("Cancelado")
            utils.logger.info("Configuración de autobackup cancelada")
            utils.pausar()
            return
    
    # Configurar intervalo
    print(f"\n⏱️  Intervalo actual: {intervalo_actual} minutos")
    if utils.confirmar("¿Cambiar intervalo?"):
        while True:
            try:
                nuevo_intervalo = input("   Nuevo intervalo en minutos (1-60): ").strip()
                nuevo_intervalo = int(nuevo_intervalo)
                if 1 <= nuevo_intervalo <= 60:
                    intervalo_actual = nuevo_intervalo
                    break
                else:
                    utils.print_warning("Intervalo debe estar entre 1 y 60 minutos")
            except ValueError:
                utils.print_warning("Ingrese un número válido")
            except KeyboardInterrupt:
                print("\nCancelado")
                utils.pausar()
                return
    
    # OMITIDA: Configuración de carpeta servidor (siempre será servidor_minecraft)
    
    # Configurar destino MEGA con navegador simplificado
    print(f"\n☁️  Destino MEGA actual: {backup_folder}")
    print("\n¿Cómo desea seleccionar la carpeta destino?")
    print("   1. Navegar por MEGA")
    print("   2. Escribir ruta manualmente")
    print("   3. Mantener actual")
    
    opcion_destino = input("\nSeleccione opción (1-3): ").strip()
    
    if opcion_destino == "1":
        print("\n🔍 Cargando carpetas MEGA...")
        nueva_ruta = navegar_carpetas_mega(backup_folder)
        if nueva_ruta:
            backup_folder = nueva_ruta
            utils.print_msg(f"Carpeta seleccionada: {backup_folder}")
            utils.logger.info(f"Destino MEGA cambiado a: {backup_folder}")
        else:
            print("Navegación cancelada, se mantiene la carpeta actual")
    elif opcion_destino == "2":
        nuevo_destino = input("   Nueva carpeta MEGA (ej: /backups): ").strip()
        if nuevo_destino:
            if not nuevo_destino.startswith("/"):
                nuevo_destino = "/" + nuevo_destino
            backup_folder = nuevo_destino
            utils.logger.info(f"Destino MEGA cambiado a: {nuevo_destino}")
    
    # Configurar prefijo de backup
    print(f"\n🏷️  Prefijo actual: {backup_prefix}")
    if utils.confirmar("¿Cambiar prefijo de backups?"):
        nuevo_prefijo = input("   Nuevo prefijo (ej: MSX): ").strip()
        if nuevo_prefijo:
            backup_prefix = nuevo_prefijo
            utils.logger.info(f"Prefijo cambiado a: {nuevo_prefijo}")
    
    # Configurar máximo de backups
    print(f"\n🗂️  Máximo de backups: {max_backups}")
    if utils.confirmar("¿Cambiar cantidad máxima de backups?"):
        while True:
            try:
                nuevo_max = input("   Cantidad máxima (1-20): ").strip()
                nuevo_max = int(nuevo_max)
                if 1 <= nuevo_max <= 20:
                    max_backups = nuevo_max
                    break
                else:
                    utils.print_warning("Cantidad debe estar entre 1 y 20")
            except ValueError:
                utils.print_warning("Ingrese un número válido")
            except KeyboardInterrupt:
                print("\nCancelado")
                utils.pausar()
                return
    
    # Mostrar resumen y confirmar
    print("\n" + "=" * 60)
    print("RESUMEN DE CONFIGURACIÓN")
    print("=" * 60)
    print(f"✓ Estado: ACTIVADO")
    print(f"✓ Intervalo: cada {intervalo_actual} minutos")
    print(f"✓ Carpeta servidor: {server_folder}")
    print(f"✓ Destino MEGA: {backup_folder}")
    print(f"✓ Prefijo: {backup_prefix}")
    print(f"✓ Máximo backups: {max_backups}")
    print("=" * 60 + "\n")
    
    if utils.confirmar("¿Guardar esta configuración?"):
        config.set("autobackup_enabled", True)
        config.set("backup_interval_minutes", intervalo_actual)
        config.set("server_folder", server_folder)
        config.set("backup_folder", backup_folder)
        config.set("backup_prefix", backup_prefix)
        config.set("max_backups", max_backups)
        
        utils.print_msg("Configuración guardada exitosamente")
        utils.logger.info(f"Autobackup configurado: intervalo={intervalo_actual}min, destino={backup_folder}, max={max_backups}")
        
        if autobackup_enabled:
            print("\n⚠️  Nota: Reinicie el proceso de autobackup para aplicar los cambios")
        else:
            print("\n✓ Autobackup activado con la nueva configuración")
    else:
        print("Configuración cancelada")
        utils.logger.info("Configuración cancelada por usuario")
    
    utils.pausar()