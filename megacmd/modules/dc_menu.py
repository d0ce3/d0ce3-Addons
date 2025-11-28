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
    work_dir = os.path.expanduser("~/.d0ce3_addons")
    os.makedirs(work_dir, exist_ok=True)
    
    sh_path = os.path.join(work_dir, "start_web_server.sh")
    webserver_path = os.path.join(work_dir, "web_server.py")
    bashrc_path = os.path.expanduser("~/.bashrc")
    bashrc_line = f"[ -f '{sh_path}' ] && nohup bash {sh_path} > /tmp/web_server.log 2>&1 &"

    print("\n" + m("─" * 50))
    print(mb("CONFIGURANDO SERVIDOR WEB DE CONTROL"))
    print(m("─" * 50) + "\n")
    print(f"📂 Instalando en: {work_dir}\n")

    try:
        # Instalar screen si no está
        print("📦 Verificando screen...")
        screen_check = subprocess.run(['which', 'screen'], capture_output=True)
        if screen_check.returncode != 0:
            print("Instalando screen...")
            subprocess.run(['sudo', 'apt-get', 'update', '-qq'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'screen'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(verde("✓ Screen instalado"))
        else:
            print(verde("✓ Screen ya está instalado"))

        print("\n📝 Creando web_server.py...")
        with open(webserver_path, "w") as f:
            f.write('''#!/usr/bin/env python3
from flask import Flask, request, jsonify
import subprocess
import os
import glob
import time

app = Flask(__name__)
PORT = int(os.getenv('PORT', 8080))
AUTH_TOKEN = os.getenv('WEB_SERVER_AUTH_TOKEN', 'default_token')

def find_msx_py():
    matches = glob.glob('/workspaces/*/msx.py')
    return matches[0] if matches else None

def execute_minecraft_command(action):
    try:
        msx_path = find_msx_py()
        if not msx_path:
            return {'error': 'msx.py no encontrado'}
        
        repo_root = os.path.dirname(msx_path)
        
        if action == 'start':
            # Verificar si ya hay una sesión corriendo
            check = subprocess.run(['screen', '-ls'], capture_output=True, text=True)
            if 'minecraft_msx' in check.stdout:
                return {
                    'status': 'info',
                    'message': 'Servidor ya está iniciado'
                }
            
            # Iniciar en screen session
            cmd = f'screen -dmS minecraft_msx bash -c "cd {repo_root} && echo 1 | python3 msx.py"'
            subprocess.Popen(cmd, shell=True, env=os.environ.copy())
            time.sleep(2)
            
            return {
                'status': 'success',
                'action': 'start',
                'message': 'Servidor Minecraft iniciando en screen session "minecraft_msx"',
                'screen_session': 'minecraft_msx'
            }
        
        elif action == 'stop':
            # Intentar enviar comando stop via screen
            check = subprocess.run(['screen', '-ls'], capture_output=True, text=True)
            if 'minecraft_msx' in check.stdout:
                # Si hay screen session, enviar echo 2
                cmd = f'screen -S minecraft_msx -X stuff "2\\n"'
                subprocess.Popen(cmd, shell=True)
            else:
                # Fallback: ejecutar directamente
                cmd = f'cd {repo_root} && echo 2 | python3 msx.py'
                subprocess.Popen(cmd, shell=True, env=os.environ.copy())
            
            time.sleep(2)
            
            return {
                'status': 'success',
                'action': 'stop',
                'message': 'Comando stop enviado al servidor'
            }
        
        elif action == 'status':
            java_check = subprocess.run(
                ['pgrep', '-f', 'java.*forge.*jar'],
                capture_output=True,
                text=True
            )
            running = bool(java_check.stdout.strip())
            pids = java_check.stdout.strip().split('\\n') if running else []
            
            # Verificar screen sessions
            screen_check = subprocess.run(['screen', '-ls'], capture_output=True, text=True)
            has_screen = 'minecraft_msx' in screen_check.stdout
            
            return {
                'status': 'success',
                'running': running,
                'minecraft_pids': pids if running else [],
                'screen_session': 'minecraft_msx' if has_screen else None
            }
        
        else:
            return {'error': f'Acción desconocida: {action}'}
    
    except Exception as e:
        import traceback
        return {
            'error': str(e),
            'traceback': traceback.format_exc()
        }

@app.route('/minecraft/start', methods=['POST'])
def minecraft_start():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token != AUTH_TOKEN:
        return jsonify({'error': 'Unauthorized'}), 401
    
    result = execute_minecraft_command('start')
    if 'error' in result:
        return jsonify(result), 500
    return jsonify(result)

@app.route('/minecraft/stop', methods=['POST'])
def minecraft_stop():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token != AUTH_TOKEN:
        return jsonify({'error': 'Unauthorized'}), 401
    
    result = execute_minecraft_command('stop')
    if 'error' in result:
        return jsonify(result), 500
    return jsonify(result)

@app.route('/minecraft/status', methods=['GET'])
def minecraft_status():
    result = execute_minecraft_command('status')
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health():
    msx_path = find_msx_py()
    return jsonify({
        'status': 'ok',
        'port': PORT,
        'msx_found': msx_path is not None,
        'msx_path': msx_path
    })

if __name__ == '__main__':
    print(f"Servidor web escuchando en puerto {PORT}")
    print(f"Token: {AUTH_TOKEN[:8]}...")
    msx_path = find_msx_py()
    if msx_path:
        print(f"msx.py encontrado: {msx_path}")
    print("Tip: Conecta a la sesión de Minecraft con: screen -r minecraft_msx")
    app.run(host='0.0.0.0', port=PORT)
''')
        os.chmod(webserver_path, 0o755)
        print(verde("✓ web_server.py creado"))

        print("📝 Creando start_web_server.sh...")
        with open(sh_path, "w") as f:
            f.write(f'''#!/bin/bash
WORK_DIR="{work_dir}"
cd "$WORK_DIR"

if pgrep -f "python3.*web_server.py" > /dev/null; then
    echo "⚠ Servidor web ya está corriendo"
    exit 0
fi

if [ -z "$WEB_SERVER_AUTH_TOKEN" ]; then
    export WEB_SERVER_AUTH_TOKEN=$(openssl rand -hex 32)
fi

PORT=${{PORT:-8080}}

if ! python3 -c "import flask" 2>/dev/null; then
    pip3 install flask >/dev/null 2>&1
fi

nohup python3 "$WORK_DIR/web_server.py" > /tmp/web_server.log 2>&1 &

echo "✅ Servidor web iniciado (puerto $PORT)"
''')
        os.chmod(sh_path, 0o755)
        print(verde("✓ start_web_server.sh creado"))

        if os.path.exists(bashrc_path):
            with open(bashrc_path, "r") as f:
                bashrc_content = f.read()
            
            if bashrc_line not in bashrc_content:
                print("\n📝 Agregando inicio automático a ~/.bashrc...")
                with open(bashrc_path, "a") as f:
                    f.write(f"\n# d0ce3-Addons auto-start\n{bashrc_line}\n")
                print(verde("✓ Agregado a ~/.bashrc"))
            else:
                print(verde("✓ Ya configurado en ~/.bashrc"))
        
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
                print(verde("✓ Flask instalado"))
            else:
                print(amarillo("⚠ Instálalo manualmente: pip3 install flask"))

        print("\n🚀 Iniciando servidor web...")
        subprocess.Popen(['bash', sh_path])
        
        print(verde("\n✓ Servidor web configurado e iniciado"))
        print(verde("✓ Se iniciará automáticamente en futuros arranques"))
        print(f"\n📂 Archivos en: {work_dir}")
        print("⭐ Ya puedes usar /minecraft_start desde Discord")
        print("\n💡 Puerto: 8080")
        print("📋 Logs: tail -f /tmp/web_server.log")
        print("🖥️  Consola: screen -r minecraft_msx")
        
        # Intentar hacer el puerto público automáticamente con loop de verificación
        print("\n🌐 Configurando puerto 8080 como público...")
        print("   Esperando que el servidor esté listo...")

        # Esperar hasta que el puerto esté escuchando (máximo 10 segundos)
        import socket
        port_ready = False
        for i in range(10):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', 8080))
                sock.close()
                if result == 0:
                    print(verde(f"   ✓ Puerto 8080 escuchando (después de {i+1}s)"))
                    port_ready = True
                    break
            except:
                pass
            time.sleep(1)
        
        if not port_ready:
            print(amarillo("   ⚠ Puerto 8080 no responde aún, intentando de todas formas..."))

        time.sleep(2)  # Espera adicional por seguridad

        try:
            codespace_name = os.getenv('CODESPACE_NAME')
            
            if codespace_name:
                result = subprocess.run(
                    ['gh', 'codespace', 'ports', 'visibility', '8080:public', '-c', codespace_name],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                if result.returncode == 0:
                    print(verde("✓ Puerto 8080 configurado como público automáticamente"))
                else:
                    error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                    raise Exception(f"gh CLI retornó código {result.returncode}: {error_msg}")
            else:
                raise Exception("CODESPACE_NAME no está definido")

        except Exception as e:
            print(amarillo(f"⚠ No se pudo configurar automáticamente: {str(e)}"))
            print("  Configura manualmente el puerto 8080 como PÚBLICO en:")
            print("  VS Code → Panel PORTS → Click derecho en 8080 → Port Visibility → Public")
            print("\n  O ejecuta manualmente:")
            print(f"  gh codespace ports visibility 8080:public -c $CODESPACE_NAME")
        
        try:
            if logger and hasattr(logger, 'info'):
                logger.info(f"Servidor web instalado en {work_dir}")
        except:
            pass
            
    except Exception as e:
        print(rojo(f"\n✗ Error: {e}"))
        import traceback
        print(traceback.format_exc())


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
    
    print("Este asistente te guiará paso a paso para configurar")
    print("la integración completa con Discord.\n")
    
    if not utils.confirmar("¿Continuar?"):
        print(rojo("\nCancelado"))
        utils.pausar()
        return
    
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
    
    config.set("discord_user_id", user_id)
    print(verde(f"\n✓ User ID guardado: {user_id}"))
    
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
        
        try:
            if logger and hasattr(logger, 'info'):
                logger.info(f"Integración Discord configurada - User ID: {user_id}")
        except:
            pass
        
        _auto_configurar_web_server()
        
    else:
        print(f"{AMARILLO}\n⚠ Configuración parcial{RESET}")
        print("Deberás exportar manualmente las variables:")
        print(f"  export DISCORD_USER_ID='{user_id}'")
        print(f"  export DISCORD_WEBHOOK_URL='{webhook_url}'")
    
    utils.pausar()


def _solicitar_user_id():
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
    print("Detectando URL del bot...\n")
    
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
        
        if not (webhook_manual.startswith("http://") or webhook_manual.startswith("https://")):
            print(f"{AMARILLO}\n⚠ URL debe comenzar con http:// o https://{RESET}")
            if utils.confirmar("¿Continuar de todas formas?"):
                return webhook_manual
            return None
        
        return webhook_manual


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
            print(f"{AMARILLO}⚠ Variables ya existen en ~/.bashrc{RESET}")
        
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
            print("El módulo discord_queue no se pudo cargar.")
            print("Esto puede deberse a problemas de empaquetado.\n")
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
