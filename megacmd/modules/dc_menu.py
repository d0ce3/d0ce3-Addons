import os
import subprocess
import time

DISCORD_BOT_INVITE_URL = "https://discord.com/oauth2/authorize?client_id=1331828744985509959&permissions=8&scope=bot%20applications.commands"

utils = CloudModuleLoader.load_module("utils")
config = CloudModuleLoader.load_module("config")
logger = CloudModuleLoader.load_module("logger")

MORADO = "\033[95m"
VERDE = "\033[92m"
ROJO = "\033[91m"
AMARILLO = "\033[93m"
AZUL = "\033[94m"
CIAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

def m(texto):
    return f"{MORADO}{texto}{RESET}"

def mb(texto):
    return f"{BOLD}{MORADO}{texto}{RESET}"

def verde(texto):
    return f"{VERDE}{texto}{RESET}"

def rojo(texto):
    return f"{ROJO}{texto}{RESET}"

def amarillo(texto):
    return f"{AMARILLO}{texto}{RESET}"

def azul(texto):
    return f"{AZUL}{texto}{RESET}"

def _auto_configurar_web_server():
    from auto_webserver_setup import auto_configurar_web_server
    auto_configurar_web_server()

def _cargar_discord_queue():
    try:
        discord_queue = CloudModuleLoader.load_module("discord_queue")
        if discord_queue is not None and hasattr(discord_queue, 'queue_instance'):
            return discord_queue
        return None
    except Exception:
        return None

def menu_principal_discord():
    while True:
        utils.limpiar_pantalla()
        
        print("\n" + m("─" * 50))
        print(mb("INTEGRACIÓN DISCORD - d0ce3|tools Bot"))
        print(m("─" * 50))
        
        user_id = config.CONFIG.get("discord_user_id") or os.getenv("DISCORD_USER_ID")
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        
        eventos_pendientes = 0
        discord_queue_disponible = False
        discord_queue = _cargar_discord_queue()
        
        if discord_queue:
            try:
                stats = discord_queue.queue_instance.get_stats()
                eventos_pendientes = stats.get('pending', 0)
                discord_queue_disponible = True
            except Exception:
                pass
        
        if user_id and webhook_url:
            print(verde("\n✓ Configuración completa"))
            if discord_queue_disponible and eventos_pendientes > 0:
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
        if discord_queue_disponible:
            print(m("│ 5. Ver estadísticas de la cola                 │"))
            print(m("│ 6. Gestión de eventos                          │"))
        else:
            print(m("│ 5. [Sistema de cola no disponible]            │"))
            print(m("│ 6. [Sistema de cola no disponible]            │"))
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
                if discord_queue_disponible:
                    mostrar_estadisticas_cola()
                else:
                    print(amarillo("\n⚠ Sistema de cola no disponible"))
                    utils.pausar()
            elif seleccion == 6:
                if discord_queue_disponible:
                    menu_gestion_eventos()
                else:
                    print(amarillo("\n⚠ Sistema de cola no disponible"))
                    utils.pausar()
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
    utils.limpiar_pantalla()
    
    print("\n" + m("─" * 50))
    print(mb("CONFIGURACIÓN DE INTEGRACIÓN DISCORD"))
    print(m("─" * 50) + "\n")
    
    user_id_actual = config.CONFIG.get("discord_user_id") or os.getenv("DISCORD_USER_ID")
    
    if user_id_actual:
        print(f"User ID configurado: {verde(user_id_actual)}\n")
        if not utils.confirmar("¿Cambiar User ID?"):
            user_id = user_id_actual
        else:
            user_id = _solicitar_user_id()
    else:
        print("No hay User ID configurado.\n")
        user_id = _solicitar_user_id()
    
    if not user_id:
        print(rojo("\nConfiguración cancelada"))
        utils.pausar()
        return
    
    config.set("discord_user_id", user_id)
    
    webhook_url = _detectar_webhook_url()
    
    print("\n" + m("─" * 50))
    print(mb("APLICANDO CONFIGURACIÓN"))
    print(m("─" * 50) + "\n")
    
    print("Configurando variables de entorno...\n")
    
    exito = _configurar_variables_permanentes(user_id, webhook_url)
    
    if exito:
        print(verde("\n✓ Configuración completa"))
        print("\n" + mb("Resumen:"))
        print(f"  Discord User ID: {user_id}")
        print(f"  Bot Webhook:     {webhook_url}")
        print("\n" + verde("✓ Notificaciones de backup activadas"))
        print(verde("✓ Sistema de cola iniciado"))
        
        try:
            if logger and hasattr(logger, 'info'):
                logger.info(f"Integración Discord configurada - User ID: {user_id}")
        except:
            pass
        
        _auto_configurar_web_server()
    else:
        print(f"{AMARILLO}\n⚠ Error al guardar configuración{RESET}")
        print("Configura manualmente con:")
        print(f"  export DISCORD_USER_ID='{user_id}'")
        print(f"  export DISCORD_WEBHOOK_URL='{webhook_url}'")
    
    utils.pausar()

