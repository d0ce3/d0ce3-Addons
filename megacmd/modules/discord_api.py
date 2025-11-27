"""
API HTTP para que el bot consulte eventos desde el Codespace
Expone endpoints Flask para polling de eventos
"""
import json
from datetime import datetime
from typing import Optional

try:
    from flask import Flask, jsonify, request
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("⚠️ Flask no disponible. Instalar con: pip install flask")

try:
    discord_queue_mod = CloudModuleLoader.load_module("discord_queue")
    discord_config_mod = CloudModuleLoader.load_module("discord_config")
    
    queue = discord_queue_mod.queue_instance
    config = discord_config_mod.discord_config
except Exception as e:
    print(f"⚠️ Error cargando módulos Discord: {e}")
    queue = None
    config = None


class DiscordAPI:
    """
    API Flask para exponer eventos Discord
    """
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        if app:
            self.register_routes()
    
    def register_routes(self):
        """Registra las rutas en la aplicación Flask"""
        
        @self.app.route('/discord/events', methods=['GET'])
        def get_events():
            """
            GET /discord/events?limit=50&max_attempts=3
            
            Retorna eventos pendientes de la cola
            """
            try:
                limit = int(request.args.get('limit', 50))
                max_attempts = int(request.args.get('max_attempts', 3))
                
                limit = min(limit, 100)
                
                if not queue:
                    return jsonify({
                        'success': False,
                        'error': 'Queue not initialized'
                    }), 500
                
                events = queue.get_pending_events(
                    max_attempts=max_attempts,
                    limit=limit
                )
                
                return jsonify({
                    'success': True,
                    'count': len(events),
                    'events': events,
                    'timestamp': datetime.now().isoformat()
                }), 200
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/discord/events/<int:event_id>/processed', methods=['POST'])
        def mark_processed(event_id):
            """
            POST /discord/events/{event_id}/processed
            
            Marca un evento como procesado
            """
            try:
                if not queue:
                    return jsonify({
                        'success': False,
                        'error': 'Queue not initialized'
                    }), 500
                
                queue.mark_processed(event_id)
                
                return jsonify({
                    'success': True,
                    'event_id': event_id,
                    'status': 'processed'
                }), 200
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/discord/events/<int:event_id>/failed', methods=['POST'])
        def mark_failed(event_id):
            """
            POST /discord/events/{event_id}/failed
            Body: {"error_message": "mensaje"}
            
            Marca un evento como fallido
            """
            try:
                if not queue:
                    return jsonify({
                        'success': False,
                        'error': 'Queue not initialized'
                    }), 500
                
                data = request.get_json() or {}
                error_message = data.get('error_message')
                
                queue.mark_failed(event_id, error_message)
                
                return jsonify({
                    'success': True,
                    'event_id': event_id,
                    'status': 'failed'
                }), 200
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/discord/stats', methods=['GET'])
        def get_stats():
            """
            GET /discord/stats
            
            Retorna estadísticas de la cola
            """
            try:
                if not queue:
                    return jsonify({
                        'success': False,
                        'error': 'Queue not initialized'
                    }), 500
                
                stats = queue.get_stats()
                
                return jsonify({
                    'success': True,
                    'stats': stats,
                    'config': config.get_status() if config else None,
                    'timestamp': datetime.now().isoformat()
                }), 200
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/discord/health', methods=['GET'])
        def health_check():
            """
            GET /discord/health
            
            Health check del sistema
            """
            return jsonify({
                'success': True,
                'status': 'healthy',
                'queue_available': queue is not None,
                'config_valid': config.is_valid() if config else False,
                'timestamp': datetime.now().isoformat()
            }), 200
        
        @self.app.route('/discord/cleanup', methods=['POST'])
        def cleanup_old_events():
            """
            POST /discord/cleanup?days=7
            
            Limpia eventos antiguos
            """
            try:
                if not queue:
                    return jsonify({
                        'success': False,
                        'error': 'Queue not initialized'
                    }), 500
                
                days = int(request.args.get('days', 7))
                deleted = queue.cleanup_old_events(days)
                
                return jsonify({
                    'success': True,
                    'deleted_count': deleted,
                    'days': days
                }), 200
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500


def create_standalone_app(host='0.0.0.0', port=8080, debug=False):
    """
    Crea y ejecuta una aplicación Flask standalone para la API
    
    Args:
        host: Host a escuchar
        port: Puerto a escuchar
        debug: Modo debug
    """
    if not FLASK_AVAILABLE:
        print("❌ Flask no está instalado")
        return None
    
    app = Flask(__name__)
    api = DiscordAPI(app)
    
    @app.route('/', methods=['GET'])
    def index():
        return jsonify({
            'service': 'd0ce3-Addons Discord API',
            'version': '1.0.0',
            'endpoints': [
                'GET /discord/health',
                'GET /discord/stats',
                'GET /discord/events',
                'POST /discord/events/<id>/processed',
                'POST /discord/events/<id>/failed',
                'POST /discord/cleanup'
            ]
        })
    
    print(f"\n🚀 Discord API iniciando en http://{host}:{port}")
    print(f"   Health: http://{host}:{port}/discord/health")
    print(f"   Events: http://{host}:{port}/discord/events\n")
    
    return app


def run_api_server(host='0.0.0.0', port=8080, debug=False):
    """
    Ejecuta el servidor API de forma standalone
    """
    app = create_standalone_app(host, port, debug)
    if app:
        app.run(host=host, port=port, debug=debug)


__all__ = [
    'DiscordAPI',
    'create_standalone_app',
    'run_api_server'
]