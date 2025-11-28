# ... (resto de imports y código arriba igual)
from megacmd.modules.auto_webserver_setup import auto_configurar_web_server

def configurar_integracion_completa():
    # ... (resto del código igual hasta)
    if exito:
        print(verde("\n✓ Configuración completa y permanente"))
        print("\nLas variables están configuradas en ~/.bashrc")
        print("Se cargarán automáticamente en cada inicio.\n")
        print(mb("Resumen:"))
        print(f"  User ID: {user_id}")
        print(f"  Webhook: {webhook_url}\n")
        print(verde("✓ Notificaciones de backup activadas"))
        print(verde("✓ Sistema de cola iniciado"))
        logger.log("INFO", f"Integración Discord configurada - User ID: {user_id}")
        print("\n🔧 Preparando servidor web para control automático...")
        auto_configurar_web_server()
    else:
        print(f"{AMARILLO}\n⚠ Configuración parcial{RESET}")
        print("Deberás exportar manualmente las variables:")
        print(f"  export DISCORD_USER_ID='{user_id}'")
        print(f"  export DISCORD_WEBHOOK_URL='{webhook_url}'")
    utils.pausar()
# ... (resto del código igual abajo)