def _solicitar_user_id():
    print(mb("Cómo obtener tu Discord User ID:"))
    print("  1. Abre Discord")
    print("  2. Configuración → Avanzado → Modo Desarrollador " + verde("(Activar)"))
    print("  3. Clic derecho en tu perfil → " + verde("Copiar ID de usuario"))
    print()
    
    while True:
        nuevo_id = input(m("Tu Discord User ID: ")).strip()
        
        if not nuevo_id:
            if utils.confirmar("\n¿Cancelar configuración?"):
                return None
            continue
        
        if nuevo_id.isdigit() and len(nuevo_id) >= 17:
            return nuevo_id
        else:
            print(rojo("\n✗ ID inválido"))
            print("  Debe ser solo números (mín. 17 dígitos)")
            print(f"  Ejemplo: {amarillo('331904820590018562')}\n")

def _detectar_webhook_url():
    render_service = os.getenv("RENDER_SERVICE_NAME")
    render_external_url = os.getenv("RENDER_EXTERNAL_URL")
    
    if render_external_url:
        return f"{render_external_url}/webhook/megacmd"
    elif render_service:
        return f"https://{render_service}.onrender.com/webhook/megacmd"
    
    railway_static_url = os.getenv("RAILWAY_STATIC_URL")
    railway_public_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    
    if railway_public_domain:
        return f"https://{railway_public_domain}/webhook/megacmd"
    elif railway_static_url:
        return f"{railway_static_url}/webhook/megacmd"
    
    return "https://doce-bt.onrender.com/webhook/megacmd"

def _configurar_variables_permanentes(user_id, webhook_url):
    try:
        bashrc_path = os.path.expanduser("~/.bashrc")
        
        if os.path.exists(bashrc_path):
            with open(bashrc_path, 'r') as f:
                contenido = f.read()
        else:
            contenido = ""
        
        lineas = contenido.split('\n')
        tiene_user_id = any('DISCORD_USER_ID' in linea for linea in lineas)
        tiene_webhook = any('DISCORD_WEBHOOK_URL' in linea for linea in lineas)
        
        nuevas_lineas = []
        
        if not tiene_user_id:
            nuevas_lineas.append(f'export DISCORD_USER_ID="{user_id}"')
        
        if not tiene_webhook:
            nuevas_lineas.append(f'export DISCORD_WEBHOOK_URL="{webhook_url}"')
        
        if nuevas_lineas:
            with open(bashrc_path, 'a') as f:
                f.write("\n# d0ce3|tools Discord Integration\n")
                for linea in nuevas_lineas:
                    f.write(linea + "\n")
            print(verde("✓ Variables agregadas a ~/.bashrc"))
        else:
            print(verde("✓ Variables ya configuradas"))
        
        os.environ["DISCORD_USER_ID"] = user_id
        os.environ["DISCORD_WEBHOOK_URL"] = webhook_url
        
        print(verde("✓ Variables exportadas en sesión actual"))
        
        return True
        
    except Exception as e:
        print(rojo(f"\n✗ Error configurando variables: {e}"))
        try:
            if logger and hasattr(logger, 'error'):
                logger.error(f"Error configurando variables permanentes: {e}")
        except:
            pass
        return False

