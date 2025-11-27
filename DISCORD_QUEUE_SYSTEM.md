# Sistema de Colas Discord - Documentación

## 🎯 Overview

Sistema de notificaciones Discord basado en colas persistentes que garantiza la entrega de eventos incluso cuando el bot está offline.

### Arquitectura

```
┌──────────────────────────────┐
│    GitHub Codespace            │
│                                  │
│  ┌──────────────────────┐  │
│  │  Backup / Minecraft    │  │
│  │  publish_event()       │  │
│  └─────────┬─────────────┘  │
│           │                      │
│           │ Escribe              │
│           │                      │
│           ↓                      │
│  ┌──────────────────────┐  │
│  │  SQLite Queue          │  │
│  │  .discord_events.db    │  │
│  └─────────┬─────────────┘  │
│           │                      │
│           │ HTTP GET             │
│           │                      │
│           ↓                      │
│  ┌──────────────────────┐  │
│  │  Flask API             │  │
│  │  /discord/events       │  │
│  └──────────────────────┘  │
└──────────┬───────────────────┐
           │ HTTPS              
           │ Poll cada 30s      
           ↓                    
┌──────────────────────────────┐
│  Discord Bot (Render)        │
│                              │
│  ┌──────────────────────┐  │
│  │  Consumer Loop      │  │
│  │  - Fetch events     │  │
│  │  - Send to Discord  │  │
│  │  - Mark processed   │  │
│  └──────────────────────┘  │
└──────────────────────────────┘
```

---

## 📦 Componentes

### 1. `discord_queue.py`
**Sistema de colas persistente con SQLite**

- ✅ Almacenamiento persistente en `/workspace/.discord_events.db`
- ✅ Reintentos automáticos (hasta 3 intentos)
- ✅ Thread-safe con singleton pattern
- ✅ Cleanup automático de eventos antiguos

**Métodos principales:**
```python
queue.add_event(user_id, event_type, payload)  # Agregar evento
queue.get_pending_events(max_attempts=3)       # Obtener pendientes
queue.mark_processed(event_id)                 # Marcar como procesado
queue.mark_failed(event_id, error_msg)         # Marcar como fallido
queue.get_stats()                              # Estadísticas
```

### 2. `discord_config.py`
**Configuración centralizada**

- ✅ Auto-detección de Codespace/Render/Railway
- ✅ Singleton pattern
- ✅ Prioridad: ENV > config.py > defaults

**Uso:**
```python
from discord_config import discord_config

if discord_config.is_valid():
    print(f"User ID: {discord_config.user_id}")
    print(f"Webhook: {discord_config.webhook_url}")
```

### 3. `discord_publisher.py`
**Publisher de eventos (lado Codespace)**

- ✅ API simple para publicar eventos
- ✅ Auto-detección de Codespace info
- ✅ Funciones helper para casos comunes

**Ejemplos:**
```python
from discord_publisher import publisher

# Error de backup
publisher.publish_backup_error(
    error_type='compression',
    error_message='Error comprimiendo archivo'
)

# Backup exitoso
publisher.publish_backup_success(
    backup_file='server-2025-11-27.zip',
    size_mb=150.5,
    duration_seconds=45.2
)

# Estado de Minecraft
publisher.publish_minecraft_status(
    status='online',
    ip='192.168.1.100',
    port=25565,
    players_online=3
)
```

### 4. `discord_api.py`
**API HTTP para exponer eventos**

- ✅ Endpoints REST para el bot
- ✅ Health checks
- ✅ Estadísticas en tiempo real

**Endpoints:**
- `GET /discord/health` - Health check
- `GET /discord/events` - Obtener eventos pendientes
- `POST /discord/events/{id}/processed` - Marcar procesado
- `POST /discord/events/{id}/failed` - Marcar fallido
- `GET /discord/stats` - Estadísticas
- `POST /discord/cleanup` - Limpiar eventos antiguos

### 5. `discord_notifier.py`
**Wrapper de compatibilidad**

- ✅ Mantiene API anterior (backward compatible)
- ✅ Usa queue system si está disponible
- ✅ Fallback a envío directo HTTP

