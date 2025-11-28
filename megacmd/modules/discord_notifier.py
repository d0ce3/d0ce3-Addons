import os
import json
from datetime import datetime

try:
    import requests
    USAR_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    USAR_REQUESTS = False
    print("⚠️  requests no disponible, usando urllib")

try:
    discord_publisher_mod = CloudModuleLoader.load_module("discord_publisher")
    discord_config_mod = CloudModuleLoader.load_module("discord_config")
    
    publisher = discord_publisher_mod.publisher
    config = discord_config_mod.discord_config
    QUEUE_SYSTEM_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Sistema de colas no disponible, usando modo directo: {e}")
    publisher = None
    config = None
    QUEUE_SYSTEM_AVAILABLE = False

WEBHOOK_URL = os.getenv(
    "DISCORD_WEBHOOK_URL",
    "http://localhost:10000/webhook/megacmd"
)


def enviar_notificacion_error(
    user_id: str,
    error_type: str,
    error_message: str,
    codespace_name: str = None
):
    """
    Envía una notificación de error al bot de Discord
    
    NUEVO: Usa sistema de colas si está disponible, fallback a HTTP directo
    
    Args:
        user_id: ID del usuario de Discord
        error_type: Tipo de error ('backup_compression', 'backup_upload', 'backup_general')
        error_message: Mensaje descriptivo del error
        codespace_name: Nombre del codespace (opcional)
    
    Returns:
        bool: True si se envió correctamente
    """
    if QUEUE_SYSTEM_AVAILABLE and publisher:
        try:
            payload = {
                'error_type': error_type,
                'error_message': error_message,
                'codespace_name': codespace_name or os.getenv("CODESPACE_NAME", "Desconocido")
            }
            
            success = publisher.publish_event(
                event_type='backup_error',
                payload=payload,
                user_id=user_id
            )
            
            if success:
                print(f"✅ Notificación encolada para usuario {user_id}")
                return True
            else:
                print("⚠️  Error encolando, intentando envío directo...")
        except Exception as e:
            print(f"⚠️  Error usando sistema de colas: {e}")
    
    return _enviar_directo(user_id, error_type, error_message, codespace_name)


