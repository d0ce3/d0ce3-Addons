"""
Módulo de menú para integración con Discord
Maneja la UI y presentación de información relacionada con el bot de Discord
"""
import os
import subprocess

# URL de invitación del bot
DISCORD_BOT_INVITE_URL = "https://discord.com/oauth2/authorize?client_id=1331828744985509959&permissions=8&scope=bot%20applications.commands"

utils = CloudModuleLoader.load_module("utils")
config = CloudModuleLoader.load_module("config")

# Colores del tema (mismo que menu.py)
MORADO = "\033[95m"
VERDE = "\033[92m"
ROJO = "\033[91m"
AMARILLO = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

def m(texto):
    """Texto en morado"""
    return f"{MORADO}{texto}{RESET}"

def mb(texto):
    """Texto en morado bold"""
    return f"{BOLD}{MORADO}{texto}{RESET}"

def verde(texto):
    """Texto en verde"""
    return f"{VERDE}{texto}{RESET}"

def rojo(texto):
    """Texto en rojo"""
    return f"{ROJO}{texto}{RESET}"


def menu_principal_discord():
    """Menú principal unificado para Discord"""
    while True:
        utils.limpiar_pantalla()
        
        print("\n" + m("─" * 50))
        print(mb("INTEGRACIÓN DISCORD - d0ce3|tools Bot"))
        print(m("─" * 50))
        
        # Estado rápido
        user_id = config.CONFIG.get("discord_user_id") or os.getenv("DISCORD_USER_ID")
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        
        if user_id and webhook_url:
            print(verde("\n✓ Configuración completa"))
        elif user_id or webhook_url:
            print(f"{AMARILLO}\n⚠ Configuración incompleta{RESET}")
        else:
            print(rojo("\n✗ Sin configurar"))
        
        print()
        print(m("┌────────────────────────────────────────────────┐"))
        print(m("│ 1. Información del bot                         │"))
        print(m("│ 2. Configurar integración                      │"))
        print(m("│ 3. Ver información de conexión                 │"))
        print(m("│ 4. Comando sugerido para Discord               │"))
        print(m("│ 5. Volver                                      │"))
        print(m("└────────────────────────────────────────────────┘"))
        
        print()
        
        try:
            seleccion = input(m("Opción: ")).strip()
            
            if not seleccion:
                break
            
            seleccion = int(seleccion)
            
            if seleccion == 1:
                mostrar_info_bot()
            elif seleccion == 2:
                configurar_integracion_completa()
            elif seleccion == 3:
                _mostrar_info_conexion_wrapper()
            elif seleccion == 4:
                _mostrar_comando_sugerido_wrapper()
            elif seleccion == 5:
                break
            else:
                print(f"{AMARILLO}Opción inválida{RESET}")
                utils.pausar()
                
        except ValueError:
            print(f"{AMARILLO}Ingresa un número válido{RESET}")
            utils.pausar()
        except KeyboardInterrupt:
            print("\n")
            break


def mostrar_info_bot():
    """Muestra información completa del bot"""
    utils.limpiar_pantalla()
    
    print("\n" + m("─" * 50))
    print(mb("¿QUÉ ES d0ce3|tools Bot?"))
    print(m("─" * 50) + "\n")
    
    print("Un bot de Discord para controlar tu Codespace desde Discord,")
    print("recibir notificaciones de backups y monitorear Minecraft.\n")
    
    print(mb("Características:"))
    print("  • Iniciar/Detener Codespace desde Discord")
    print("  • Monitoreo automático de servidor Minecraft")
    print("  • Notificaciones de errores en backups")
    print("  • Sistema de permisos multiusuario\n")
    
    print(mb("Enlace de invitación:"))
    print(f"  {DISCORD_BOT_INVITE_URL}\n")
    
    print(mb("Pasos rápidos:"))
    print("  1. Invita el bot a tu servidor (enlace de arriba)")
    print("  2. En Discord: /setup con tu token de GitHub")
    print("  3. En Discord: /vincular para conectar este Codespace")
    print("  4. Aquí: Usa 'Configurar integración' del menú\n")
    
    print(mb("Comandos principales:"))
    print("\n  Control:")
    print("    /start, /stop, /status")
    print("\n  Minecraft:")
    print("    /minecraft_start [ip]")
    print("    /minecraft_status <ip>")
    print("\n  Configuración:")
    print("    /setup, /vincular, /permitir, /info\n")
    
    print(m("─" * 50))
    
    # Abrir navegador
    if utils.confirmar("\n¿Abrir enlace de invitación en navegador?"):
        try:
            import webbrowser
            webbrowser.open(DISCORD_BOT_INVITE_URL)
            print(verde("\n✓ Abriendo navegador..."))
        except:
            print(f"{AMARILLO}\nNo se pudo abrir navegador{RESET}")
            print(f"Enlace: {DISCORD_BOT_INVITE_URL}")
    
    utils.pausar()


