import os

# URL de invitación del bot
DISCORD_BOT_INVITE_URL = "https://discord.com/oauth2/authorize?client_id=1331828744985509959&permissions=8&scope=bot%20applications.commands"

utils = CloudModuleLoader.load_module("utils")
config = CloudModuleLoader.load_module("config")


def menu_principal_discord():
    """Menú principal unificado para todas las opciones de Discord"""
    while True:
        utils.limpiar_pantalla()
        
        print("\n" + "="*70)
        print("🤖 INTEGRACIÓN DISCORD - d0ce3|tools Bot")
        print("="*70 + "\n")
        
        # Mostrar estado rápido
        user_id = config.CONFIG.get("discord_user_id") or os.getenv("DISCORD_USER_ID")
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        
        if user_id and webhook_url:
            print("✅ Configuración: Completa")
        elif user_id or webhook_url:
            print("⚠️  Configuración: Incompleta")
        else:
            print("❌ Configuración: Pendiente")
        
        print()
        print("="*70)
        
        opciones = [
            "📋 ¿Qué es el bot Discord? (Info completa)",
            "⚙️  Configurar Discord User ID",
            "📡 Ayuda para configurar Webhook",
            "🌐 Ver información de conexión Codespace",
            "💡 Ver comando sugerido para Discord",
            "📊 Ver estado de configuración",
            "🔗 Copiar enlace de invitación",
            "🌍 Abrir enlace en navegador",
            "🔙 Volver al menú principal"
        ]
        
        print("\nOpciones:")
        for i, opcion in enumerate(opciones, 1):
            print(f" {i}. {opcion}")
        
        print()
        
        try:
            seleccion = input("> ").strip()
            
            if not seleccion:
                break
            
            seleccion = int(seleccion)
            
            if seleccion == 1:
                mostrar_info_discord_completa()
            elif seleccion == 2:
                configurar_discord_user_id()
            elif seleccion == 3:
                mostrar_ayuda_webhook()
            elif seleccion == 4:
                _mostrar_info_conexion_wrapper()
            elif seleccion == 5:
                _mostrar_comando_sugerido_wrapper()
            elif seleccion == 6:
                _mostrar_estado_configuracion()
            elif seleccion == 7:
                _copiar_enlace_portapapeles()
            elif seleccion == 8:
                _abrir_enlace_navegador()
            elif seleccion == 9:
                break
            else:
                utils.print_warning("Opción inválida")
                utils.pausar()
                
        except ValueError:
            utils.print_warning("Ingresa un número válido")
            utils.pausar()
        except KeyboardInterrupt:
            print("\n")
            break


def mostrar_info_discord_completa():
    """Muestra información completa sobre la integración con Discord"""
    utils.limpiar_pantalla()
    
    print("\n" + "="*70)
    print("🤖 ¿QUÉ ES d0ce3|tools Bot?")
    print("="*70 + "\n")
    
    print("📌 Descripción:")
    print("   Un bot de Discord que te permite controlar tu Codespace desde Discord,")
    print("   recibir notificaciones de backups y monitorear tu servidor Minecraft.\n")
    
    print("✨ Características principales:")
    print("   • Iniciar/Detener Codespace desde Discord")
    print("   • Monitoreo automático de servidor Minecraft")
    print("   • Notificaciones de errores en backups automáticos de MEGACMD")
    print("   • Sistema de permisos multiusuario")
    print("   • Consultar estado en tiempo real")
    print("   • Compartir acceso con amigos/colaboradores\n")
    
    print("🔗 Enlace de invitación:")
    print(f"   {DISCORD_BOT_INVITE_URL}\n")
    
    print("📋 Pasos para configurar (rápido):")
    print("   1. Invita el bot a tu servidor de Discord")
    print("   2. En Discord, usa /setup con tu token de GitHub")
    print("   3. Usa /vincular para conectar este Codespace")
    print("   4. ¡Listo! Ya podés usar los comandos\n")
    
    print("⚙️ Configurar notificaciones de backups:")
    print("   1. Obtén tu Discord User ID (Modo Desarrollador → Copiar ID)")
    print("   2. Configúralo desde el menú principal")
    print("   3. Exporta variables de entorno (ver 'Ayuda Webhook')\n")
    
    print("💡 Comandos disponibles en Discord:")
    print("\n   Control de Codespace:")
    print("   • /start                  - Inicia tu Codespace")
    print("   • /stop                   - Detiene tu Codespace")
    print("   • /status                 - Consulta estado del Codespace")
    
    print("\n   Minecraft:")
    print("   • /minecraft_start [ip]   - Inicia y monitorea Minecraft")
    print("   • /minecraft_stop         - Detiene monitoreo")
    print("   • /minecraft_status <ip>  - Consulta servidor Minecraft")
    
    print("\n   Configuración:")
    print("   • /setup                  - Configura tu token GitHub")
    print("   • /vincular [codespace]   - Vincula tu Codespace")
    print("   • /refrescar              - Renueva tu token")
    
    print("\n   Permisos:")
    print("   • /permitir @usuario      - Otorga acceso a otro usuario")
    print("   • /revocar @usuario       - Revoca acceso")
    print("   • /permisos               - Lista usuarios autorizados")
    
    print("\n   Información:")
    print("   • /info                   - Tu configuración actual")
    print("   • /ayuda                  - Lista todos los comandos")
    
    print("\n" + "="*70)
    utils.pausar()


