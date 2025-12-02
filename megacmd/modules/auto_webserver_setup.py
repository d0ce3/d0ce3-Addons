import os
import subprocess
import time
import socket
import glob
import json

WEBSERVER_CONFIG_FILE = os.path.expanduser("~/.d0ce3_addons/webserver_config.json")
CURRENT_WEBSERVER_VERSION = "1.0.0"

DEFAULT_WEBSERVER_CONFIG = {
    "port": 8080,
    "session_name": "msx",
    "auto_public": True,
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

def auto_configurar_web_server():
    utils = CloudModuleLoader.load_module("utils")
    config = CloudModuleLoader.load_module("config")
    
    webserver_config = cargar_webserver_config()
    
    work_dir = os.path.expanduser("~/.d0ce3_addons")
    sh_path = os.path.join(work_dir, "start_web_server.sh")
    webserver_path = os.path.join(work_dir, "web_server.py")
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
            os.path.exists(sh_path)
        )
        
        session_name = webserver_config.get("session_name", "msx")
        port = webserver_config.get("port", 8080)
        
        check_running = subprocess.run(
            ['tmux', 'has-session', '-t', session_name],
            capture_output=True
        )
        servidor_corriendo = check_running.returncode == 0
        
        if todo_instalado and not necesita_actualizacion(webserver_config):
            if servidor_corriendo:
                print(f"✓ Servidor web ya está configurado y corriendo")
                print(f"💡 Puerto: {port}")
                print(f"📋 Ver logs: tmux attach -t {session_name}")
                print()
                
                if webserver_config.get("auto_public", True):
                    print(f"🌐 Configurando puerto {port} como público...")
                    codespace_name = os.getenv('CODESPACE_NAME')
                    if codespace_name:
                        result = subprocess.run(
                            ['gh', 'codespace', 'ports', 'visibility', f'{port}:public', '-c', codespace_name],
                            capture_output=True,
                            text=True,
                            timeout=15
                        )
                        if result.returncode == 0:
                            verify = subprocess.run(
                                ['gh', 'codespace', 'ports', '-c', codespace_name],
                                capture_output=True,
                                text=True,
                                timeout=10
                            )
                            if str(port) in verify.stdout and 'public' in verify.stdout.lower():
                                print(f"✓ Puerto {port} está público")
                                if utils:
                                    utils.logger.info(f"Puerto {port} configurado como público")
                            else:
                                print(f"⚠ Puerto {port} configurado, pero verifica manualmente")
                                if utils:
                                    utils.logger.warning("Puerto configurado pero no verificado como público")
                        else:
                            print("⚠ No se pudo configurar automáticamente")
                    else:
                        print("⚠ No se puede configurar automáticamente (CODESPACE_NAME no definido)")
                
                return True
        
        if necesita_actualizacion(webserver_config):
            print(f"🔄 Actualizando servidor web ({webserver_config.get('version', '0.0.0')} → {CURRENT_WEBSERVER_VERSION})...\n")
            if servidor_corriendo:
                print(f"🛑 Deteniendo sesión {session_name}...")
                subprocess.run(['tmux', 'kill-session', '-t', session_name], capture_output=True)
                time.sleep(1)
        else:
            print("📦 Instalando servidor web de control...\n")
        
        os.makedirs(work_dir, exist_ok=True)

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
            process = subprocess.Popen(
                ['bash', '-c', f'cd {{repo_root}} && echo "1" | python3 msx.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=os.environ.copy()
            )
            time.sleep(1)
            return {{
                'status': 'success',
                'action': 'start',
                'message': 'Servidor Minecraft iniciando...',
                'pid': process.pid
            }}
        
        elif action == 'stop':
            process = subprocess.Popen(
                ['bash', '-c', f'cd {{repo_root}} && echo "2" | python3 msx.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=os.environ.copy()
            )
            time.sleep(1)
            return {{
                'status': 'success',
                'action': 'stop',
                'message': 'Comando stop enviado al servidor'
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
    return jsonify({{
        'status': 'ok',
        'port': PORT,
        'msx_found': msx_path is not None,
        'msx_path': msx_path
    }})

@app.route('/get_token', methods=['GET'])
def get_token():
    return jsonify({{
        'token': AUTH_TOKEN,
        'codespace_name': os.getenv('CODESPACE_NAME', 'unknown')
    }})

if __name__ == '__main__':
    print(f"Servidor web escuchando en puerto {{PORT}}")
    print(f"Token: {{AUTH_TOKEN[:8]}}...")
    msx_path = find_msx_py()
    if msx_path:
        print(f"msx.py encontrado: {{msx_path}}")
    app.run(host='0.0.0.0', port=PORT, debug=True)
''')
        os.chmod(webserver_path, 0o755)

        with open(sh_path, "w") as f:
            f.write(f'''#!/bin/bash
WORK_DIR="$HOME/.d0ce3_addons"
cd "$WORK_DIR"

SESSION_NAME="{session_name}"
PORT={port}

configure_public_port() {{
    if [ -n "$CODESPACE_NAME" ]; then
        for i in {{1..3}}; do
            gh codespace ports visibility $PORT:public -c "$CODESPACE_NAME" >/dev/null 2>&1
            if [ $? -eq 0 ]; then
                return 0
            fi
            sleep 2
        done
    fi
}}

if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    configure_public_port
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

tmux new-session -d -s $SESSION_NAME "python3 $WORK_DIR/web_server.py"

sleep 3

configure_public_port
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
        print(f"📋 Ver logs: tmux attach -t {session_name}")

        if webserver_config.get("auto_public", True):
            print(f"\n🌐 Configurando puerto {port} como público...")
            time.sleep(2)
            try:
                codespace_name = os.getenv('CODESPACE_NAME')
                if codespace_name:
                    result = subprocess.run(
                        ['gh', 'codespace', 'ports', 'visibility', f'{port}:public', '-c', codespace_name],
                        capture_output=True,
                        text=True,
                        timeout=15
                    )
                    if result.returncode == 0:
                        verify = subprocess.run(
                            ['gh', 'codespace', 'ports', '-c', codespace_name],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if str(port) in verify.stdout and 'public' in verify.stdout.lower():
                            print(f"✓ Puerto {port} está público")
                        else:
                            print(f"⚠ Verifica manualmente el puerto {port}")
                    else:
                        print("⚠ No se pudo configurar automáticamente")
                else:
                    print("⚠ No se puede configurar automáticamente")
            except Exception as e:
                print(f"⚠ Error: {str(e)}")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        if utils:
            utils.logger.error(f"Error en configuración web server: {e}")
            import traceback
            utils.logger.error(traceback.format_exc())
    
    return True