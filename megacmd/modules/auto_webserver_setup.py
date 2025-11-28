import os
import subprocess
import time
import socket
import glob

def auto_configurar_web_server():
    work_dir = os.path.expanduser("~/.d0ce3_addons")
    os.makedirs(work_dir, exist_ok=True)
    
    sh_path = os.path.join(work_dir, "start_web_server.sh")
    webserver_path = os.path.join(work_dir, "web_server.py")
    bashrc_path = os.path.expanduser("~/.bashrc")
    bashrc_line = f"[ -f '{sh_path}' ] && nohup bash {sh_path} > /tmp/web_server.log 2>&1 &"

    print("\n" + "─" * 50)
    print("CONFIGURANDO SERVIDOR WEB DE CONTROL")
    print("─" * 50 + "\n")
    print(f"📂 Instalando en: {work_dir}\n")

    try:
        print("📦 Verificando screen...")
        screen_check = subprocess.run(['which', 'screen'], capture_output=True)
        if screen_check.returncode != 0:
            print("Instalando screen...")
            subprocess.run(['sudo', 'apt-get', 'update', '-qq'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'screen'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("✓ Screen instalado")
        else:
            print("✓ Screen ya está instalado")

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
            check = subprocess.run(['screen', '-ls'], capture_output=True, text=True)
            if 'minecraft_msx' in check.stdout:
                return {'status': 'info', 'message': 'Servidor ya está iniciado'}
            
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
            check = subprocess.run(['screen', '-ls'], capture_output=True, text=True)
            if 'minecraft_msx' in check.stdout:
                cmd = f'screen -S minecraft_msx -X stuff "2\\n"'
                subprocess.Popen(cmd, shell=True)
            else:
                cmd = f'cd {repo_root} && echo 2 | python3 msx.py'
                subprocess.Popen(cmd, shell=True, env=os.environ.copy())
            
            time.sleep(2)
            
            return {
                'status': 'success',
                'action': 'stop',
                'message': 'Comando stop enviado al servidor'
            }
        
        elif action == 'status':
            java_check = subprocess.run(['pgrep', '-f', 'java.*forge.*jar'], capture_output=True, text=True)
            running = bool(java_check.stdout.strip())
            pids = java_check.stdout.strip().split('\\n') if running else []
            
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
        print("✓ web_server.py creado")

        print("📝 Creando start_web_server.sh...")
        with open(sh_path, "w") as f:
            f.write('''#!/bin/bash
WORK_DIR="$HOME/.d0ce3_addons"
cd "$WORK_DIR"

if pgrep -f "python3.*web_server.py" > /dev/null; then
    echo "⚠ Servidor web ya está corriendo"
    exit 0
fi

if [ -z "$WEB_SERVER_AUTH_TOKEN" ]; then
    NEW_TOKEN=$(openssl rand -hex 32)
    if ! grep -q "WEB_SERVER_AUTH_TOKEN" ~/.bashrc 2>/dev/null; then
        echo "export WEB_SERVER_AUTH_TOKEN=\\"$NEW_TOKEN\\"" >> ~/.bashrc
    fi
    export WEB_SERVER_AUTH_TOKEN="$NEW_TOKEN"
fi

PORT=${PORT:-8080}

if ! python3 -c "import flask" 2>/dev/null; then
    pip3 install flask >/dev/null 2>&1
fi

nohup python3 "$WORK_DIR/web_server.py" > /tmp/web_server.log 2>&1 &
echo "✅ Servidor web iniciado (puerto $PORT)"
echo "🔑 Token: ${WEB_SERVER_AUTH_TOKEN:0:8}..."
''')
        os.chmod(sh_path, 0o755)
        print("✓ start_web_server.sh creado")

        if os.path.exists(bashrc_path):
            with open(bashrc_path, "r") as f:
                bashrc_content = f.read()
            if bashrc_line not in bashrc_content:
                print("\n📝 Agregando inicio automático a ~/.bashrc...")
                with open(bashrc_path, "a") as f:
                    f.write(f"\n# d0ce3-Addons auto-start\n{bashrc_line}\n")
                print("✓ Agregado a ~/.bashrc")
            else:
                print("✓ Ya configurado en ~/.bashrc")

        print("\n📦 Verificando Flask...")
        try:
            import flask
            print("✓ Flask ya está instalado")
        except ImportError:
            print("Instalando Flask...")
            subprocess.call(["pip3", "install", "flask"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("✓ Flask instalado")

        print("\n🚀 Iniciando servidor web...")
        subprocess.Popen(['bash', sh_path])
        
        print("✓ Servidor web configurado e iniciado")
        print("✓ Se iniciará automáticamente en futuros arranques")
        print(f"\n📂 Archivos en: {work_dir}")
        print("⭐ Ya puedes usar /minecraft_start desde Discord")
        print("\n💡 Puerto: 8080")
        print("📋 Logs: tail -f /tmp/web_server.log")
        print("🖥️  Consola: screen -r minecraft_msx")

        print("\n🌐 Configurando puerto 8080 como público...")
        port_ready = False
        for i in range(10):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', 8080))
                sock.close()
                if result == 0:
                    print(f"   ✓ Puerto 8080 escuchando (después de {i+1}s)")
                    port_ready = True
                    break
            except:
                pass
            time.sleep(1)
        
        if not port_ready:
            print("   ⚠ Puerto 8080 no responde aún, intentando de todas formas...")

        time.sleep(2)
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
                    print("✓ Puerto 8080 configurado como público automáticamente")
                else:
                    print("⚠ Configura manualmente el puerto 8080 como PÚBLICO en VS Code → Panel PORTS")
            else:
                print("⚠ CODESPACE_NAME no está definido")
        except Exception as e:
            print(f"⚠ No se pudo configurar automáticamente: {str(e)}")
            print("  Configura manualmente: gh codespace ports visibility 8080:public -c $CODESPACE_NAME")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        print(traceback.format_exc())
    
    return True
