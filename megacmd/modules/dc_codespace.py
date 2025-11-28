import os
import subprocess
import json

utils = CloudModuleLoader.load_module("utils")
config = CloudModuleLoader.load_module("config")


def obtener_nombre_codespace():
    codespace_name = os.getenv("CODESPACE_NAME")
    
    if codespace_name:
        utils.logger.info(f"Codespace detectado: {codespace_name}")
        return codespace_name
    
    utils.logger.warning("CODESPACE_NAME no detectado")
    return None


def leer_configuracion_msx():
    workspace = os.getenv("CODESPACE_VSCODE_FOLDER", "/workspace")
    config_path = os.path.join(workspace, "configuracion.json")
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                configuracion = json.load(f)
            utils.logger.info(f"Configuración MSX cargada: servicio={configuracion.get('servicio_a_usar')}")
            return configuracion
        else:
            utils.logger.warning(f"Archivo configuracion.json no encontrado en {config_path}")
            return None
    except Exception as e:
        utils.logger.error(f"Error leyendo configuracion.json: {e}")
        return None


def obtener_ip_desde_playit():
    try:
        # Buscar archivo de configuración de playit
        workspace = os.getenv("CODESPACE_VSCODE_FOLDER", "/workspace")
        playit_config = os.path.join(workspace, ".playit", "config.toml")
        
        if os.path.exists(playit_config):
            with open(playit_config, 'r') as f:
                contenido = f.read()
            
            # Buscar la IP en el archivo
            for line in contenido.split('\n'):
                if 'address' in line.lower() or 'tunnel' in line.lower():
                    # Extraer IP del formato: address = "ip:puerto"
                    if '"' in line:
                        partes = line.split('"')
                        if len(partes) >= 2:
                            ip_completa = partes[1]
                            utils.logger.info(f"IP de playit encontrada: {ip_completa}")
                            return ip_completa
        
        # Si no se encuentra en config, intentar desde el proceso
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'playit' in line.lower():
                    # Intentar extraer IP del comando
                    utils.logger.info("Proceso playit detectado")
                    break
        
        utils.logger.warning("No se pudo obtener IP de playit")
        return None
        
    except Exception as e:
        utils.logger.error(f"Error obteniendo IP de playit: {e}")
        return None


