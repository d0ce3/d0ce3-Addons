import os
import subprocess

def auto_configurar_web_server():
    workspace = os.getenv("CODESPACE_VSCODE_FOLDER", "/workspace")
    addon_path = f"{workspace}/d0ce3-Addons"
    sh_path = os.path.join(addon_path, "start_web_server.sh")
    bashrc_path = os.path.expanduser("~/.bashrc")
    bashrc_line = f"cd {addon_path} && nohup bash start_web_server.sh &"

    # 1. Crear script si no existe
    if not os.path.exists(sh_path):
        with open(sh_path, "w") as f:
            f.write("""#!/bin/bash\nif [ -z \"$WEB_SERVER_AUTH_TOKEN\" ]; then\n    export WEB_SERVER_AUTH_TOKEN=$(openssl rand -hex 32)\nfi\nPORT=${PORT:-8080}\ncd \"$(dirname \"$0\")\"\nif ! python3 -c \"import flask\" 2>/dev/null; then\n    echo \"Instalando Flask...\"\n    pip3 install flask\nfi\nnohup python3 web_server.py > /tmp/web_server.log 2>&1 &\necho \"Servidor web iniciado en segundo plano (puerto $PORT)\"\n""")
        os.chmod(sh_path, 0o755)
        print("✓ start_web_server.sh creado.")

    # 2. Agregar al bashrc si no está
    if os.path.exists(bashrc_path):
        with open(bashrc_path, "r") as f:
            bashrc_content = f.read()
        if bashrc_line not in bashrc_content:
            with open(bashrc_path, "a") as f:
                f.write("\n# Iniciar servidor web de control Minecraft (Discord)\n")
                f.write(bashrc_line + "\n")
            print("✓ start_web_server.sh agregado a ~/.bashrc para arranque automático.")

    # 3. Instalar Flask si hace falta
    try:
        import flask
        print("✓ Flask ya está instalado.")
    except ImportError:
        print("Instalando Flask...")
        subprocess.call(["pip3", "install", "flask"])

    # 4. Ejecutar el servidor web ahora mismo
    try:
        subprocess.Popen(['bash', sh_path])
        print("✓ Servidor web de control iniciado en segundo plano.")
        print("⭐ Ya puedes usar /minecraft_start en Discord.")
    except Exception as e:
        print(f"⚠️  Error al iniciar el servidor web automáticamente: {e}")
        print(f"Puedes iniciarlo manualmente con: bash {sh_path}")