def _enviar_directo(user_id: str, error_type: str, error_message: str, codespace_name: str = None):
    try:
        if not codespace_name:
            codespace_name = os.getenv("CODESPACE_NAME", "Desconocido")
        
        payload = {
            "user_id": user_id,
            "error_type": error_type,
            "error_message": error_message,
            "codespace_name": codespace_name,
            "timestamp": datetime.now().isoformat()
        }
        
        if USAR_REQUESTS:
            response = requests.post(
                WEBHOOK_URL,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Notificación enviada directamente a Discord para usuario {user_id}")
                return True
            else:
                print(f"⚠️  Error enviando notificación: HTTP {response.status_code}")
                try:
                    print(f"   Respuesta: {response.text[:200]}")
                except:
                    pass
                return False
        else:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                WEBHOOK_URL,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            response = urllib.request.urlopen(req, timeout=10)
            
            if response.status == 200:
                print(f"✅ Notificación enviada directamente a Discord para usuario {user_id}")
                return True
            else:
                print(f"⚠️  Error enviando notificación: HTTP {response.status}")
                return False
            
    except Exception as e:
        error_name = type(e).__name__
        
        if "Timeout" in error_name or "timeout" in str(e).lower():
            print("⚠️  Timeout al enviar notificación a Discord")
        elif "Connection" in error_name or "connection" in str(e).lower():
            print("⚠️  No se pudo conectar al bot de Discord")
            print(f"   URL: {WEBHOOK_URL}")
            print("   Verifica que el bot esté corriendo y la URL sea correcta")
        else:
            print(f"⚠️  Error enviando notificación: {e}")
        
        return False


def notificar_error_compresion(user_id: str, error_message: str):
    if QUEUE_SYSTEM_AVAILABLE and publisher:
        return publisher.publish_backup_error('compression', error_message)
    
    return enviar_notificacion_error(
        user_id=user_id,
        error_type="backup_compression",
        error_message=error_message
    )


def notificar_error_subida(user_id: str, error_message: str):
    if QUEUE_SYSTEM_AVAILABLE and publisher:
        return publisher.publish_backup_error('upload', error_message)
    
    return enviar_notificacion_error(
        user_id=user_id,
        error_type="backup_upload",
        error_message=error_message
    )


def notificar_error_general(user_id: str, error_message: str):
    if QUEUE_SYSTEM_AVAILABLE and publisher:
        return publisher.publish_backup_error('general', error_message)
    
    return enviar_notificacion_error(
        user_id=user_id,
        error_type="backup_general",
        error_message=error_message
    )


def obtener_user_id():
    if QUEUE_SYSTEM_AVAILABLE and config:
        return config.user_id
    
    user_id = os.getenv("DISCORD_USER_ID")
    if user_id:
        return user_id
    
    try:
        config_mod = CloudModuleLoader.load_module("config")
        if config_mod:
            user_id = config_mod.CONFIG.get("discord_user_id")
            if user_id:
                return user_id
    except:
        pass
    
    return None


def verificar_configuracion():
    if QUEUE_SYSTEM_AVAILABLE and config:
        status = config.get_status()
        return {
            "user_id": config.user_id,
            "webhook_url": config.webhook_url,
            "codespace_name": config.codespace_name,
            "configurado": config.is_valid(),
            "queue_system": True
        }
    
    estado = {
        "user_id": obtener_user_id(),
        "webhook_url": WEBHOOK_URL,
        "codespace_name": os.getenv("CODESPACE_NAME"),
        "configurado": False,
        "queue_system": False
    }
    
    estado["configurado"] = bool(estado["user_id"] and estado["webhook_url"])
    
    return estado


def probar_notificacion():
    user_id = obtener_user_id()
    
    if not user_id:
        print("❌ Error: DISCORD_USER_ID no configurado")
        print("\n💡 Configura tu User ID:")
        print("   1. Usa 'Configurar Discord User ID' en el menú")
        print("   2. O exporta la variable:")
        print("      export DISCORD_USER_ID='tu_id_aqui'")
        return False
    
    estado = verificar_configuracion()
    
    if estado.get('queue_system'):
        print(f"\n📦 Sistema de colas: ✅ Activo")
    else:
        print(f"\n📦 Sistema de colas: ⚠️  No disponible (modo directo)")
        if not WEBHOOK_URL or WEBHOOK_URL == "http://localhost:10000/webhook/megacmd":
            print("⚠️  Advertencia: Usando URL de webhook por defecto (localhost)")
            print("   Configura DISCORD_WEBHOOK_URL con la URL real de tu bot")
    
    print(f"\n🧪 Enviando notificación de prueba a {user_id}...")
    
    resultado = notificar_error_general(
        user_id,
        "🧪 Notificación de prueba desde MegaCMD. Si recibiste esto, la configuración funciona correctamente."
    )
    
    if resultado:
        print("✅ Notificación enviada/encolada exitosamente")
        if estado.get('queue_system'):
            print("   El bot la procesará en el próximo polling")
        else:
            print("   Revisa tus DMs en Discord")
        return True
    else:
        print("❌ Error enviando notificación")
        print("\n🔍 Verifica:")
        if not estado.get('queue_system'):
            print("   1. Que el bot esté corriendo")
            print("   2. Que DISCORD_WEBHOOK_URL sea correcta")
            print("   3. Que tengas DMs abiertos en Discord")
        else:
            print("   1. Que el sistema de colas esté inicializado")
            print("   2. Que tengas permisos de escritura en /workspace")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("🧪 PRUEBA DE NOTIFICACIONES DISCORD")
    print("=" * 70 + "\n")
    
    estado = verificar_configuracion()
    
    print("📊 Configuración actual:")
    print(f"   User ID: {estado['user_id'] or '❌ No configurado'}")
    print(f"   Webhook URL: {estado['webhook_url']}")
    print(f"   Codespace: {estado['codespace_name'] or 'No detectado'}")
    print(f"   Sistema de colas: {'✅ Activo' if estado.get('queue_system') else '❌ Desactivado'}")
    print(f"   Estado: {'✅ Configurado' if estado['configurado'] else '❌ Incompleto'}")
    print()
    
    if not estado['configurado']:
        print("⚠️  Configuración incompleta")
        print("\nPara configurar:")
        print("   export DISCORD_USER_ID='tu_id_aqui'")
        print("   export DISCORD_WEBHOOK_URL='https://tu-bot.url/webhook/megacmd'")
        print()
        exit(1)
    
    probar_notificacion()
    
    print("\n" + "=" * 70)