def configurar_integracion_completa():
    """Configuración paso a paso completa"""
    utils.limpiar_pantalla()
    
    print("\n" + m("─" * 50))
    print(mb("CONFIGURACIÓN DE INTEGRACIÓN DISCORD"))
    print(m("─" * 50) + "\n")
    
    print("Este asistente te guiará paso a paso para configurar")
    print("la integración completa con Discord.\n")
    
    if not utils.confirmar("¿Continuar?"):
        print(rojo("\nCancelado"))
        utils.pausar()
        return
    
    # Paso 1: User ID
    print("\n" + m("─" * 50))
    print(mb("PASO 1/2 - Discord User ID"))
    print(m("─" * 50) + "\n")
    
    user_id_actual = config.CONFIG.get("discord_user_id", "")
    if user_id_actual:
        print(f"User ID actual: {user_id_actual}\n")
        if not utils.confirmar("¿Cambiar User ID?"):
            user_id = user_id_actual
        else:
            user_id = _solicitar_user_id()
    else:
        user_id = _solicitar_user_id()
    
    if not user_id:
        print(rojo("\nConfiguración cancelada"))
        utils.pausar()
        return
    
    # Guardar User ID
    config.set("discord_user_id", user_id)
    print(verde(f"\n✓ User ID guardado: {user_id}"))
    
    # Paso 2: Webhook URL
    print("\n" + m("─" * 50))
    print(mb("PASO 2/2 - URL del Webhook"))
    print(m("─" * 50) + "\n")
    
    webhook_actual = os.getenv("DISCORD_WEBHOOK_URL", "")
    if webhook_actual:
        print(f"Webhook actual: {webhook_actual}\n")
        if not utils.confirmar("¿Cambiar webhook URL?"):
            webhook_url = webhook_actual
        else:
            webhook_url = _solicitar_webhook_url()
    else:
        webhook_url = _solicitar_webhook_url()
    
    if not webhook_url:
        print(f"{AMARILLO}\nSe omitió la configuración del webhook{RESET}")
        print("Podrás configurarlo después exportando manualmente:")
        print(f"  export DISCORD_WEBHOOK_URL='tu_url_aqui'")
        utils.pausar()
        return
    
    # Configurar variables de entorno permanentemente
    print("\n" + m("─" * 50))
    print(mb("APLICANDO CONFIGURACIÓN"))
    print(m("─" * 50) + "\n")
    
    print("Configurando variables de entorno de forma permanente...\n")
    
    exito = _configurar_variables_permanentes(user_id, webhook_url)
    
    if exito:
        print(verde("\n✓ Configuración completa y permanente"))
        print("\nLas variables están configuradas en ~/.bashrc")
        print("Se cargarán automáticamente en cada inicio.\n")
        
        print(mb("Resumen:"))
        print(f"  User ID: {user_id}")
        print(f"  Webhook: {webhook_url}\n")
        
        print(verde("✓ Notificaciones de backup activadas"))
        utils.logger.info(f"Integración Discord configurada - User ID: {user_id}")
    else:
        print(f"{AMARILLO}\n⚠ Configuración parcial{RESET}")
        print("Deberás exportar manualmente las variables:")
        print(f"  export DISCORD_USER_ID='{user_id}'")
        print(f"  export DISCORD_WEBHOOK_URL='{webhook_url}'")
    
    utils.pausar()


def _solicitar_user_id():
    """Solicita el Discord User ID al usuario"""
    print("Cómo obtener tu Discord User ID:")
    print("  1. Abre Discord")
    print("  2. Configuración → Avanzado → Modo Desarrollador (activar)")
    print("  3. Clic derecho en tu perfil → Copiar ID de usuario\n")
    
    while True:
        nuevo_id = input(m("Discord User ID (Enter para cancelar): ")).strip()
        
        if not nuevo_id:
            return None
        
        if nuevo_id.isdigit() and len(nuevo_id) >= 17:
            return nuevo_id
        else:
            print(rojo("\n✗ ID inválido"))
            print("  • Debe ser solo números")
            print("  • Mínimo 17 dígitos")
            print("  • Ejemplo: 123456789012345678\n")


