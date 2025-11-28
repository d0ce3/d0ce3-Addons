#!/usr/bin/env python3
"""
Servidor web para control remoto de Minecraft
Permite al bot de Discord iniciar el servidor de Minecraft
"""

from flask import Flask, request, jsonify
import os
import subprocess
import threading
import time
import json
from datetime import datetime
import logging

app = Flask(__name__)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Token de autenticación (se debe configurar en .env)
AUTH_TOKEN = os.getenv('WEB_SERVER_AUTH_TOKEN', 'default_token_change_me')

# Ruta al workspace
WORKSPACE = os.getenv('CODESPACE_VSCODE_FOLDER', '/workspace')
MSX_PATH = os.path.join(WORKSPACE, 'msx.py')
CONFIG_PATH = os.path.join(WORKSPACE, 'configuracion.json')

# Estado del servidor
servidor_estado = {
    'iniciando': False,
    'online': False,
    'proceso': None,
    'ultimo_inicio': None,
    'ip': None
}


def verificar_token(token):
    """Verifica que el token de autenticación sea válido"""
    return token == AUTH_TOKEN


def leer_configuracion_msx():
    """Lee el archivo configuracion.json"""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error leyendo configuracion.json: {e}")
    return None


def obtener_ip_servidor():
    """Obtiene la IP del servidor según el servicio configurado"""
    config = leer_configuracion_msx()
    if not config:
        return None
    
    servicio = config.get('servicio_a_usar', '').lower()
    
    try:
        if servicio == 'playit':
            # Intentar leer desde archivo de configuración de playit
            playit_config = os.path.join(WORKSPACE, '.playit', 'config.toml')
            if os.path.exists(playit_config):
                with open(playit_config, 'r') as f:
                    contenido = f.read()
                    for line in contenido.split('\n'):
                        if 'address' in line.lower() and '"' in line:
                            partes = line.split('"')
                            if len(partes) >= 2:
                                return partes[1]
        
        elif servicio == 'tailscale':
            result = subprocess.run(
                ['tailscale', 'ip'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        
        elif servicio == 'zerotier':
            result = subprocess.run(
                ['zerotier-cli', 'listnetworks'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lineas = result.stdout.strip().split('\n')
                for linea in lineas[1:]:
                    partes = linea.split()
                    if len(partes) >= 3:
                        ip_candidata = partes[-1]
                        if '.' in ip_candidata or ':' in ip_candidata:
                            return ip_candidata
    
    except Exception as e:
        logger.error(f"Error obteniendo IP: {e}")
    
    return None


def iniciar_minecraft_automatico():
    """Inicia Minecraft automáticamente ejecutando msx.py con opción 1"""
    global servidor_estado
    
    try:
        logger.info("Iniciando proceso de Minecraft...")
        servidor_estado['iniciando'] = True
        servidor_estado['ultimo_inicio'] = datetime.now().isoformat()
        
        # Verificar que existe msx.py
        if not os.path.exists(MSX_PATH):
            logger.error(f"msx.py no encontrado en {MSX_PATH}")
            servidor_estado['iniciando'] = False
            return False, "msx.py no encontrado"
        
        # Esperar un poco para que el Codespace esté listo
        logger.info("Esperando 5 segundos...")
        time.sleep(5)
        
        # Ejecutar msx.py con opción 1 (iniciar servidor)
        # Usamos echo "1" para enviar automáticamente la opción
        cmd = f'echo "1" | python3 {MSX_PATH}'
        
        logger.info(f"Ejecutando: {cmd}")
        proceso = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=WORKSPACE
        )
        
        # Esperar un poco para ver si hubo algún error inmediato
        time.sleep(2)
        
        if proceso.poll() is not None:
            # El proceso terminó, revisar si fue error
            stdout, stderr = proceso.communicate()
            logger.error(f"Proceso terminó inmediatamente")
            logger.error(f"STDOUT: {stdout.decode()}")
            logger.error(f"STDERR: {stderr.decode()}")
            servidor_estado['iniciando'] = False
            return False, "Error al iniciar servidor"
        
        servidor_estado['proceso'] = proceso
        servidor_estado['iniciando'] = False
        servidor_estado['online'] = True
        
        # Obtener IP
        time.sleep(3)  # Esperar a que el servidor esté completamente arrancado
        ip = obtener_ip_servidor()
        if ip:
            servidor_estado['ip'] = ip
            logger.info(f"Servidor iniciado con IP: {ip}")
        
        logger.info("✓ Minecraft iniciado correctamente")
        return True, "Servidor iniciado"
        
    except Exception as e:
        logger.error(f"Error iniciando Minecraft: {e}")
        servidor_estado['iniciando'] = False
        servidor_estado['online'] = False
        return False, str(e)


@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar que el servidor está vivo"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'workspace': WORKSPACE
    })


@app.route('/minecraft/start', methods=['POST'])
def minecraft_start():
    """Endpoint para iniciar el servidor de Minecraft"""
    try:
        # Verificar autenticación
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': 'No se proporcionó token de autenticación'
            }), 401
        
        token = auth_header.split('Bearer ')[1]
        if not verificar_token(token):
            return jsonify({
                'success': False,
                'error': 'Token inválido'
            }), 401
        
        # Verificar si ya está iniciando
        if servidor_estado['iniciando']:
            return jsonify({
                'success': False,
                'error': 'El servidor ya se está iniciando',
                'estado': servidor_estado
            })
        
        # Verificar si ya está online
        if servidor_estado['online']:
            ip = servidor_estado.get('ip') or obtener_ip_servidor()
            return jsonify({
                'success': True,
                'message': 'El servidor ya está online',
                'ip': ip,
                'estado': servidor_estado
            })
        
        # Iniciar en un thread separado para no bloquear
        thread = threading.Thread(target=iniciar_minecraft_automatico)
        thread.daemon = True
        thread.start()
        
        # Esperar un poco para obtener resultado inicial
        time.sleep(2)
        
        return jsonify({
            'success': True,
            'message': 'Iniciando servidor de Minecraft...',
            'estado': servidor_estado,
            'nota': 'El servidor tardará aproximadamente 30-60 segundos en estar completamente listo'
        })
        
    except Exception as e:
        logger.error(f"Error en /minecraft/start: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/minecraft/status', methods=['GET'])
def minecraft_status():
    """Endpoint para consultar el estado del servidor"""
    try:
        # Verificar autenticación (opcional para status)
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split('Bearer ')[1]
            if not verificar_token(token):
                return jsonify({
                    'success': False,
                    'error': 'Token inválido'
                }), 401
        
        # Actualizar IP si está online y no la tenemos
        if servidor_estado['online'] and not servidor_estado.get('ip'):
            servidor_estado['ip'] = obtener_ip_servidor()
        
        return jsonify({
            'success': True,
            'estado': servidor_estado,
            'ip': servidor_estado.get('ip') or obtener_ip_servidor(),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en /minecraft/status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/minecraft/ip', methods=['GET'])
def minecraft_ip():
    """Endpoint para obtener solo la IP del servidor"""
    try:
        ip = obtener_ip_servidor()
        
        if ip:
            return jsonify({
                'success': True,
                'ip': ip
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo obtener la IP'
            }), 404
        
    except Exception as e:
        logger.error(f"Error en /minecraft/ip: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    
    logger.info("="*50)
    logger.info("🚀 Servidor Web de Control de Minecraft")
    logger.info("="*50)
    logger.info(f"Puerto: {port}")
    logger.info(f"Workspace: {WORKSPACE}")
    logger.info(f"Auth Token: {'Configurado' if AUTH_TOKEN != 'default_token_change_me' else 'USAR DEFAULT (INSEGURO)'}")
    logger.info("="*50)
    
    if AUTH_TOKEN == 'default_token_change_me':
        logger.warning("⚠️  ADVERTENCIA: Usando token por defecto. Configura WEB_SERVER_AUTH_TOKEN en .env")
    
    app.run(host='0.0.0.0', port=port, debug=False)
