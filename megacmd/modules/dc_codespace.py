"""
Módulo de lógica para integración Discord + Codespace
Maneja la comunicación entre el Codespace y el bot de Discord
"""
import os
import subprocess

utils = CloudModuleLoader.load_module("utils")
config = CloudModuleLoader.load_module("config")


def obtener_nombre_codespace():
    """
    Obtiene el nombre del Codespace actual
    
    Returns:
        str: Nombre del codespace o None si no se detecta
    """
    codespace_name = os.getenv("CODESPACE_NAME")
    
    if codespace_name:
        utils.logger.info(f"Codespace detectado: {codespace_name}")
        return codespace_name
    
    utils.logger.warning("CODESPACE_NAME no detectado")
    return None


def obtener_ip_codespace():
    """
    Obtiene la IP pública del Codespace
    
    Returns:
        str: IP pública o None si no se puede obtener
    """
    try:
        result = subprocess.run(
            ["curl", "-s", "ifconfig.me"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            ip = result.stdout.strip()
            utils.logger.info(f"IP pública obtenida: {ip}")
            return ip
        
        # Alternativa: usar ipify
        result = subprocess.run(
            ["curl", "-s", "https://api.ipify.org"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            ip = result.stdout.strip()
            utils.logger.info(f"IP pública obtenida (ipify): {ip}")
            return ip
        
        utils.logger.warning("No se pudo obtener IP pública")
        return None
        
    except Exception as e:
        utils.logger.error(f"Error obteniendo IP: {e}")
        return None


def obtener_puertos_abiertos():
    """
    Obtiene los puertos que están escuchando en el Codespace
    
    Returns:
        list: Lista de puertos abiertos
    """
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
    """
    Intenta detectar si hay un servidor de Minecraft corriendo
    
    Returns:
        dict: Información del servidor o None
    """
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
    """
    Genera la IP completa para conectarse al servidor Minecraft
    
    Returns:
        str: IP:puerto o None
    """
    info_servidor = detectar_servidor_minecraft()
    
    if not info_servidor:
        return None
    
    ip = info_servidor.get("ip")
    puerto = info_servidor.get("puerto", 25565)
    
    if not ip:
        return None
    
    # Si es puerto por defecto, no incluirlo
    if puerto == 25565:
        return ip
    else:
        return f"{ip}:{puerto}"


def verificar_configuracion_discord():
    """
    Verifica que la configuración de Discord esté completa
    
    Returns:
        dict: Estado de la configuración
    """
    estado = {
        "user_id_config": bool(config.CONFIG.get("discord_user_id")),
        "user_id_env": bool(os.getenv("DISCORD_USER_ID")),
        "webhook_url": bool(os.getenv("DISCORD_WEBHOOK_URL")),
        "codespace_name": bool(os.getenv("CODESPACE_NAME")),
        "configuracion_completa": False
    }
    
    # Configuración mínima necesaria
    estado["configuracion_completa"] = (
        (estado["user_id_config"] or estado["user_id_env"]) and
        estado["webhook_url"]
    )
    
    return estado


# Colores del tema
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
    
    # Nombre del Codespace
    codespace_name = obtener_nombre_codespace()
    if codespace_name:
        print(verde(f"✓ Codespace: {codespace_name}"))
    else:
        print(amarillo("⚠ Codespace no detectado"))
    
    # IP pública
    print()
    ip = obtener_ip_codespace()
    if ip:
        print(verde(f"✓ IP pública: {ip}"))
    else:
        print(amarillo("⚠ No se pudo obtener IP pública"))
    
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
    """
    Genera el comando de Discord sugerido para iniciar el servidor
    
    Returns:
        str: Comando sugerido o None
    """
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
        
        # Intentar copiar
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
            print(f"   Prueba: /minecraft_start ip:{ip}:25565")
    
    print("\n" + m("─" * 50))
    utils.pausar()


def verificar_java_corriendo():
    """
    Verifica si hay un proceso Java corriendo (probablemente Minecraft)
    
    Returns:
        bool: True si hay Java corriendo
    """
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
    """
    Obtiene información sobre el uso de recursos del sistema
    
    Returns:
        dict: CPU, memoria, disco
    """
    recursos = {}
    
    try:
        # CPU - usar uptime para carga promedio
        result = subprocess.run(
            ["uptime"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            recursos['uptime'] = result.stdout.strip()
        
        # Memoria
        result = subprocess.run(
            ["free", "-h"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            recursos['memoria'] = result.stdout.strip()
        
        # Disco
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


# Funciones exportadas
__all__ = [
    'obtener_nombre_codespace',
    'obtener_ip_codespace',
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