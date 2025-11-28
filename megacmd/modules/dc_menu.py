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
logger = CloudModuleLoader.load_module("logger")

# Colores del tema (mismo que menu.py)
MORADO = "\033[95m"
VERDE = "\033[92m"
ROJO = "\033[91m"
AMARILLO = "\033[93m"
AZUL = "\033[94m"
CIAN = "\033[96m"
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

def amarillo(texto):
    """Texto en amarillo"""
    return f"{AMARILLO}{texto}{RESET}"

def azul(texto):
    """Texto en azul"""
    return f"{AZUL}{texto}{RESET}"


def _auto_configurar_web_server():
    """
    Configura automáticamente el servidor web de control de Minecraft
    - Crea start_web_server.sh si no existe
    - Lo agrega a ~/.bashrc para arranque automático
    - Instala Flask si hace falta
    - Inicia el servidor web inmediatamente
    """
    workspace = os.getenv("CODESPACE_VSCODE_FOLDER", "/workspace")
    addon_path = f"{workspace}/d0ce3-Addons"
    sh_path = os.path.join(addon_path, "start_web_server.sh")
    bashrc_path = os.path.expanduser("~/.bashrc")
    bashrc_line = f"cd {addon_path} && nohup bash start_web_server.sh > /tmp/web_server.log 2>&1 &"

    print("\n" + m("─" * 50))
    print(mb("CONFIGURANDO SERVIDOR WEB DE CONTROL"))
    print(m("─" * 50) + "\n")

    try:
        # 1. Crear script si no existe
        if not os.path.exists(sh_path):
            print("📝 Creando start_web_server.sh...")
            with open(sh_path, "w") as f:
                f.write("""#!/bin/bash
# Script de inicio automático del servidor web de control de Minecraft

echo "========================================="
echo "🚀 Iniciando servidor web de control"
echo "========================================="

# Generar token si no existe
if [ -z "$WEB_SERVER_AUTH_TOKEN" ]; then
    export WEB_SERVER_AUTH_TOKEN=$(openssl rand -hex 32)
    echo "🔑 Token generado: $WEB_SERVER_AUTH_TOKEN"
fi

# Puerto
PORT=${PORT:-8080}
echo "📡 Puerto: $PORT"

# Ir al directorio correcto
cd "$(dirname "$0")"

# Instalar Flask si no está
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Instalando Flask..."
    pip3 install flask
fi

# Iniciar servidor en segundo plano
nohup python3 web_server.py > /tmp/web_server.log 2>&1 &

echo "✅ Servidor web iniciado en segundo plano"
echo "📋 Logs en: /tmp/web_server.log"
echo "========================================="
""")
            os.chmod(sh_path, 0o755)
            print(verde("✓ start_web_server.sh creado"))
        else:
            print(verde("✓ start_web_server.sh ya existe"))

        # 2. Agregar al bashrc si no está
        if os.path.exists(bashrc_path):
            with open(bashrc_path, "r") as f:
                bashrc_content = f.read()
            
            if bashrc_line not in bashrc_content:
                print("\n📝 Agregando inicio automático a ~/.bashrc...")
                with open(bashrc_path, "a") as f:
                    f.write("\n# Servidor web de control Minecraft (d0ce3-Addons)\n")
                    f.write(bashrc_line + "\n")
                print(verde("✓ Agregado a ~/.bashrc para arranque automático"))
            else:
                print(verde("✓ Ya está configurado en ~/.bashrc"))
        
        # 3. Verificar/Instalar Flask
        print("\n📦 Verificando Flask...")
        try:
            import flask
            print(verde("✓ Flask ya está instalado"))
        except ImportError:
            print("Instalando Flask...")
            resultado = subprocess.call(["pip3", "install", "flask"], 
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
            if resultado == 0:
                print(verde("✓ Flask instalado correctamente"))
            else:
                print(amarillo("⚠ No se pudo instalar Flask automáticamente"))
                print("  Instálalo manualmente: pip3 install flask")

        # 4. Iniciar el servidor web ahora mismo
        print("\n🚀 Iniciando servidor web...")
        try:
            subprocess.Popen(['bash', sh_path],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            print(verde("\n✓ Servidor web de control iniciado en segundo plano"))
            print(verde("✓ Se iniciará automáticamente en futuros arranques"))
            print("\n⭐ Ya puedes usar /minecraft_start desde Discord")
            print("\n💡 El servidor escucha en puerto 8080")
            print("📋 Ver logs: tail -f /tmp/web_server.log")
            
            logger.log("INFO", "Servidor web de control iniciado automáticamente")
            
        except Exception as e:
            print(rojo(f"\n✗ Error al iniciar el servidor web: {e}"))
            print(f"\n💡 Puedes iniciarlo manualmente con:")
            print(f"   bash {sh_path}")
            logger.log("ERROR", f"Error iniciando servidor web: {e}")
    
    except Exception as e:
        print(rojo(f"\n✗ Error en configuración automática: {e}"))
        print("\n💡 Configuración manual necesaria:")
        print(f"   1. Navega a: {addon_path}")
        print(f"   2. Ejecuta: bash start_web_server.sh")
        logger.log("ERROR", f"Error en auto_configurar_web_server: {e}")


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
        
        # Verificar estado de la cola
        try:
            discord_queue = CloudModuleLoader.load_module("discord_queue")
            stats = discord_queue.queue_instance.get_stats()
            eventos_pendientes = stats.get('pending', 0)
        except:
            eventos_pendientes = 0
        
        if user_id and webhook_url:
            print(verde("\n✓ Configuración completa"))
            if eventos_pendientes > 0:
                print(amarillo(f"  ⚠ {eventos_pendientes} evento(s) pendiente(s)"))
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
        print(m("│ 5. Ver estadísticas de la cola                 │"))
        print(m("│ 6. Gestión de eventos                          │"))
        print(m("│ 7. Volver                                      │"))
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
                mostrar_estadisticas_cola()
            elif seleccion == 6:
                menu_gestion_eventos()
            elif seleccion == 7:
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
    print("  • Notificaciones de backups (éxito/error)")
    print("  • Sistema de permisos multiusuario")
    print("  • Sistema de cola de eventos")
    print("  • Polling cada 30 segundos\n")
    
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
    print("    /mc_start, /mc_stop, /mc_status")
    print("\n  Configuración:")
    print("    /setup, /vincular, /refrescar")
    print("\n  Eventos:")
    print("    /addon_stats - Ver estadísticas del sistema\n")
    
    print(mb("Integración:"))
    print("  • Sistema de cola SQLite local")
    print("  • Exposición vía HTTP (puerto 8080)")
    print("  • El bot hace polling cada 30 segundos")
    print("  • Notificaciones automáticas por DM\n")
    
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
        print(verde("✓ Sistema de cola iniciado"))
        logger.log("INFO", f"Integración Discord configurada - User ID: {user_id}")
        
        # AUTO-CONFIGURACIÓN DEL SERVIDOR WEB
        _auto_configurar_web_server()
        
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
        return f"{render_external_url}/webhook/megacmd"
    elif render_service:
        return f"https://{render_service}.onrender.com/webhook/megacmd"
    
    # Detectar Railway
    railway_static_url = os.getenv("RAILWAY_STATIC_URL")
    railway_public_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    
    if railway_public_domain:
        return f"https://{railway_public_domain}/webhook/megacmd"
    elif railway_static_url:
        return f"{railway_static_url}/webhook/megacmd"
    
    # Hardcoded: Render conocido (Doce-Bt)
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
        logger.log("ERROR", f"Error configurando variables permanentes: {e}")
        return False


def mostrar_estadisticas_cola():
    """Muestra estadísticas detalladas de la cola de eventos"""
    utils.limpiar_pantalla()
    
    print("\n" + m("─" * 50))
    print(mb("ESTADÍSTICAS DE LA COLA DE EVENTOS"))
    print(m("─" * 50) + "\n")
    
    try:
        discord_queue = CloudModuleLoader.load_module("discord_queue")
        stats = discord_queue.queue_instance.get_stats()
        
        print(mb("Eventos:"))
        print(f"  Total:      {stats['total']}")
        print(f"  Pendientes: {amarillo(str(stats['pending']))}")
        print(f"  Procesados: {verde(str(stats['processed']))}")
        print(f"  Fallidos:   {rojo(str(stats['failed']))}\n")
        
        if stats['pending'] > 0:
            print(amarillo(f"⚠ Hay {stats['pending']} evento(s) esperando ser procesados"))
            print("  El bot de Discord debe estar online para procesarlos.\n")
        
        if stats['failed'] > 0:
            print(rojo(f"✗ {stats['failed']} evento(s) fallaron después de 3 intentos"))
            print("  Usa 'Gestión de eventos' para revisar y reintentar.\n")
        
        # Información adicional
        print(mb("Base de datos:"))
        workspace = os.getenv("CODESPACE_VSCODE_FOLDER", "/workspace")
        db_path = os.path.join(workspace, ".discord_events.db")
        
        if os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            size_kb = size_bytes / 1024
            print(f"  Ubicación: {db_path}")
            print(f"  Tamaño:    {size_kb:.2f} KB\n")
        else:
            print(rojo("  ✗ Base de datos no encontrada\n"))
        
    except Exception as e:
        print(rojo(f"✗ Error obteniendo estadísticas: {e}\n"))
        logger.log("ERROR", f"Error en estadísticas de cola: {e}")
    
    utils.pausar()


def menu_gestion_eventos():
    """Menú para gestionar eventos de la cola"""
    while True:
        utils.limpiar_pantalla()
        
        print("\n" + m("─" * 50))
        print(mb("GESTIÓN DE EVENTOS"))
        print(m("─" * 50))
        
        try:
            discord_queue = CloudModuleLoader.load_module("discord_queue")
            stats = discord_queue.queue_instance.get_stats()
            
            print(f"\nPendientes: {amarillo(str(stats['pending']))}")
            print(f"Fallidos:   {rojo(str(stats['failed']))}\n")
        except:
            print(rojo("\n✗ Error al cargar estadísticas\n"))
        
        print(m("┌────────────────────────────────────────────────┐"))
        print(m("│ 1. Ver eventos fallidos                        │"))
        print(m("│ 2. Reintentar evento fallido                   │"))
        print(m("│ 3. Limpiar eventos antiguos (7+ días)         │"))
        print(m("│ 4. Ver todos los eventos pendientes            │"))
        print(m("│ 5. Volver                                      │"))
        print(m("└────────────────────────────────────────────────┘"))
        
        print()
        
        try:
            seleccion = input(m("Opción: ")).strip()
            
            if not seleccion:
                break
            
            seleccion = int(seleccion)
            
            if seleccion == 1:
                _ver_eventos_fallidos()
            elif seleccion == 2:
                _reintentar_evento()
            elif seleccion == 3:
                _limpiar_eventos_antiguos()
            elif seleccion == 4:
                _ver_eventos_pendientes()
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


def _ver_eventos_fallidos():
    """Muestra eventos que fallaron"""
    utils.limpiar_pantalla()
    
    print("\n" + m("─" * 50))
    print(mb("EVENTOS FALLIDOS"))
    print(m("─" * 50) + "\n")
    
    try:
        discord_queue = CloudModuleLoader.load_module("discord_queue")
        eventos = discord_queue.queue_instance.get_failed_events()
        
        if not eventos:
            print(verde("✓ No hay eventos fallidos\n"))
        else:
            for i, evento in enumerate(eventos, 1):
                print(f"{i}. ID: {evento['id']}")
                print(f"   Tipo: {evento['event_type']}")
                print(f"   Usuario: {evento['user_id']}")
                print(f"   Intentos: {evento['attempts']}")
                if evento['error_message']:
                    print(f"   Error: {rojo(evento['error_message'])}")
                print()
    
    except Exception as e:
        print(rojo(f"✗ Error: {e}\n"))
    
    utils.pausar()


def _reintentar_evento():
    """Reintenta un evento fallido"""
    try:
        event_id = input(m("ID del evento a reintentar: ")).strip()
        
        if not event_id or not event_id.isdigit():
            print(rojo("\n✗ ID inválido"))
            utils.pausar()
            return
        
        discord_queue = CloudModuleLoader.load_module("discord_queue")
        discord_queue.queue_instance.retry_failed_event(int(event_id))
        
        print(verde(f"\n✓ Evento {event_id} marcado para reintentar"))
        logger.log("INFO", f"Evento {event_id} reintentado manualmente")
    
    except Exception as e:
        print(rojo(f"\n✗ Error: {e}"))
    
    utils.pausar()


def _limpiar_eventos_antiguos():
    """Limpia eventos procesados antiguos"""
    print("\n" + m("─" * 50))
    print(mb("LIMPIAR EVENTOS ANTIGUOS"))
    print(m("─" * 50) + "\n")
    
    print("Esto eliminará eventos procesados con más de 7 días.\n")
    
    if not utils.confirmar("¿Continuar?"):
        return
    
    try:
        discord_queue = CloudModuleLoader.load_module("discord_queue")
        eliminados = discord_queue.queue_instance.cleanup_old_events(days=7)
        
        print(verde(f"\n✓ {eliminados} evento(s) eliminado(s)"))
        logger.log("INFO", f"Limpieza de eventos: {eliminados} eliminados")
    
    except Exception as e:
        print(rojo(f"\n✗ Error: {e}"))
    
    utils.pausar()


def _ver_eventos_pendientes():
    """Muestra eventos pendientes"""
    utils.limpiar_pantalla()
    
    print("\n" + m("─" * 50))
    print(mb("EVENTOS PENDIENTES"))
    print(m("─" * 50) + "\n")
    
    try:
        discord_queue = CloudModuleLoader.load_module("discord_queue")
        eventos = discord_queue.queue_instance.get_pending_events(limit=20)
        
        if not eventos:
            print(verde("✓ No hay eventos pendientes\n"))
        else:
            for i, evento in enumerate(eventos, 1):
                print(f"{i}. ID: {evento['id']}")
                print(f"   Tipo: {evento['event_type']}")
                print(f"   Usuario: {evento['user_id']}")
                print(f"   Creado: {evento['created_at']}")
                print(f"   Intentos: {evento['attempts']}")
                print()
    
    except Exception as e:
        print(rojo(f"✗ Error: {e}\n"))
    
    utils.pausar()


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
    'mostrar_estadisticas_cola',
    'menu_gestion_eventos',
    'DISCORD_BOT_INVITE_URL'
]