def mostrar_estadisticas_cola():
    utils.limpiar_pantalla()
    
    print("\n" + m("─" * 50))
    print(mb("ESTADÍSTICAS DE LA COLA DE EVENTOS"))
    print(m("─" * 50) + "\n")
    
    try:
        discord_queue = _cargar_discord_queue()
        
        if discord_queue is None:
            print(rojo("✗ Sistema de cola no disponible\n"))
            print("El módulo discord_queue no se pudo cargar.\n")
            utils.pausar()
            return
        
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
        try:
            if logger and hasattr(logger, 'error'):
                logger.error(f"Error en estadísticas de cola: {e}")
        except:
            pass
    
    utils.pausar()

def menu_gestion_eventos():
    while True:
        utils.limpiar_pantalla()
        
        print("\n" + m("─" * 50))
        print(mb("GESTIÓN DE EVENTOS"))
        print(m("─" * 50))
        
        discord_queue = _cargar_discord_queue()
        
        if discord_queue:
            try:
                stats = discord_queue.queue_instance.get_stats()
                print(f"\nPendientes: {amarillo(str(stats['pending']))}")
                print(f"Fallidos:   {rojo(str(stats['failed']))}\n")
            except:
                print(rojo("\n✗ Error al cargar estadísticas\n"))
        else:
            print(amarillo("\n⚠ Sistema de cola no disponible\n"))
        
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
    utils.limpiar_pantalla()
    
    print("\n" + m("─" * 50))
    print(mb("EVENTOS FALLIDOS"))
    print(m("─" * 50) + "\n")
    
    try:
        discord_queue = _cargar_discord_queue()
        
        if discord_queue is None:
            print(rojo("✗ Sistema de cola no disponible\n"))
            utils.pausar()
            return
        
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
    try:
        discord_queue = _cargar_discord_queue()
        
        if discord_queue is None:
            print(rojo("\n✗ Sistema de cola no disponible"))
            utils.pausar()
            return
        
        event_id = input(m("ID del evento a reintentar: ")).strip()
        
        if not event_id or not event_id.isdigit():
            print(rojo("\n✗ ID inválido"))
            utils.pausar()
            return
        
        discord_queue.queue_instance.retry_failed_event(int(event_id))
        
        print(verde(f"\n✓ Evento {event_id} marcado para reintentar"))
        try:
            if logger and hasattr(logger, 'info'):
                logger.info(f"Evento {event_id} reintentado manualmente")
        except:
            pass
    
    except Exception as e:
        print(rojo(f"\n✗ Error: {e}"))
    
    utils.pausar()

def _limpiar_eventos_antiguos():
    print("\n" + m("─" * 50))
    print(mb("LIMPIAR EVENTOS ANTIGUOS"))
    print(m("─" * 50) + "\n")
    
    print("Esto eliminará eventos procesados con más de 7 días.\n")
    
    if not utils.confirmar("¿Continuar?"):
        return
    
    try:
        discord_queue = _cargar_discord_queue()
        
        if discord_queue is None:
            print(rojo("\n✗ Sistema de cola no disponible"))
            utils.pausar()
            return
        
        eliminados = discord_queue.queue_instance.cleanup_old_events(days=7)
        
        print(verde(f"\n✓ {eliminados} evento(s) eliminado(s)"))
        try:
            if logger and hasattr(logger, 'info'):
                logger.info(f"Limpieza de eventos: {eliminados} eliminados")
        except:
            pass
    
    except Exception as e:
        print(rojo(f"\n✗ Error: {e}"))
    
    utils.pausar()

def _ver_eventos_pendientes():
    utils.limpiar_pantalla()
    
    print("\n" + m("─" * 50))
    print(mb("EVENTOS PENDIENTES"))
    print(m("─" * 50) + "\n")
    
    try:
        discord_queue = _cargar_discord_queue()
        
        if discord_queue is None:
            print(rojo("✗ Sistema de cola no disponible\n"))
            utils.pausar()
            return
        
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

__all__ = [
    'menu_principal_discord',
    'mostrar_info_bot',
    'configurar_integracion_completa',
    'mostrar_estadisticas_cola',
    'menu_gestion_eventos',
    'DISCORD_BOT_INVITE_URL'
]