### 6. `discord_consumer_example.py`
**Consumer para el bot (lado Render/Railway)**

- ✅ Polling cada 30 segundos (configurable)
- ✅ Múltiples Codespaces
- ✅ Manejo de errores robusto
- ✅ Embeds Discord con formato

---

## 🚀 Setup

### Paso 1: Actualizar el paquete

```bash
cd /workspace/d0ce3-Addons
./create_package.sh
git add .
git commit -m "feat: add queue-based Discord system"
git push
```

### Paso 2: Actualizar módulos en el Codespace

En el addon de megacmd:
```
Menú principal > Actualizar Módulos
```

### Paso 3: Configurar variables de entorno

```bash
export DISCORD_USER_ID="tu_discord_user_id"
# Webhook URL es auto-detectada, pero puedes forzarla:
export DISCORD_WEBHOOK_URL="https://doce-bt.onrender.com/webhook/megacmd"
```

O usar el menú del addon:
```
Menú Discord > Configurar integración
```

### Paso 4: Exponer API Flask

Crea un script `start_discord_api.py` en tu Codespace:

```python
from megacmd.modules.discord_api import run_api_server

if __name__ == "__main__":
    run_api_server(host='0.0.0.0', port=8080, debug=False)
```

Ejecuta en background:
```bash
nohup python start_discord_api.py > discord_api.log 2>&1 &
```

**O integra con tu servidor existente:**

```python
from flask import Flask
from megacmd.modules.discord_api import DiscordAPI

app = Flask(__name__)

# Tus rutas existentes
@app.route('/')
def index():
    return "Hello"

# Agregar rutas Discord
discord_api = DiscordAPI(app)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
```

### Paso 5: Configurar el bot (Doce-Bt)

**En tu bot de Discord:**

1. Copia `discord_consumer_example.py` a tu proyecto:
```bash
wget https://raw.githubusercontent.com/d0ce3/d0ce3-Addons/main/discord_consumer_example.py
```

2. Importa y usa en tu bot:

```python
import discord
from discord.ext import commands
from discord_consumer_example import start_consumer

bot = commands.Bot(command_prefix='/', intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    
    # Iniciar consumer
    codespaces = [
        'https://tu-codespace-8080.app.github.dev',
        # Agregar más si tienes múltiples Codespaces
    ]
    
    consumer = await start_consumer(bot, codespaces, poll_interval=30)
    print(f"✅ Consumer iniciado para {len(codespaces)} Codespace(s)")

bot.run('TU_BOT_TOKEN')
```

3. Instalar dependencias en el bot:
```bash
pip install aiohttp
```

---

## 🧪 Testing

### Test 1: Verificar configuración
```python
from megacmd.modules.discord_config import discord_config

print(discord_config.get_status())
```

### Test 2: Publicar evento de prueba

```python
from megacmd.modules.discord_publisher import publisher

publisher.publish_backup_error(
    error_type='general',
    error_message='🧪 Evento de prueba - Sistema funcionando'
)
```

### Test 3: Verificar queue

```python
from megacmd.modules.discord_queue import queue_instance

stats = queue_instance.get_stats()
print(f"Total: {stats['total']}")
print(f"Pendientes: {stats['pending']}")
print(f"Procesados: {stats['processed']}")
print(f"Fallidos: {stats['failed']}")
```

### Test 4: Verificar API

```bash
# Health check
curl https://tu-codespace-8080.app.github.dev/discord/health

# Ver eventos pendientes
curl https://tu-codespace-8080.app.github.dev/discord/events

# Ver estadísticas
curl https://tu-codespace-8080.app.github.dev/discord/stats
```

### Test 5: Probar desde el addon

```
Menú Discord > Configurar integración > Probar notificación
```

---

## 🛠️ Mantenimiento

### Limpiar eventos antiguos

**Automático:**
Los eventos procesados se limpian automáticamente después de 7 días.

**Manual:**
```python
from megacmd.modules.discord_queue import queue_instance

deleted = queue_instance.cleanup_old_events(days=7)
print(f"Eliminados: {deleted} eventos")
```

