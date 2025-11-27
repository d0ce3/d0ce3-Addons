"""
Discord Bot Consumer - Para usar en Doce-Bt
Pollea eventos desde el Codespace y los envía a Discord

Cómo usar:
1. Copia este archivo a tu proyecto Doce-Bt
2. Importa y ejecuta start_consumer() en tu bot
3. El consumer hará polling cada 30 segundos
"""
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CodespaceEventConsumer:
    """
    Consumer que pollea eventos desde el Codespace
    """
    
    def __init__(self, bot, codespace_urls: List[str], poll_interval: int = 30):
        """
        Args:
            bot: Instancia del bot Discord
            codespace_urls: Lista de URLs de Codespaces a monitorear
                          Ejemplo: ['https://codespace-8080.app.github.dev']
            poll_interval: Intervalo de polling en segundos (default: 30)
        """
        self.bot = bot
        self.codespace_urls = codespace_urls
        self.poll_interval = poll_interval
        self.session: Optional[aiohttp.ClientSession] = None
        self.running = False
        self.stats = {
            'total_polled': 0,
            'total_processed': 0,
            'total_failed': 0,
            'last_poll': None
        }
    
    async def start(self):
        """Inicia el consumer"""
        if self.running:
            logger.warning("Consumer ya está corriendo")
            return
        
        self.running = True
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))
        
        logger.info(f"🚀 Consumer iniciado - polling cada {self.poll_interval}s")
        logger.info(f"   Monitoreando: {len(self.codespace_urls)} Codespace(s)")
        
        asyncio.create_task(self._polling_loop())
    
    async def stop(self):
        """Detiene el consumer"""
        self.running = False
        
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info("⏹️ Consumer detenido")
    
    async def _polling_loop(self):
        """Loop principal de polling"""
        while self.running:
            try:
                await self._poll_all_codespaces()
                self.stats['last_poll'] = datetime.now().isoformat()
            except Exception as e:
                logger.error(f"❌ Error en polling loop: {e}", exc_info=True)
            
            await asyncio.sleep(self.poll_interval)
    
    async def _poll_all_codespaces(self):
        """Pollea todos los Codespaces configurados"""
        tasks = [
            self._poll_codespace(url)
            for url in self.codespace_urls
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _poll_codespace(self, codespace_url: str):
        """Pollea un Codespace específico"""
        try:
            events_url = f"{codespace_url}/discord/events"
            
            async with self.session.get(events_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('success'):
                        events = data.get('events', [])
                        
                        if events:
                            logger.info(f"📦 {len(events)} evento(s) desde {codespace_url}")
                            
                            for event in events:
                                await self._process_event(event, codespace_url)
                        
                        self.stats['total_polled'] += len(events)
                    else:
                        logger.warning(f"⚠️  Error en respuesta de {codespace_url}: {data.get('error')}")
                
                elif response.status == 404:
                    logger.debug(f"Endpoint no encontrado en {codespace_url} (puede estar desactualizado)")
                else:
                    logger.warning(f"⚠️  HTTP {response.status} desde {codespace_url}")
        
        except aiohttp.ClientError as e:
            logger.debug(f"No se pudo conectar a {codespace_url}: {e}")
        except Exception as e:
            logger.error(f"❌ Error polling {codespace_url}: {e}")
    
    async def _process_event(self, event: Dict, codespace_url: str):
        """
        Procesa un evento individual
        
        Args:
            event: Evento a procesar
            codespace_url: URL del Codespace origen
        """
        event_id = event['id']
        event_type = event['event_type']
        user_id = event['user_id']
        payload = event['payload']
        
        try:
            logger.info(f"🔄 Procesando evento #{event_id}: {event_type}")
            
            user = await self.bot.fetch_user(int(user_id))
            if not user:
                logger.warning(f"⚠️  Usuario {user_id} no encontrado")
                await self._mark_failed(event_id, codespace_url, "Usuario no encontrado")
                return
            
            if event_type == 'backup_error':
                await self._handle_backup_error(user, payload)
            
            elif event_type == 'backup_success':
                await self._handle_backup_success(user, payload)
            
            elif event_type == 'minecraft_status':
                await self._handle_minecraft_status(user, payload)
            
            elif event_type == 'codespace_status':
                await self._handle_codespace_status(user, payload)
            
            else:
                logger.warning(f"⚠️  Tipo de evento desconocido: {event_type}")
                await self._mark_failed(event_id, codespace_url, f"Tipo desconocido: {event_type}")
                return
            
            await self._mark_processed(event_id, codespace_url)
            self.stats['total_processed'] += 1
            logger.info(f"✅ Evento #{event_id} procesado")
        
        except Exception as e:
            logger.error(f"❌ Error procesando evento #{event_id}: {e}", exc_info=True)
            await self._mark_failed(event_id, codespace_url, str(e))
            self.stats['total_failed'] += 1
    
    async def _handle_backup_error(self, user, payload):
        """Maneja errores de backup"""
        error_type = payload.get('error_type', 'general')
        error_message = payload.get('error_message', 'Error desconocido')
        codespace_name = payload.get('codespace_name', 'Desconocido')
        
        embed_color = 0xFF0000  # Rojo
        
        if 'compression' in error_type:
            title = "📦 Error en Compresión de Backup"
        elif 'upload' in error_type:
            title = "☁️ Error en Subida a MEGA"
        else:
            title = "❌ Error en Backup"
        
        embed = {
            'title': title,
            'description': f'```\n{error_message}\n```',
            'color': embed_color,
            'fields': [
                {'name': 'Codespace', 'value': codespace_name, 'inline': True},
                {'name': 'Tipo', 'value': error_type, 'inline': True}
            ],
            'timestamp': datetime.now().isoformat(),
            'footer': {'text': 'd0ce3|tools • Backup Monitor'}
        }
        
        await user.send(embed=embed)
    
    async def _handle_backup_success(self, user, payload):
        """Maneja backups exitosos"""
        backup_file = payload.get('backup_file', 'Desconocido')
        size_mb = payload.get('size_mb', 0)
        duration = payload.get('duration_seconds', 0)
        codespace_name = payload.get('codespace_name', 'Desconocido')
        
        embed = {
            'title': '✅ Backup Completado',
            'color': 0x00FF00,  # Verde
            'fields': [
                {'name': 'Archivo', 'value': f'`{backup_file}`', 'inline': False},
                {'name': 'Tamaño', 'value': f'{size_mb:.2f} MB', 'inline': True},
                {'name': 'Duración', 'value': f'{duration:.1f}s', 'inline': True},
                {'name': 'Codespace', 'value': codespace_name, 'inline': True}
            ],
            'timestamp': datetime.now().isoformat(),
            'footer': {'text': 'd0ce3|tools • Backup Monitor'}
        }
        
        await user.send(embed=embed)
    
    async def _handle_minecraft_status(self, user, payload):
        """Maneja cambios de estado de Minecraft"""
        status = payload.get('status', 'unknown')
        ip = payload.get('ip')
        port = payload.get('port', 25565)
        players = payload.get('players_online', 0)
        
        status_emoji = {
            'online': '✅',
            'offline': '❌',
            'starting': '🔄',
            'stopping': '⏹️'
        }.get(status, '❓')
        
        embed = {
            'title': f'{status_emoji} Servidor Minecraft - {status.upper()}',
            'color': 0x00FF00 if status == 'online' else 0xFF0000,
            'fields': [],
            'timestamp': datetime.now().isoformat()
        }
        
        if ip:
            server_address = f'{ip}:{port}' if port != 25565 else ip
            embed['fields'].append({'name': 'IP', 'value': f'`{server_address}`', 'inline': True})
        
        if status == 'online':
            embed['fields'].append({'name': 'Jugadores', 'value': str(players), 'inline': True})
        
        await user.send(embed=embed)
    
    async def _handle_codespace_status(self, user, payload):
        """Maneja cambios de estado del Codespace"""
        action = payload.get('action', 'unknown')
        details = payload.get('details', {})
        codespace_name = payload.get('codespace_name', 'Desconocido')
        
        action_emoji = {
            'started': '▶️',
            'stopped': '⏹️',
            'error': '❌'
        }.get(action, '🔔')
        
        embed = {
            'title': f'{action_emoji} Codespace {action.upper()}',
            'description': f'**{codespace_name}**',
            'color': 0x00FF00 if action == 'started' else 0xFF0000,
            'timestamp': datetime.now().isoformat()
        }
        
        if details:
            for key, value in details.items():
                embed.setdefault('fields', []).append({
                    'name': key.replace('_', ' ').title(),
                    'value': str(value),
                    'inline': True
                })
        
        await user.send(embed=embed)
    
    async def _mark_processed(self, event_id: int, codespace_url: str):
        """Marca un evento como procesado"""
        try:
            url = f"{codespace_url}/discord/events/{event_id}/processed"
            async with self.session.post(url) as response:
                if response.status != 200:
                    logger.warning(f"⚠️  Error marcando evento #{event_id} como procesado")
        except Exception as e:
            logger.error(f"❌ Error marcando procesado #{event_id}: {e}")
    
    async def _mark_failed(self, event_id: int, codespace_url: str, error_message: str):
        """Marca un evento como fallido"""
        try:
            url = f"{codespace_url}/discord/events/{event_id}/failed"
            async with self.session.post(url, json={'error_message': error_message}) as response:
                if response.status != 200:
                    logger.warning(f"⚠️  Error marcando evento #{event_id} como fallido")
        except Exception as e:
            logger.error(f"❌ Error marcando fallido #{event_id}: {e}")
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas del consumer"""
        return self.stats.copy()


async def start_consumer(bot, codespace_urls: List[str], poll_interval: int = 30):
    """
    Función helper para iniciar el consumer
    
    Uso en tu bot:
    
    @bot.event
    async def on_ready():
        codespaces = [
            'https://tu-codespace-8080.app.github.dev',
            # Agregar más Codespaces si es necesario
        ]
        await start_consumer(bot, codespaces, poll_interval=30)
    
    Args:
        bot: Instancia del bot Discord
        codespace_urls: Lista de URLs de Codespaces
        poll_interval: Intervalo de polling en segundos
    """
    consumer = CodespaceEventConsumer(bot, codespace_urls, poll_interval)
    await consumer.start()
    
    return consumer