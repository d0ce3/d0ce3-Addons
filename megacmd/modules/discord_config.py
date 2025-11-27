"""
Gestor centralizado de configuración Discord
Singleton que unifica todas las fuentes de configuración
"""
import os
import subprocess
from typing import Optional

class DiscordConfig:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._load()
        self._initialized = True
    
    def _load(self):
        """Carga la configuración desde múltiples fuentes con prioridad"""
        self.user_id = self._get_user_id()
        self.webhook_url = self._get_webhook_url()
        self.codespace_name = os.getenv("CODESPACE_NAME")
        self.codespace_url = self._detect_codespace_url()
    
    def _get_user_id(self) -> Optional[str]:
        """Obtiene el User ID con prioridad: ENV > config.py"""
        user_id = os.getenv("DISCORD_USER_ID")
        if user_id:
            return user_id
        
        try:
            config = CloudModuleLoader.load_module("config")
            if config:
                user_id = config.CONFIG.get("discord_user_id")
                if user_id:
                    return user_id
        except:
            pass
        
        return None
    
    def _get_webhook_url(self) -> Optional[str]:
        """Obtiene la URL del webhook con auto-detección"""
        webhook = os.getenv("DISCORD_WEBHOOK_URL")
        if webhook and webhook != "http://localhost:10000/webhook/megacmd":
            return webhook
        
        detected = self._detect_webhook_url()
        if detected:
            return detected
        
        return webhook
    
    def _detect_webhook_url(self) -> Optional[str]:
        """
        Auto-detecta la URL del webhook según el entorno
        Prioridad: Render > Railway > Hardcoded
        """
        render_external = os.getenv("RENDER_EXTERNAL_URL")
        if render_external:
            return f"{render_external}/webhook/megacmd"
        
        render_service = os.getenv("RENDER_SERVICE_NAME")
        if render_service:
            return f"https://{render_service}.onrender.com/webhook/megacmd"
        
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
        if railway_domain:
            return f"https://{railway_domain}/webhook/megacmd"
        
        railway_static = os.getenv("RAILWAY_STATIC_URL")
        if railway_static:
            return f"{railway_static}/webhook/megacmd"
        
        return "https://doce-bt.onrender.com/webhook/megacmd"
    
    def _detect_codespace_url(self) -> Optional[str]:
        """
        Detecta la URL pública del Codespace
        Formato: https://{codespace_name}-{port}.app.github.dev
        """
        if not self.codespace_name:
            return None
        
        return f"https://{self.codespace_name}-8080.app.github.dev"
    
    def is_valid(self) -> bool:
        """Verifica si la configuración es válida"""
        return bool(self.user_id and self.webhook_url)
    
    def reload(self):
        """Recarga la configuración"""
        self._load()
    
    def get_status(self) -> dict:
        """Retorna el estado actual de la configuración"""
        return {
            'user_id': bool(self.user_id),
            'user_id_value': self.user_id[:8] + '...' if self.user_id else None,
            'webhook_url': bool(self.webhook_url),
            'webhook_url_value': self.webhook_url if self.webhook_url else None,
            'codespace_name': self.codespace_name,
            'codespace_url': self.codespace_url,
            'is_valid': self.is_valid()
        }
    
    def __repr__(self):
        return f"<DiscordConfig valid={self.is_valid()} user_id={bool(self.user_id)} webhook={bool(self.webhook_url)}>"


discord_config = DiscordConfig()


__all__ = [
    'DiscordConfig',
    'discord_config'
]