**Vía API:**
```bash
curl -X POST "https://tu-codespace-8080.app.github.dev/discord/cleanup?days=7"
```

### Ver eventos fallidos

```python
from megacmd.modules.discord_queue import queue_instance

failed = queue_instance.get_failed_events()
for event in failed:
    print(f"#{event['id']}: {event['event_type']} - {event['error_message']}")
```

### Reintentar evento fallido

```python
queue_instance.retry_failed_event(event_id=123)
```

---

## 🐞 Troubleshooting

### Problema: Eventos no se están encolando

**Solución:**
1. Verificar configuración:
```python
from megacmd.modules.discord_config import discord_config
print(discord_config.get_status())
```

2. Verificar permisos:
```bash
ls -la /workspace/.discord_events.db
```

3. Verificar logs:
```python
from megacmd.modules.discord_publisher import publisher
print(publisher.is_enabled())
```

### Problema: Bot no recibe eventos

**Solución:**
1. Verificar que la API esté corriendo:
```bash
curl https://tu-codespace-8080.app.github.dev/discord/health
```

2. Verificar que el Codespace esté en la lista del bot

3. Ver logs del consumer en el bot

### Problema: Eventos se quedan en "pending"

**Solución:**
1. Verificar que el bot esté corriendo
2. Verificar conectividad:
```bash
curl https://tu-codespace-8080.app.github.dev/discord/events
```

3. Revisar eventos fallidos:
```python
queue_instance.get_failed_events()
```

---

## 📊 Monitoring

### Dashboard de estadísticas

```python
from megacmd.modules.discord_queue import queue_instance
from megacmd.modules.discord_config import discord_config

print("\n=== DISCORD QUEUE STATS ===")
stats = queue_instance.get_stats()
for key, value in stats.items():
    print(f"{key}: {value}")

print("\n=== CONFIG STATUS ===")
status = discord_config.get_status()
for key, value in status.items():
    print(f"{key}: {value}")
```

---

## ⚙️ Configuración avanzada

### Cambiar intervalo de polling

En el bot:
```python
consumer = await start_consumer(bot, codespaces, poll_interval=15)  # 15 segundos
```

### Múltiples Codespaces

```python
codespaces = [
    'https://codespace1-8080.app.github.dev',
    'https://codespace2-8080.app.github.dev',
    'https://codespace3-8080.app.github.dev'
]
consumer = await start_consumer(bot, codespaces)
```

### Custom event types

```python
from megacmd.modules.discord_publisher import publisher

publisher.publish_event(
    event_type='custom_event',
    payload={
        'custom_field': 'valor',
        'another_field': 123
    }
)
```

Luego en el consumer, agregar handler:
```python
if event_type == 'custom_event':
    await self._handle_custom_event(user, payload)
```

---

## 📝 Migración desde sistema anterior

**✅ No se requiere cambios en código existente**

El nuevo sistema es **100% backward compatible**. Si usabas:

```python
from discord_notifier import notificar_error_general

notificar_error_general(user_id, "mensaje")
```

Sigue funcionando, pero ahora usa el sistema de colas automáticamente.

---

## 🛡️ Ventajas del nuevo sistema

✅ **No se pierden eventos** - Persistencia en SQLite  
✅ **Funciona offline** - Queue cuando bot está caído  
✅ **Escalable** - Múltiples Codespaces → 1 bot  
✅ **Debugging fácil** - Base de datos visible  
✅ **Reintentos automáticos** - Hasta 3 intentos  
✅ **Zero config** - Auto-detección de entorno  
✅ **Backward compatible** - No rompe código existente  
✅ **Monitoreable** - Estadísticas y health checks  

---

## 🔗 Links útiles

- [Repositorio](https://github.com/d0ce3/d0ce3-Addons)
- [Consumer example](https://github.com/d0ce3/d0ce3-Addons/blob/main/discord_consumer_example.py)
- [Bot Doce-Bt](https://github.com/d0ce3/Doce-Bt) *(si es público)*

---

**Creado por d0ce3 | v1.0.0**