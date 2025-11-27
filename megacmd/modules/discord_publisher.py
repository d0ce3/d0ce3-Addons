"""
Publisher de eventos Discord desde el Codespace
Publica eventos a la cola SQLite para que el bot los procese
"""
import os
from typing import Optional, Dict
from datetime import datetime

try:
    utils = CloudModuleLoader.load_module("utils")
    discord_queue_mod = CloudModuleLoader.load_module("discord_queue")
    discord_config_mod = CloudModuleLoader.load_module("discord_config")
    
    queue = discord_queue_mod.queue_instance
    config = discord_config_mod.discord_config
except Exception as e:
    print(f"⚠️ Error cargando módulos Discord: {e}")
    queue = None
    config = None
    utils = None


class EventPublisher:
    """
    Publisher centralizado de eventos Discord
    Maneja la lógica de publicación a la cola
    """
    
    @staticmethod
    def is_enabled() -> bool:
        """Verifica si el sistema de notificaciones está habilitado"""
        return config is not None and config.is_valid()
    
    @staticmethod
    def _ensure_codespace_info(payload: dict) -> dict:
        """Agrega información del Codespace al payload"""
        if 'codespace_name' not in payload:
            payload['codespace_name'] = config.codespace_name or "Desconocido"
        
        if 'timestamp' not in payload:
            payload['timestamp'] = datetime.now().isoformat()
        
        return payload
    
    @staticmethod
    def publish_event(event_type: str, payload: dict, user_id: Optional[str] = None) -> bool:
        """
        Publica un evento genérico a la cola
        
        Args:
            event_type: Tipo de evento
            payload: Datos del evento
            user_id: ID del usuario (opcional, usa el de config si no se provee)
        
        Returns:
            bool: True si se publicó exitosamente
        """
        if not EventPublisher.is_enabled():
            if utils:
                utils.logger.debug("Sistema de notificaciones Discord deshabilitado")
            return False
        
        try:
            target_user = user_id or config.user_id
            if not target_user:
                if utils:
                    utils.logger.warning("No se puede publicar evento: user_id no configurado")
                return False
            
            payload = EventPublisher._ensure_codespace_info(payload)
            
            event_id = queue.add_event(
                user_id=target_user,
                event_type=event_type,
                payload=payload
            )
            
            if utils:
                utils.logger.info(f"Evento publicado: {event_type} (ID: {event_id})")
            
            return True
            
        except Exception as e:
            if utils:
                utils.logger.error(f"Error publicando evento {event_type}: {e}")
            return False
    
    @staticmethod
    def publish_backup_error(error_type: str, error_message: str, 
                            backup_file: Optional[str] = None) -> bool:
        """
        Publica un error de backup
        
        Args:
            error_type: 'compression', 'upload', 'general'
            error_message: Mensaje descriptivo del error
            backup_file: Nombre del archivo de backup (opcional)
        
        Returns:
            bool: True si se publicó exitosamente
        """
        payload = {
            'error_type': f"backup_{error_type}",
            'error_message': error_message,
            'backup_file': backup_file
        }
        
        return EventPublisher.publish_event('backup_error', payload)
    
    @staticmethod
    def publish_backup_success(backup_file: str, size_mb: float, 
                              duration_seconds: float) -> bool:
        """
        Publica un backup exitoso
        
        Args:
            backup_file: Nombre del archivo
            size_mb: Tamaño en MB
            duration_seconds: Duración del proceso
        
        Returns:
            bool: True si se publicó exitosamente
        """
        payload = {
            'backup_file': backup_file,
            'size_mb': round(size_mb, 2),
            'duration_seconds': round(duration_seconds, 2)
        }
        
        return EventPublisher.publish_event('backup_success', payload)
    
    @staticmethod
    def publish_minecraft_status(status: str, ip: Optional[str] = None, 
                                port: int = 25565, players_online: int = 0) -> bool:
        """
        Publica el estado del servidor Minecraft
        
        Args:
            status: 'online', 'offline', 'starting', 'stopping'
            ip: IP del servidor
            port: Puerto del servidor
            players_online: Jugadores conectados
        
        Returns:
            bool: True si se publicó exitosamente
        """
        payload = {
            'status': status,
            'ip': ip,
            'port': port,
            'players_online': players_online
        }
        
        return EventPublisher.publish_event('minecraft_status', payload)
    
    @staticmethod
    def publish_codespace_status(action: str, details: Optional[dict] = None) -> bool:
        """
        Publica el estado del Codespace
        
        Args:
            action: 'started', 'stopped', 'error'
            details: Detalles adicionales
        
        Returns:
            bool: True si se publicó exitosamente
        """
        payload = {
            'action': action,
            'details': details or {}
        }
        
        return EventPublisher.publish_event('codespace_status', payload)
    
    @staticmethod
    def get_queue_stats() -> Dict:
        """Retorna estadísticas de la cola"""
        if not queue:
            return {'error': 'Queue not initialized'}
        
        try:
            return queue.get_stats()
        except Exception as e:
            return {'error': str(e)}


publisher = EventPublisher()


publish_backup_error = publisher.publish_backup_error
publish_backup_success = publisher.publish_backup_success
publish_minecraft_status = publisher.publish_minecraft_status
publish_codespace_status = publisher.publish_codespace_status


__all__ = [
    'EventPublisher',
    'publisher',
    'publish_backup_error',
    'publish_backup_success',
    'publish_minecraft_status',
    'publish_codespace_status'
]