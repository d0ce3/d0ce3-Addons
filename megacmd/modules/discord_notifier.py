import os
import json
from datetime import datetime

# Intentar importar requests, si falla usar urllib
try:
    import requests
    USAR_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    USAR_REQUESTS = False
    print("⚠️  requests no disponible, usando urllib")


# URL del webhook del bot (configurable vía variable de entorno)
WEBHOOK_URL = os.getenv(
    "DISCORD_WEBHOOK_URL",
    "http://localhost:10000/webhook/megacmd"  # Cambiar en producción
)


def enviar_notificacion_error(
    user_id: str,
    error_type: str,
    error_message: str,
    codespace_name: str = None
):
    """
    Envía una notificación de error al bot de Discord
    
    Args:
        user_id: ID del usuario de Discord
        error_type: Tipo de error ('backup_compression', 'backup_upload', 'backup_general')
        error_message: Mensaje descriptivo del error
        codespace_name: Nombre del codespace (opcional)
    
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        # Detectar nombre del codespace si no se proporcionó
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
            # Usar requests
            response = requests.post(
                WEBHOOK_URL,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Notificación enviada a Discord para usuario {user_id}")
                return True
            else:
                print(f"⚠️  Error enviando notificación: HTTP {response.status_code}")
                try:
                    print(f"   Respuesta: {response.text[:200]}")
                except:
                    pass
                return False
        else:
            # Usar urllib
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                WEBHOOK_URL,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            response = urllib.request.urlopen(req, timeout=10)
            
            if response.status == 200:
                print(f"✅ Notificación enviada a Discord para usuario {user_id}")
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
    """
    Notifica un error durante la compresión del backup
    
    Args:
        user_id: ID del usuario de Discord
        error_message: Descripción del error
    
    Returns:
        bool: True si se envió correctamente
    """
    return enviar_notificacion_error(
        user_id=user_id,
        error_type="backup_compression",
        error_message=error_message
    )


def notificar_error_subida(user_id: str, error_message: str):
    """
    Notifica un error durante la subida a MEGA
    
    Args:
        user_id: ID del usuario de Discord
        error_message: Descripción del error
    
    Returns:
        bool: True si se envió correctamente
    """
    return enviar_notificacion_error(
        user_id=user_id,
        error_type="backup_upload",
        error_message=error_message
    )


def notificar_error_general(user_id: str, error_message: str):
    """
    Notifica un error general en el backup
    
    Args:
        user_id: ID del usuario de Discord
        error_message: Descripción del error
    
    Returns:
        bool: True si se envió correctamente
    """
    return enviar_notificacion_error(
        user_id=user_id,
        error_type="backup_general",
        error_message=error_message
    )


def obtener_user_id():
    """
    Obtiene el user_id del propietario desde el archivo de configuración
    o desde una variable de entorno
    
    Returns:
        str: User ID o None si no está configurado
    """
    # Intentar desde variable de entorno primero
    user_id = os.getenv("DISCORD_USER_ID")
    if user_id:
        return user_id
    
    # Intentar desde archivo de configuración
    try:
        config = CloudModuleLoader.load_module("config")
        if config:
            user_id = config.CONFIG.get("discord_user_id")
            if user_id:
                return user_id
    except:
        pass
    
    return None


def verificar_configuracion():
    estado = {
        "user_id": obtener_user_id(),
        "webhook_url": WEBHOOK_URL,
        "codespace_name": os.getenv("CODESPACE_NAME"),
        "configurado": False
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
    
    if not WEBHOOK_URL or WEBHOOK_URL == "http://localhost:10000/webhook/megacmd":
        print("⚠️  Advertencia: Usando URL de webhook por defecto (localhost)")
        print("   Configura DISCORD_WEBHOOK_URL con la URL real de tu bot")
    
    print(f"\n🧪 Enviando notificación de prueba a {user_id}...")
    
    resultado = notificar_error_general(
        user_id,
        "🧪 Notificación de prueba desde MegaCMD. Si recibiste esto, la configuración funciona correctamente."
    )
    
    if resultado:
        print("✅ Notificación enviada exitosamente")
        print("   Revisa tus DMs en Discord")
        return True
    else:
        print("❌ Error enviando notificación")
        print("\n🔍 Verifica:")
        print("   1. Que el bot esté corriendo")
        print("   2. Que DISCORD_WEBHOOK_URL sea correcta")
        print("   3. Que tengas DMs abiertos en Discord")
        return False


# Script de prueba
if __name__ == "__main__":
    print("=" * 70)
    print("🧪 PRUEBA DE NOTIFICACIONES DISCORD")
    print("=" * 70 + "\n")
    
    # Mostrar configuración actual
    estado = verificar_configuracion()
    
    print("📊 Configuración actual:")
    print(f"   User ID: {estado['user_id'] or '❌ No configurado'}")
    print(f"   Webhook URL: {estado['webhook_url']}")
    print(f"   Codespace: {estado['codespace_name'] or 'No detectado'}")
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