def configurar_discord_user_id():
    """Configura el Discord User ID del usuario"""
    utils.limpiar_pantalla()
    print("\n" + "="*60)
    print("⚙️ CONFIGURAR DISCORD USER ID")
    print("="*60 + "\n")
    
    user_id_actual = config.CONFIG.get("discord_user_id", "")
    
    if user_id_actual:
        print(f"📌 User ID actual: {user_id_actual}\n")
    
    print("🔍 Cómo obtener tu Discord User ID:")
    print("   1. Abre Discord")
    print("   2. Ve a Configuración → Avanzado")
    print("   3. Activa 'Modo Desarrollador'")
    print("   4. Clic derecho en tu perfil → Copiar ID de usuario\n")
    
    print("💡 Ejemplo de ID: 123456789012345678 (17-19 dígitos)\n")
    
    nuevo_id = input("Ingresá tu Discord User ID (Enter para cancelar): ").strip()
    
    if nuevo_id:
        if nuevo_id.isdigit() and len(nuevo_id) >= 17:
            config.set("discord_user_id", nuevo_id)
            utils.print_msg(f"Discord User ID guardado: {nuevo_id}")
            utils.logger.info(f"Discord User ID configurado: {nuevo_id}")
            
            print("\n📋 Siguientes pasos:")
            print("\n1. Configura la variable de entorno (temporal):")
            print(f"   export DISCORD_USER_ID='{nuevo_id}'")
            
            print("\n2. Para hacerla permanente, agregá a ~/.bashrc:")
            print(f"   echo 'export DISCORD_USER_ID=\"{nuevo_id}\"' >> ~/.bashrc")
            print("   source ~/.bashrc")
            
            print("\n3. Configura también el webhook URL:")
            print("   (Ver 'Ayuda Webhook' en el menú)")
            
        else:
            utils.print_error("ID inválido")
            print("   • Debe ser solo números")
            print("   • Debe tener al menos 17 dígitos")
            print("   • Ejemplo válido: 123456789012345678")
    else:
        print("\n❌ Cancelado")
    
    utils.pausar()


def mostrar_ayuda_webhook():
    """Muestra ayuda para configurar el webhook"""
    utils.limpiar_pantalla()
    print("\n" + "="*70)
    print("📡 CONFIGURAR WEBHOOK PARA NOTIFICACIONES")
    print("="*70 + "\n")
    
    print("Para recibir notificaciones de errores en Discord, necesitás")
    print("configurar la URL del webhook del bot.\n")
    
    print("🔧 Configuración según tu despliegue:")
    print("\n1. Bot en Render:")
    print("   export DISCORD_WEBHOOK_URL='https://tu-app.onrender.com/webhook/megacmd'")
    
    print("\n2. Bot en Railway:")
    print("   export DISCORD_WEBHOOK_URL='https://tu-app.up.railway.app/webhook/megacmd'")
    
    print("\n3. Bot local (desarrollo):")
    print("   export DISCORD_WEBHOOK_URL='http://localhost:10000/webhook/megacmd'")
    
    print("\n4. Otra plataforma:")
    print("   export DISCORD_WEBHOOK_URL='https://tu-dominio.com/webhook/megacmd'")
    
    print("\n💾 Para hacerlo permanente:")
    print("   echo 'export DISCORD_WEBHOOK_URL=\"https://...\"' >> ~/.bashrc")
    print("   source ~/.bashrc")
    
    print("\n✅ Variables necesarias (resumen):")
    print("   • DISCORD_USER_ID     - Tu ID de usuario de Discord")
    print("   • DISCORD_WEBHOOK_URL - URL del bot para recibir notificaciones")
    print("   • CODESPACE_NAME      - Se detecta automáticamente")
    
    print("\n🧪 Probar notificaciones:")
    print("   Desde Python en este Codespace:")
    print("   >>> from modules import discord_notifier")
    print("   >>> discord_notifier.probar_notificacion()")
    
    print("\n📌 Tipos de notificaciones:")
    print("   • backup_compression - Error al comprimir backup")
    print("   • backup_upload      - Error al subir a MEGA")
    print("   • backup_general     - Error general en backup")
    
    print("\n" + "="*70)
    utils.pausar()