def _solicitar_webhook_url():
    """Detecta automáticamente la URL del webhook"""
    print("Detectando URL del bot...\n")
    
    # Detectar automáticamente
    webhook_url = _detectar_webhook_url()
    
    if webhook_url:
        print(verde(f"✓ URL detectada: {webhook_url}\n"))
        return webhook_url
    else:
        print(f"{AMARILLO}⚠ No se pudo detectar automáticamente{RESET}\n")
        print("Ingresa la URL manualmente:")
        print("  Render:   https://nombre-app.onrender.com/webhook/megacmd")
        print("  Railway:  https://nombre-app.up.railway.app/webhook/megacmd\n")
        
        webhook_manual = input(m("Webhook URL (Enter para omitir): ")).strip()
        
        if not webhook_manual:
            return None
        
        # Validación básica
        if not (webhook_manual.startswith("http://") or webhook_manual.startswith("https://")):
            print(f"{AMARILLO}\n⚠ URL debe comenzar con http:// o https://{RESET}")
            if utils.confirmar("¿Continuar de todas formas?"):
                return webhook_manual
            return None
        
        return webhook_manual


def _detectar_webhook_url():
    """
    Detecta automáticamente la URL del webhook según el entorno
    
    Returns:
        str: URL detectada o None
    """
    # Detectar Render
    render_service = os.getenv("RENDER_SERVICE_NAME")
    render_external_url = os.getenv("RENDER_EXTERNAL_URL")
    
    if render_external_url:
        # Render proporciona la URL completa
        return f"{render_external_url}/webhook/megacmd"
    elif render_service:
        # Construir URL desde el nombre del servicio
        return f"https://{render_service}.onrender.com/webhook/megacmd"
    
    # Detectar Railway
    railway_static_url = os.getenv("RAILWAY_STATIC_URL")
    railway_public_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    
    if railway_public_domain:
        return f"https://{railway_public_domain}/webhook/megacmd"
    elif railway_static_url:
        return f"{railway_static_url}/webhook/megacmd"
    
    # Hardcoded: Render conocido (Doce-Bt)
    # Esto funciona si el bot está en render.com con el nombre "Doce-Bt"
    return "https://doce-bt.onrender.com/webhook/megacmd"


def _configurar_variables_permanentes(user_id, webhook_url):
    """Configura las variables en ~/.bashrc de forma permanente"""
    try:
        bashrc_path = os.path.expanduser("~/.bashrc")
        
        # Leer contenido actual
        if os.path.exists(bashrc_path):
            with open(bashrc_path, 'r') as f:
                contenido = f.read()
        else:
            contenido = ""
        
        # Verificar si ya existen las variables
        lineas = contenido.split('\n')
        tiene_user_id = any('DISCORD_USER_ID' in linea for linea in lineas)
        tiene_webhook = any('DISCORD_WEBHOOK_URL' in linea for linea in lineas)
        
        # Preparar nuevas líneas
        nuevas_lineas = []
        
        if not tiene_user_id:
            nuevas_lineas.append(f'export DISCORD_USER_ID="{user_id}"')
        
        if not tiene_webhook:
            nuevas_lineas.append(f'export DISCORD_WEBHOOK_URL="{webhook_url}"')
        
        # Si hay algo que agregar
        if nuevas_lineas:
            with open(bashrc_path, 'a') as f:
                f.write("\n# d0ce3|tools Discord Integration\n")
                for linea in nuevas_lineas:
                    f.write(linea + "\n")
            
            print(verde("✓ Variables agregadas a ~/.bashrc"))
        else:
            print(f"{AMARILLO}⚠ Variables ya existen en ~/.bashrc{RESET}")
        
        # Exportar en la sesión actual
        os.environ["DISCORD_USER_ID"] = user_id
        os.environ["DISCORD_WEBHOOK_URL"] = webhook_url
        
        print(verde("✓ Variables exportadas en sesión actual"))
        
        return True
        
    except Exception as e:
        print(rojo(f"\n✗ Error configurando variables: {e}"))
        utils.logger.error(f"Error configurando variables permanentes: {e}")
        return False


def _mostrar_info_conexion_wrapper():
    """Wrapper para llamar a dc_codespace.mostrar_info_conexion()"""
    try:
        dc_codespace = CloudModuleLoader.load_module("dc_codespace")
        if dc_codespace:
            dc_codespace.mostrar_info_conexion()
        else:
            print(rojo("\n✗ Error cargando módulo dc_codespace"))
            utils.pausar()
    except Exception as e:
        print(rojo(f"\n✗ Error: {e}"))
        utils.pausar()


def _mostrar_comando_sugerido_wrapper():
    """Wrapper para llamar a dc_codespace.mostrar_comando_sugerido()"""
    try:
        dc_codespace = CloudModuleLoader.load_module("dc_codespace")
        if dc_codespace:
            dc_codespace.mostrar_comando_sugerido()
        else:
            print(rojo("\n✗ Error cargando módulo dc_codespace"))
            utils.pausar()
    except Exception as e:
        print(rojo(f"\n✗ Error: {e}"))
        utils.pausar()


# Funciones exportadas
__all__ = [
    'menu_principal_discord',
    'mostrar_info_bot',
    'configurar_integracion_completa',
    'DISCORD_BOT_INVITE_URL'
]