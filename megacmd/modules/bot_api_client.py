import requests
import os
import json
from datetime import datetime

class BotAPIClient:
    def __init__(self):
        self.bot_url = os.getenv("BOT_API_URL", "https://doce-bt.onrender.com/api")
        self.webhook_url = os.getenv("BOT_WEBHOOK_URL", "https://doce-bt.onrender.com/webhook/tunnel_notify")
        self.discord_user_id = os.getenv("DISCORD_USER_ID")
        self.config_cache_file = "/tmp/bot_config_cache.json"
        
        if not self.discord_user_id:
            print("⚠️  DISCORD_USER_ID no configurado en variables de entorno")
    
    def get_config(self):
        if not self.discord_user_id:
            print("❌ No se puede obtener config sin DISCORD_USER_ID")
            return self._load_from_cache()
        
        try:
            print(f"🔍 Consultando configuración del bot para usuario {self.discord_user_id}...")
            
            response = requests.get(
                f"{self.bot_url}/user/config/{self.discord_user_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                config = response.json()
                print(f"✅ Configuración obtenida del bot")
                print(f"   Webhook URL: {config.get('webhook_url')}")
                print(f"   Codespace: {config.get('codespace_name')}")
                
                self._save_to_cache(config)
                return config
            
            elif response.status_code == 404:
                print("⚠️  Usuario no encontrado en el bot")
                print("   Usa /setup en Discord primero")
                return self._load_from_cache()
            
            else:
                print(f"⚠️  Error del bot: HTTP {response.status_code}")
                return self._load_from_cache()
        
        except requests.exceptions.Timeout:
            print("⚠️  Timeout consultando el bot, usando caché...")
            return self._load_from_cache()
        
        except Exception as e:
            print(f"⚠️  Error consultando el bot: {e}")
            return self._load_from_cache()
    
    def notify_tunnel(self, tunnel_url, tunnel_type="cloudflare", tunnel_port=25565, voicechat_address=None):
        if not self.discord_user_id:
            print("❌ No se puede notificar sin DISCORD_USER_ID")
            return False
        
        try:
            print(f"📤 Notificando al bot sobre el tunnel...")
            print(f"   URL: {tunnel_url}")
            print(f"   Tipo: {tunnel_type}")
            
            codespace_name = os.getenv("CODESPACE_NAME", "unknown")
            
            payload = {
                "user_id": self.discord_user_id,
                "codespace_name": codespace_name,
                "tunnel_url": tunnel_url,
                "tunnel_port": tunnel_port,
                "tunnel_type": tunnel_type,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            if voicechat_address:
                payload["voicechat_address"] = voicechat_address
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Bot notificado exitosamente")
                result = response.json()
                
                if result.get("notification_sent"):
                    print("   📨 Usuario notificado por DM")
                
                return True
            else:
                print(f"⚠️  Error notificando al bot: HTTP {response.status_code}")
                return False
        
        except Exception as e:
            print(f"❌ Error notificando al bot: {e}")
            return False
    
    def update_tunnel(self, tunnel_url, tunnel_type="cloudflare", tunnel_port=25565):
        if not self.discord_user_id:
            print("❌ No se puede actualizar sin DISCORD_USER_ID")
            return False
        
        try:
            print(f"🔄 Actualizando tunnel en el bot...")
            
            payload = {
                "discord_user_id": self.discord_user_id,
                "tunnel_url": tunnel_url,
                "tunnel_type": tunnel_type,
                "tunnel_port": tunnel_port
            }
            
            response = requests.post(
                f"{self.bot_url}/user/tunnel",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Tunnel actualizado en el bot")
                return True
            else:
                print(f"⚠️  Error actualizando: HTTP {response.status_code}")
                return False
        
        except Exception as e:
            print(f"❌ Error actualizando tunnel: {e}")
            return False
    
    def _save_to_cache(self, config):
        try:
            with open(self.config_cache_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"💾 Configuración guardada en caché local")
        except Exception as e:
            print(f"⚠️  Error guardando caché: {e}")
    
    def _load_from_cache(self):
        try:
            if os.path.exists(self.config_cache_file):
                with open(self.config_cache_file, 'r') as f:
                    config = json.load(f)
                print(f"💾 Usando configuración desde caché local")
                return config
        except Exception as e:
            print(f"⚠️  Error cargando caché: {e}")
        
        return None
    
    def get_webhook_url(self):
        config = self.get_config()
        if config:
            return config.get("webhook_url", self.webhook_url)
        return self.webhook_url