def _mostrar_info_conexion_wrapper():
    """Wrapper para llamar a dc_codespace.mostrar_info_conexion()"""
    try:
        dc_codespace = CloudModuleLoader.load_module("dc_codespace")
        if dc_codespace:
            dc_codespace.mostrar_info_conexion()
        else:
            utils.print_error("No se pudo cargar módulo dc_codespace")
            utils.pausar()
    except Exception as e:
        utils.print_error(f"Error: {e}")
        utils.pausar()


def _mostrar_comando_sugerido_wrapper():
    """Wrapper para llamar a dc_codespace.mostrar_comando_sugerido()"""
    try:
        dc_codespace = CloudModuleLoader.load_module("dc_codespace")
        if dc_codespace:
            dc_codespace.mostrar_comando_sugerido()
        else:
            utils.print_error("No se pudo cargar módulo dc_codespace")
            utils.pausar()
    except Exception as e:
        utils.print_error(f"Error: {e}")
        utils.pausar()


def _mostrar_estado_configuracion():
    """Muestra el estado actual de la configuración de Discord"""
    utils.limpiar_pantalla()
    print("\n" + "="*70)
    print("📊 ESTADO DE CONFIGURACIÓN DISCORD")
    print("="*70 + "\n")
    
    # User ID en config
    user_id = config.CONFIG.get("discord_user_id")
    if user_id:
        utils.print_msg(f"Discord User ID (config): {user_id}", "✓")
    else:
        utils.print_warning("Discord User ID no configurado en config")
    
    # Variable de entorno User ID
    env_user_id = os.getenv("DISCORD_USER_ID")
    if env_user_id:
        utils.print_msg(f"DISCORD_USER_ID (env): {env_user_id}", "✓")
    else:
        utils.print_warning("Variable DISCORD_USER_ID no configurada")
    
    # Webhook URL
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if webhook_url:
        # Mostrar solo parte de la URL por seguridad
        url_mostrar = webhook_url[:30] + "..." if len(webhook_url) > 30 else webhook_url
        utils.print_msg(f"Webhook URL: {url_mostrar}", "✓")
    else:
        utils.print_warning("Variable DISCORD_WEBHOOK_URL no configurada")
    
    # Codespace name
    codespace_name = os.getenv("CODESPACE_NAME")
    if codespace_name:
        utils.print_msg(f"Codespace: {codespace_name}", "✓")
    else:
        utils.print_warning("CODESPACE_NAME no detectado (¿no estás en Codespace?)")
    
    print("\n" + "="*70)
    
    # Resumen
    if (user_id or env_user_id) and webhook_url:
        print("\n✅ Configuración completa - Las notificaciones funcionarán")
    else:
        print("\n⚠️  Configuración incompleta")
        print("\n💡 Para configurar:")
        print("   1. Usa 'Configurar Discord User ID' del menú")
        print("   2. Agrega las variables de entorno (ver 'Ayuda Webhook')")
    
    utils.pausar()


def _copiar_enlace_portapapeles():
    """Intenta copiar el enlace al portapapeles"""
    try:
        import pyperclip
        pyperclip.copy(DISCORD_BOT_INVITE_URL)
        utils.print_msg("Enlace copiado al portapapeles!")
        print(f"\n   {DISCORD_BOT_INVITE_URL}")
    except ImportError:
        utils.print_warning("pyperclip no instalado")
        print(f"\n   Enlace: {DISCORD_BOT_INVITE_URL}")
        print("\n   Instalá pyperclip con: pip install pyperclip")
    except Exception as e:
        utils.print_warning(f"No se pudo copiar: {e}")
        print(f"\n   Enlace: {DISCORD_BOT_INVITE_URL}")
    utils.pausar()


def _abrir_enlace_navegador():
    """Intenta abrir el enlace en el navegador"""
    try:
        import webbrowser
        webbrowser.open(DISCORD_BOT_INVITE_URL)
        utils.print_msg("Abriendo navegador...")
        print(f"\n   URL: {DISCORD_BOT_INVITE_URL}")
    except Exception as e:
        utils.print_warning(f"No se pudo abrir el navegador: {e}")
        print(f"\n   Enlace: {DISCORD_BOT_INVITE_URL}")
    utils.pausar()


# Funciones exportadas
__all__ = [
    'menu_principal_discord',
    'mostrar_info_discord_completa',
    'configurar_discord_user_id',
    'mostrar_ayuda_webhook',
    'DISCORD_BOT_INVITE_URL'
]