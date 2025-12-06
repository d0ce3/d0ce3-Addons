import os
import subprocess
import time
import socket
import glob
import json
import threading
import re
import requests

WEBSERVER_CONFIG_FILE = os.path.expanduser("~/.d0ce3_addons/webserver_config.json")
TUNNEL_URL_FILE = os.path.expanduser("~/.d0ce3_addons/tunnel_url.txt")
CURRENT_WEBSERVER_VERSION = "1.0.0"

DISCORD_USER_ID = os.getenv("DISCORD_USER_ID")
BOT_WEBHOOK_URL = os.getenv("BOT_WEBHOOK_URL", "https://doce-bt.onrender.com/webhook/tunnel_notify")
BOT_API_URL = os.getenv("BOT_API_URL", "https://doce-bt.onrender.com/api")

DEFAULT_WEBSERVER_CONFIG = {
    "port": 8080,
    "session_name": "msx",
    "auto_public": True,
    "use_cloudflare": True,
    "version": CURRENT_WEBSERVER_VERSION
}

def cargar_webserver_config():
    if os.path.exists(WEBSERVER_CONFIG_FILE):
        try:
            with open(WEBSERVER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for key, value in DEFAULT_WEBSERVER_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except:
            return DEFAULT_WEBSERVER_CONFIG.copy()
    else:
        guardar_webserver_config(DEFAULT_WEBSERVER_CONFIG)
        return DEFAULT_WEBSERVER_CONFIG.copy()

def guardar_webserver_config(config):
    try:
        os.makedirs(os.path.dirname(WEBSERVER_CONFIG_FILE), exist_ok=True)
        with open(WEBSERVER_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False

def ensure_tmux_installed():
    check = subprocess.run(['which', 'tmux'], capture_output=True)
    if check.returncode != 0:
        print("📦 Instalando tmux...")
        try:
            subprocess.run(['sudo', 'apt-get', 'update', '-qq'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', '-qq', 'tmux'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("✓ tmux instalado")
            return True
        except:
            print("✗ No se pudo instalar tmux")
            return False
    return True

def necesita_actualizacion(webserver_config):
    installed_version = webserver_config.get("version", "0.0.0")
    return installed_version != CURRENT_WEBSERVER_VERSION

def limpiar_bashrc_duplicados():
    bashrc_path = os.path.expanduser("~/.bashrc")
    if not os.path.exists(bashrc_path):
        return
    
    try:
        with open(bashrc_path, 'r') as f:
            lines = f.readlines()
        
        new_lines = []
        skip_next = False
        found_webserver = False
        
        for i, line in enumerate(lines):
            if 'd0ce3-Addons auto-start' in line:
                if not found_webserver:
                    new_lines.append(line)
                    found_webserver = True
                skip_next = True
                continue
            
            if skip_next and 'start_web_server.sh' in line:
                if not found_webserver or (found_webserver and 'disown' in line):
                    new_lines.append(line)
                    found_webserver = False
                skip_next = False
                continue
            
            new_lines.append(line)
        
        with open(bashrc_path, 'w') as f:
            f.writelines(new_lines)
    except:
        pass

def get_tunnel_url():
    if os.path.exists(TUNNEL_URL_FILE):
        try:
            with open(TUNNEL_URL_FILE, 'r') as f:
                return f.read().strip()
        except:
            return None
    return None

def get_config_from_bot():
    if not DISCORD_USER_ID:
        return None
    
    try:
        response = requests.get(
            f"{BOT_API_URL}/user/config/{DISCORD_USER_ID}",
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def notify_bot_webhook(tunnel_url, tunnel_type="cloudflare", tunnel_port=8080, voicechat_address=None):
    if not DISCORD_USER_ID:
        return False
    
    try:
        codespace_name = os.getenv("CODESPACE_NAME", "unknown")
        
        payload = {
            "user_id": DISCORD_USER_ID,
            "codespace_name": codespace_name,
            "tunnel_url": tunnel_url,
            "tunnel_port": tunnel_port,
            "tunnel_type": tunnel_type,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        if voicechat_address:
            payload["voicechat_address"] = voicechat_address
        
        response = requests.post(
            BOT_WEBHOOK_URL,
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("notification_sent"):
                print("📨 Bot notificado - Usuario recibirá DM en Discord")
            return True
    except:
        pass
    return False

def auto_configurar_web_server():
    utils = CloudModuleLoader.load_module("utils")
    config = CloudModuleLoader.load_module("config")
    
    webserver_config = cargar_webserver_config()
    
    work_dir = os.path.expanduser("~/.d0ce3_addons")
    sh_path = os.path.join(work_dir, "start_web_server.sh")
    webserver_path = os.path.join(work_dir, "web_server.py")
    tunnel_manager_path = os.path.join(work_dir, "tunnel_manager.py")
    bashrc_path = os.path.expanduser("~/.bashrc")
    bashrc_line = f"[ -f '{sh_path}' ] && (bash {sh_path} > /dev/null 2>&1 &); disown 2>/dev/null"

    print("\n" + "─" * 50)
    print("CONFIGURANDO SERVIDOR WEB DE CONTROL")
    print("─" * 50 + "\n")

    try:
        if not ensure_tmux_installed():
            return False
        
        limpiar_bashrc_duplicados()
        
        todo_instalado = (
            os.path.exists(webserver_path) and
            os.path.exists(sh_path) and
            os.path.exists(tunnel_manager_path)
        )
        
        session_name = webserver_config.get("session_name", "msx")
        port = webserver_config.get("port", 8080)
        use_cloudflare = webserver_config.get("use_cloudflare", True)
        
        check_running = subprocess.run(
            ['tmux', 'has-session', '-t', 'webserver'],
            capture_output=True
        )
        servidor_corriendo = check_running.returncode == 0
        
        if todo_instalado and not necesita_actualizacion(webserver_config):
            if servidor_corriendo:
                print(f"✓ Servidor web ya está configurado y corriendo")
                print(f"💡 Puerto: {port}")
                print(f"📋 Ver logs msx: tmux attach -t msx, con este comando vas a poder acceder a la terminal normalmente")
                print(f" Usa ese comando unicamente si queres ver los logs o interactuar con la terminal.")
                print(f" Si queres salir de la termianal sin detener el servidor, presiona Ctrl+B y luego D.")
                print(f" Tambien creo que no hace falta aclarar, esto unicamente funciona si el servidor de Minecraft fue iniciado desde discord")
                
                if use_cloudflare:
                    tunnel_url = get_tunnel_url()
                    if tunnel_url:
                        print(f"🌐 URL pública: {tunnel_url}")
                        
                        if DISCORD_USER_ID:
                            notify_bot_webhook(tunnel_url, "cloudflare", port)
                    else:
                        print(f"⚠ URL pública no disponible aún")
                
                print()
                return True
        
        if necesita_actualizacion(webserver_config):
            print(f"🔄 Actualizando servidor web ({webserver_config.get('version', '0.0.0')} → {CURRENT_WEBSERVER_VERSION})...\n")
            if servidor_corriendo:
                print(f"🛑 Deteniendo sesión webserver...")
                subprocess.run(['tmux', 'kill-session', '-t', 'webserver'], capture_output=True)
                time.sleep(1)
        else:
            print("📦 Instalando servidor web de control...\n")
        
        os.makedirs(work_dir, exist_ok=True)

        with open(tunnel_manager_path, "w") as f:
            f.write(f'''#!/usr/bin/env python3
import subprocess
import os
import time
import re
import threading
import requests

PORT = {port}
TUNNEL_URL_FILE = "{TUNNEL_URL_FILE}"
DISCORD_USER_ID = os.getenv("DISCORD_USER_ID")
BOT_WEBHOOK_URL = os.getenv("BOT_WEBHOOK_URL", "{BOT_WEBHOOK_URL}")

def install_cloudflared():
    print("🔍 Verificando cloudflared...")
    
    try:
        subprocess.run(['cloudflared', '--version'], capture_output=True, check=True, timeout=5)
        print("✅ cloudflared ya instalado")
        return True
    except:
        print("📦 Instalando cloudflared...")
        
        try:
            arch_check = subprocess.run(['uname', '-m'], capture_output=True, text=True)
            arch = arch_check.stdout.strip()
            
            if arch == 'x86_64':
                binary = 'cloudflared-linux-amd64'
            elif arch == 'aarch64':
                binary = 'cloudflared-linux-arm64'
            else:
                binary = 'cloudflared-linux-amd64'
            
            install_commands = f"""
                curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/{{binary}} -o /tmp/cloudflared && \\
                chmod +x /tmp/cloudflared && \\
                sudo mv /tmp/cloudflared /usr/local/bin/cloudflared
            """
            
            subprocess.run(['bash', '-c', install_commands], check=True, capture_output=True, timeout=60)
            print("✅ cloudflared instalado")
            return True
        except Exception as e:
            print(f"❌ Error instalando cloudflared: {{e}}")
            return False

def notify_bot(tunnel_url):
    if not DISCORD_USER_ID:
        return False
    
    try:
        codespace_name = os.getenv("CODESPACE_NAME", "unknown")
        
        payload = {{
            "user_id": DISCORD_USER_ID,
            "codespace_name": codespace_name,
            "tunnel_url": tunnel_url,
            "tunnel_port": PORT,
            "tunnel_type": "cloudflare",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }}
        
        response = requests.post(BOT_WEBHOOK_URL, json=payload, timeout=15)
        
        if response.status_code == 200:
            print("📨 Bot notificado - Usuario recibirá DM")
            return True
    except:
        pass
    return False

def start_tunnel():
    print(f"🔄 Creando túnel Cloudflare para puerto {{PORT}}...")
    
    try:
        tunnel_process = subprocess.Popen(
            ['cloudflared', 'tunnel', '--url', f'http://localhost:{{PORT}}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        public_url = None
        
        def read_tunnel_output():
            nonlocal public_url
            for line in tunnel_process.stderr:
                if 'trycloudflare.com' in line:
                    match = re.search(r'https://[a-z0-9-]+\\.trycloudflare\\.com', line)
                    if match and not public_url:
                        public_url = match.group(0)
                        print(f"✅ Túnel público creado: {{public_url}}")
                        
                        with open(TUNNEL_URL_FILE, 'w') as f:
                            f.write(public_url)
                        
                        notify_bot(public_url)
        
        tunnel_thread = threading.Thread(target=read_tunnel_output, daemon=True)
        tunnel_thread.start()
        
        for i in range(60):
            if public_url:
                return True
            time.sleep(0.5)
        
        print("⚠️ Túnel creado pero URL no capturada")
        return True
    except Exception as e:
        print(f"❌ Error creando túnel: {{e}}")
        return False

if __name__ == '__main__':
    if install_cloudflared():
        start_tunnel()
        
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            pass
''')
        os.chmod(tunnel_manager_path, 0o755)

        with open(webserver_path, "w") as f:
            f.write(f'''#!/usr/bin/env python3
from flask import Flask, request, jsonify
import subprocess
import os
import glob
import time

app = Flask(__name__)
PORT = int(os.getenv('PORT', {port}))
AUTH_TOKEN = os.getenv('WEB_SERVER_AUTH_TOKEN', 'default_token')

def find_msx_py():
    matches = glob.glob('/workspaces/*/msx.py')
    return matches[0] if matches else None

def execute_minecraft_command(action):
    try:
        msx_path = find_msx_py()
        if not msx_path:
            return {{'error': 'msx.py no encontrado'}}
        
        repo_root = os.path.dirname(msx_path)
        
        if action == 'start':
            check = subprocess.run(
                ["tmux", "has-session", "-t", "msx"],
                capture_output=True
            )
            
            if check.returncode == 0:
                return {{
                    'status': 'success',
                    'action': 'start',
                    'message': 'Servidor ya está corriendo en tmux sesión msx',
                    'attach_command': 'tmux attach -t msx'
                }}
            
            subprocess.run(
                ["tmux", "new-session", "-d", "-s", "msx", "-c", repo_root],
                check=True
            )
            
            subprocess.run(
                ["tmux", "send-keys", "-t", "msx", "python3 msx.py", "C-m"],
                check=True
            )
            
            time.sleep(2)
            
            subprocess.run(
                ["tmux", "send-keys", "-t", "msx", "1", "C-m"],
                check=True
            )
            
            return {{
                'status': 'success',
                'action': 'start',
                'message': 'Minecraft iniciando en tmux sesión msx',
                'attach_command': 'tmux attach -t msx'
            }}
        
        elif action == 'stop':
            subprocess.run(
                ["tmux", "send-keys", "-t", "msx", "2", "C-m"],
                capture_output=True
            )
            time.sleep(1)
            return {{
                'status': 'success',
                'action': 'stop',
                'message': 'Comando de stop enviado a la sesión msx'
            }}
        
        elif action == 'status':
            java_check = subprocess.run(
                ['pgrep', '-f', 'java.*forge.*jar'],
                capture_output=True,
                text=True
            )
            running = bool(java_check.stdout.strip())
            pids = java_check.stdout.strip().split('\\n') if running else []
            return {{
                'status': 'success',
                'running': running,
                'minecraft_pids': pids if running else []
            }}
        
        else:
            return {{'error': f'Acción desconocida: {{action}}'}}
    
    except Exception as e:
        import traceback
        return {{'error': str(e), 'traceback': traceback.format_exc()}}

@app.route('/minecraft/start', methods=['POST'])
def minecraft_start():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token != AUTH_TOKEN:
        return jsonify({{'error': 'Unauthorized'}}), 401
    result = execute_minecraft_command('start')
    if 'error' in result:
        return jsonify(result), 500
    return jsonify(result)

@app.route('/minecraft/stop', methods=['POST'])
def minecraft_stop():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token != AUTH_TOKEN:
        return jsonify({{'error': 'Unauthorized'}}), 401
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
    tunnel_url = None
    try:
        with open('{TUNNEL_URL_FILE}', 'r') as f:
            tunnel_url = f.read().strip()
    except:
        pass
    
    return jsonify({{
        'status': 'ok',
        'port': PORT,
        'msx_found': msx_path is not None,
        'msx_path': msx_path,
        'tunnel_url': tunnel_url
    }})

@app.route('/get_token', methods=['GET'])
def get_token():
    return jsonify({{
        'token': AUTH_TOKEN,
        'codespace_name': os.getenv('CODESPACE_NAME', 'unknown')
    }})

@app.route('/get_url', methods=['GET'])
def get_url():
    tunnel_url = None
    try:
        with open('{TUNNEL_URL_FILE}', 'r') as f:
            tunnel_url = f.read().strip()
    except:
        pass
    
    return jsonify({{'tunnel_url': tunnel_url}})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
''')
        os.chmod(webserver_path, 0o755)

        with open(sh_path, "w") as f:
            f.write(f'''#!/bin/bash
WORK_DIR="$HOME/.d0ce3_addons"
cd "$WORK_DIR"

SESSION_NAME="webserver"
PORT={port}
USE_CLOUDFLARE={str(use_cloudflare).lower()}

if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    exit 0
fi

if [ -z "$WEB_SERVER_AUTH_TOKEN" ]; then
    BASHRC="$HOME/.bashrc"
    
    if grep -q "^export WEB_SERVER_AUTH_TOKEN=" "$BASHRC" 2>/dev/null; then
        source "$BASHRC"
    else
        NEW_TOKEN=$(openssl rand -hex 32)
        
        grep -v "^export WEB_SERVER_AUTH_TOKEN=" "$BASHRC" > "$BASHRC.tmp" 2>/dev/null || touch "$BASHRC.tmp"
        echo "export WEB_SERVER_AUTH_TOKEN=\\"$NEW_TOKEN\\"" >> "$BASHRC.tmp"
        mv "$BASHRC.tmp" "$BASHRC"
        
        export WEB_SERVER_AUTH_TOKEN="$NEW_TOKEN"
    fi
fi

if [ -z "$WEB_SERVER_AUTH_TOKEN" ]; then
    exit 1
fi

if ! python3 -c "import flask" 2>/dev/null; then
    pip3 install flask >/dev/null 2>&1
fi

if ! python3 -c "import requests" 2>/dev/null; then
    pip3 install requests >/dev/null 2>&1
fi

if [ -n "$CODESPACE_NAME" ]; then
    for i in {{1..30}}; do
        VISIBILITY=$(gh codespace ports -c "$CODESPACE_NAME" 2>/dev/null | grep "^$PORT" | awk '{{print $3}}')
        
        if [ "$VISIBILITY" = "public" ]; then
            break
        fi
        
        gh codespace ports visibility $PORT:public -c "$CODESPACE_NAME" >/dev/null 2>&1
        
        sleep 2
    done
fi

tmux new-session -d -s $SESSION_NAME "python3 $WORK_DIR/web_server.py"

if [ "$USE_CLOUDFLARE" = "true" ]; then
    nohup python3 "$WORK_DIR/tunnel_manager.py" > /dev/null 2>&1 &
fi
''')
        os.chmod(sh_path, 0o755)

        webserver_config["version"] = CURRENT_WEBSERVER_VERSION
        guardar_webserver_config(webserver_config)

        if os.path.exists(bashrc_path):
            with open(bashrc_path, "r") as f:
                bashrc_content = f.read()
            
            if bashrc_line not in bashrc_content and "start_web_server.sh" not in bashrc_content:
                with open(bashrc_path, "a") as f:
                    f.write(f"\n# d0ce3-Addons auto-start\n{bashrc_line}\n")

        try:
            import flask
        except ImportError:
            subprocess.call(["pip3", "install", "-q", "flask"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        try:
            import requests
        except ImportError:
            subprocess.call(["pip3", "install", "-q", "requests"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        subprocess.Popen(['bash', sh_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        port_ready = False
        for i in range(10):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                if result == 0:
                    port_ready = True
                    break
            except:
                pass
            time.sleep(1)
        
        if not port_ready:
            print(f"⚠ Puerto {port} no responde aún")
        
        print(f"\n✓ Servidor web configurado")
        print(f"💡 Puerto: {port}")
        print(f"📋 Ver logs msx: tmux attach -t msx, con este comando vas a poder acceder a la terminal normalmente")
        print(f" Usa ese comando unicamente si queres ver los logs o interactuar con la terminal.")
        print(f" Si queres salir de la termianal sin detener el servidor, presiona Ctrl+B y luego D.")
        print(f" Tambien creo que no hace falta aclarar, esto unicamente funciona si el servidor de Minecraft fue iniciado desde discord")
        
        if use_cloudflare:
            print(f"🌐 Cloudflare Tunnel activado")
            print(f"⏳ URL pública disponible en ~10 segundos")
            
            if DISCORD_USER_ID:
                print(f"📨 Bot será notificado automáticamente cuando el tunnel esté listo")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        if utils:
            utils.logger.error(f"Error en configuración web server: {e}")
            import traceback
            utils.logger.error(traceback.format_exc())
    
    return True