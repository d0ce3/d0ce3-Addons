#!/bin/bash

# Script para iniciar el servidor web de control de Minecraft
# Se debe ejecutar en el Codespace cuando arranque

echo "========================================"
echo "🚀 Iniciando servidor web de control"
echo "========================================"

# Verificar que estamos en el workspace correcto
if [ -z "$CODESPACE_VSCODE_FOLDER" ]; then
    echo "⚠️  CODESPACE_VSCODE_FOLDER no definido"
    export CODESPACE_VSCODE_FOLDER="/workspace"
fi

echo "Workspace: $CODESPACE_VSCODE_FOLDER"

# Generar token aleatorio si no existe
if [ -z "$WEB_SERVER_AUTH_TOKEN" ]; then
    echo "⚠️  Generando token aleatorio..."
    export WEB_SERVER_AUTH_TOKEN=$(openssl rand -hex 32)
    echo "Token: $WEB_SERVER_AUTH_TOKEN"
    echo ""
    echo "📝 Guarda este token para configurar el bot de Discord"
    echo ""
fi

# Puerto
PORT=${PORT:-8080}
echo "Puerto: $PORT"

# Ir al directorio de d0ce3-Addons
cd "$CODESPACE_VSCODE_FOLDER/d0ce3-Addons" || exit 1

# Instalar Flask si no está instalado
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Instalando Flask..."
    pip3 install flask
fi

echo ""
echo "✅ Servidor web listo"
echo "========================================"
echo ""

# Iniciar servidor
python3 web_server.py