def obtener_ip_desde_tailscale():
    try:
        result = subprocess.run(
            ["tailscale", "ip"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            ip = result.stdout.strip().split('\n')[0]  # Primera IP
            utils.logger.info(f"IP de tailscale obtenida: {ip}")
            return ip
        
        utils.logger.warning("No se pudo obtener IP de tailscale")
        return None
        
    except FileNotFoundError:
        utils.logger.warning("tailscale no instalado")
        return None
    except Exception as e:
        utils.logger.error(f"Error obteniendo IP de tailscale: {e}")
        return None


def obtener_ip_desde_zerotier():
    try:
        result = subprocess.run(
            ["zerotier-cli", "listnetworks"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            # Parsear output de zerotier-cli
            lineas = result.stdout.strip().split('\n')
            for linea in lineas[1:]:  # Saltar header
                partes = linea.split()
                if len(partes) >= 3:
                    # La IP suele estar en la última columna
                    ip_candidata = partes[-1]
                    if '.' in ip_candidata or ':' in ip_candidata:
                        utils.logger.info(f"IP de zerotier obtenida: {ip_candidata}")
                        return ip_candidata
        
        utils.logger.warning("No se pudo obtener IP de zerotier")
        return None
        
    except FileNotFoundError:
        utils.logger.warning("zerotier-cli no instalado")
        return None
    except Exception as e:
        utils.logger.error(f"Error obteniendo IP de zerotier: {e}")
        return None


def obtener_ip_codespace():
    configuracion_msx = leer_configuracion_msx()
    
    if not configuracion_msx:
        utils.logger.warning("No se pudo leer configuracion.json de MSX")
        return None
    
    servicio = configuracion_msx.get("servicio_a_usar", "").lower()
    
    if not servicio:
        utils.logger.warning("servicio_a_usar no especificado en configuracion.json")
        return None
    
    utils.logger.info(f"Servicio de túnel configurado: {servicio}")
    
    # Obtener IP según el servicio
    if servicio == "playit":
        ip = obtener_ip_desde_playit()
    elif servicio == "tailscale":
        ip = obtener_ip_desde_tailscale()
    elif servicio == "zerotier":
        ip = obtener_ip_desde_zerotier()
    else:
        utils.logger.warning(f"Servicio desconocido: {servicio}")
        return None
    
    if ip:
        utils.logger.info(f"IP obtenida desde {servicio}: {ip}")
        return ip
    else:
        utils.logger.warning(f"No se pudo obtener IP desde {servicio}")
        return None


def obtener_puertos_abiertos():
    try:
        result = subprocess.run(
            ["ss", "-tuln"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return []
        
        puertos = []
        for line in result.stdout.split('\n'):
            if 'LISTEN' in line or 'ESTAB' in line:
                parts = line.split()
                if len(parts) >= 5:
                    local_addr = parts[4]
                    if ':' in local_addr:
                        puerto = local_addr.split(':')[-1]
                        if puerto.isdigit():
                            puertos.append(int(puerto))
        
        puertos_unicos = sorted(list(set(puertos)))
        utils.logger.info(f"Puertos detectados: {puertos_unicos}")
        return puertos_unicos
        
    except Exception as e:
        utils.logger.error(f"Error obteniendo puertos: {e}")
        return []


def detectar_servidor_minecraft():
    puertos_minecraft = [25565, 25566, 25567, 25575]  # Incluye RCON
    puertos_abiertos = obtener_puertos_abiertos()
    
    for puerto in puertos_minecraft:
        if puerto in puertos_abiertos:
            utils.logger.info(f"Puerto Minecraft detectado: {puerto}")
            
            # Verificar si hay proceso Java corriendo
            if verificar_java_corriendo():
                return {
                    "puerto": puerto,
                    "ip": obtener_ip_codespace(),
                    "detectado": True
                }
    
    return None


def generar_ip_minecraft():
    info_servidor = detectar_servidor_minecraft()
    
    if not info_servidor:
        return None
    
    ip = info_servidor.get("ip")
    puerto = info_servidor.get("puerto", 25565)
    
    if not ip:
        return None
    
    # Si la IP ya incluye puerto (como en playit), usar así
    if ':' in ip:
        return ip
    
    # Si es puerto por defecto, no incluirlo
    if puerto == 25565:
        return ip
    else:
        return f"{ip}:{puerto}"


def verificar_configuracion_discord():
    estado = {
        "user_id_config": bool(config.CONFIG.get("discord_user_id")),
        "user_id_env": bool(os.getenv("DISCORD_USER_ID")),
        "webhook_url": bool(os.getenv("DISCORD_WEBHOOK_URL")),
        "codespace_name": bool(os.getenv("CODESPACE_NAME")),
        "configuracion_completa": False
    }
    
    estado["configuracion_completa"] = (
        (estado["user_id_config"] or estado["user_id_env"]) and
        estado["webhook_url"]
    )
    
    return estado


MORADO = "\033[95m"
VERDE = "\033[92m"
AMARILLO = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

def m(texto):
    return f"{MORADO}{texto}{RESET}"

def mb(texto):
    return f"{BOLD}{MORADO}{texto}{RESET}"

def verde(texto):
    return f"{VERDE}{texto}{RESET}"

def amarillo(texto):
    return f"{AMARILLO}{texto}{RESET}"


def mostrar_info_conexion():
    """Muestra información de conexión del Codespace y servidor Minecraft"""
    utils.limpiar_pantalla()
    print("\n" + m("─" * 50))
    print(mb("INFORMACIÓN DE CONEXIÓN"))
    print(m("─" * 50) + "\n")
    
    codespace_name = obtener_nombre_codespace()
    if codespace_name:
        print(verde(f"✓ Codespace: {codespace_name}"))
    else:
        print(amarillo("⚠ Codespace no detectado"))
    
    # Leer configuración MSX
    print()
    configuracion_msx = leer_configuracion_msx()
    if configuracion_msx:
        servicio = configuracion_msx.get("servicio_a_usar", "desconocido")
        print(verde(f"✓ Servicio de túnel: {servicio}"))
    else:
        print(amarillo("⚠ configuracion.json no encontrado"))
    
    print()
    ip = obtener_ip_codespace()
    if ip:
        print(verde(f"✓ IP del servicio: {ip}"))
    else:
        print(amarillo("⚠ No se pudo obtener IP del servicio"))
    
    # Servidor Minecraft
    print()
    info_mc = detectar_servidor_minecraft()
    if info_mc:
        ip_completa = generar_ip_minecraft()
        print(verde("✓ Servidor Minecraft detectado"))
        print(f"  Puerto: {info_mc['puerto']}")
        print(f"  IP: {ip_completa}")
    else:
        print(amarillo("⚠ Servidor Minecraft no detectado"))
    
    # Puertos abiertos
    print()
    puertos = obtener_puertos_abiertos()
    if puertos:
        puertos_str = ', '.join(map(str, puertos[:10]))
        print(f"Puertos abiertos: {puertos_str}")
        if len(puertos) > 10:
            print(f"  ... y {len(puertos) - 10} más")
    
    # Estado de configuración Discord
    print("\n" + m("─" * 50))
    print(mb("Configuración Discord"))
    print()
    estado = verificar_configuracion_discord()
    
    if estado["user_id_config"] or estado["user_id_env"]:
        print(verde("✓ User ID configurado"))
    else:
        print(amarillo("✗ User ID no configurado"))
    
    if estado["webhook_url"]:
        print(verde("✓ Webhook URL configurada"))
    else:
        print(amarillo("✗ Webhook URL no configurada"))
    
    print()
    
    if estado["configuracion_completa"]:
        print(verde("✓ Notificaciones activas"))
    else:
        print(amarillo("⚠ Notificaciones desactivadas"))
    
    print("\n" + m("─" * 50))
    utils.pausar()


def generar_comando_discord():
    ip_minecraft = generar_ip_minecraft()
    
    if not ip_minecraft:
        return None
    
    return f"/minecraft_start ip:{ip_minecraft}"


def mostrar_comando_sugerido():
    """Muestra el comando sugerido para usar en Discord"""
    utils.limpiar_pantalla()
    print("\n" + m("─" * 50))
    print(mb("COMANDO SUGERIDO PARA DISCORD"))
    print(m("─" * 50) + "\n")
    
    comando = generar_comando_discord()
    
    if comando:
        print(verde("✓ Servidor Minecraft detectado\n"))
        print("Usa este comando en Discord:\n")
        print(f"  {comando}\n")
        
        print("El bot:")
        print("  • Inicia el Codespace si está detenido")
        print("  • Monitorea el servidor cada minuto")
        print("  • Te notifica cuando cambie el estado\n")
        
        try:
            import pyperclip
            if utils.confirmar("¿Copiar comando?"):
                pyperclip.copy(comando)
                print(verde("\n✓ Comando copiado"))
                utils.logger.info(f"Comando copiado: {comando}")
        except ImportError:
            pass
        except Exception as e:
            utils.logger.warning(f"No se pudo copiar: {e}")
    else:
        print(amarillo("⚠ Servidor Minecraft no detectado\n"))
        print("Opciones:\n")
        print("1. Si el servidor NO está corriendo:")
        print("   • Inicia tu servidor primero")
        
        print("\n2. Comando básico en Discord:")
        print("   /minecraft_start")
        
        ip = obtener_ip_codespace()
        if ip:
            print(f"\n3. Tu IP actual: {ip}")
            if ':' not in ip:
                print(f"   Prueba: /minecraft_start ip:{ip}:25565")
    
    print("\n" + m("─" * 50))
    utils.pausar()


def verificar_java_corriendo():
    try:
        result = subprocess.run(
            ["pgrep", "-f", "java"],
            capture_output=True,
            timeout=2
        )
        
        esta_corriendo = result.returncode == 0
        
        if esta_corriendo:
            utils.logger.info("Proceso Java detectado (probablemente Minecraft)")
        
        return esta_corriendo
        
    except Exception as e:
        utils.logger.warning(f"No se pudo verificar proceso Java: {e}")
        return False


def obtener_uso_recursos():
    recursos = {}
    
    try:
        result = subprocess.run(
            ["uptime"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            recursos['uptime'] = result.stdout.strip()
        
        result = subprocess.run(
            ["free", "-h"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            recursos['memoria'] = result.stdout.strip()
        
        result = subprocess.run(
            ["df", "-h", "/"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            recursos['disco'] = result.stdout.strip()
        
    except Exception as e:
        utils.logger.error(f"Error obteniendo recursos: {e}")
    
    return recursos


__all__ = [
    'obtener_nombre_codespace',
    'leer_configuracion_msx',
    'obtener_ip_codespace',
    'obtener_ip_desde_playit',
    'obtener_ip_desde_tailscale',
    'obtener_ip_desde_zerotier',
    'obtener_puertos_abiertos',
    'detectar_servidor_minecraft',
    'generar_ip_minecraft',
    'verificar_configuracion_discord',
    'mostrar_info_conexion',
    'generar_comando_discord',
    'mostrar_comando_sugerido',
    'verificar_java_corriendo',
    'obtener_uso_recursos'
]
