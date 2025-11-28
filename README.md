# 🛠️ d0ce3-Addons

**Sistema de addons y herramientas para Minecraft Server en GitHub Codespaces**

Colección de addons diseñados específicamente para MEGAcmd en entornos de GitHub Codespaces, con integración completa al bot de Discord [Doce-Bt](https://github.com/d0ce3/Doce-Bt). Optimizado para ejecutarse en el entorno MSX.

---

## ⚠️ Importante: Entorno MSX

**Este proyecto está diseñado exclusivamente para ejecutarse en el entorno MSX.**

### ¿Qué es MSX?
MSX es un entorno pre-configurado para Minecraft en GitHub Codespaces que incluye:
- Servidor Minecraft optimizado
- Python 3.9+
- Estructura de directorios específica
- Variables de entorno configuradas

### Requisitos del Sistema
- **Entorno**: GitHub Codespace con MSX
- **MEGAcmd**: Instalado y configurado
- **Python**: 3.9 o superior
- **Cuenta MEGA**: Para backups en la nube
- **Bot Discord**: [Doce-Bt](https://github.com/d0ce3/Doce-Bt) desplegado

---

## ✨ Características Principales

### 📦 Sistema de Backups Automatizado
- **Compresión incremental**: Backups optimizados con .zip
- **Subida automática a MEGA**: Integración nativa con MEGAcmd
- **Programación flexible**: Backups automáticos cada X minutos
- **Gestión inteligente**: Limpieza automática de backups antiguos
- **Notificaciones en tiempo real**: Alertas en Discord sobre éxito/fallos

### 🔔 Sistema de Eventos y Notificaciones
- **Cola de eventos**: Sistema SQLite para eventos asincrónicos
- **Notificaciones Discord**: Envío automático vía webhook
- **Polling inteligente**: El bot de Discord consulta eventos periódicamente
- **Reintentos automáticos**: Hasta 3 intentos para eventos fallidos
- **Tipos de eventos soportados**:
  - ✅ Backups exitosos
  - ❌ Errores en backups
  - 🎮 Estado del servidor Minecraft
  - 🖥️ Estado del Codespace

### 🎮 Monitoreo de Minecraft
- **Estado en tiempo real**: Detecta cuando el servidor inicia/detiene
- **Información de jugadores**: Cantidad de jugadores online
- **IP automática**: Detecta y comparte la IP del servidor
- **Integración con Discord**: Notificaciones automáticas de estado

### 📂 Gestión de Archivos
- **Listado inteligente**: Visualización de archivos con tamaños
- **Descarga/subida MEGA**: Interfaz simplificada para MEGAcmd
- **Gestión de mundos**: Backup selectivo de carpetas
- **Limpieza automatizada**: Elimina archivos antiguos

### 🔧 Utilidades del Sistema
- **Logger centralizado**: Sistema de logs con rotación
- **Configuración JSON**: Gestión persistente de configuraciones
- **Detección de entorno**: Identifica automáticamente Render/Railway
- **Carga dinámica de módulos**: Sistema de plugins modular

---

## 📖 Uso

### Menú Principal

```bash
mega-cmd
menu
```

**Opciones disponibles:**

```
┌────────────────────────────────────────────────┐
│ 1. Gestión de backups                         │
│ 2. Gestión de archivos                        │
│ 3. Configuración de backups automáticos       │
│ 4. Logs                                        │
│ 5. Integración Discord                         │
│ 6. Salir                                       │
└────────────────────────────────────────────────┘
```

### Sistema de Backups

#### Backup Manual
```bash
menu → 1 → 1  # Crear backup completo
```

#### Configurar Backups Automáticos
```bash
menu → 3 → 1  # Activar/configurar
# Elige intervalo: 1, 2, 3, 6, 12, 24 horas
```

#### Ver Estado de Backups
```bash
menu → 3 → 2  # Ver configuración actual
```

### Integración con Discord

#### Configuración Inicial

```bash
menu → 5 → 2  # Configurar integración
```

El asistente te pedirá:

1. **Discord User ID**
   - Activa Modo Desarrollador en Discord
   - Clic derecho en tu perfil → Copiar ID

2. **Webhook URL** (detección automática)
   - El sistema detecta automáticamente la URL del bot
   - Si no, ingresa manualmente:
     - Render: `https://nombre-app.onrender.com/webhook/megacmd`
     - Railway: `https://nombre-app.up.railway.app/webhook/megacmd`

#### Información del Bot

```bash
menu → 5 → 1  # Ver información completa
```

Muestra:
- Características del bot
- Enlace de invitación
- Comandos disponibles
- Pasos de configuración

---

## 🔧 Sistema de Eventos

### Arquitectura

El sistema utiliza una arquitectura de polling con cola de eventos:

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  MSX Codespace  │──────│  Discord Queue   │──────│   Doce-Bt Bot   │
│                 │      │   (SQLite DB)    │      │   (Render/Fly)  │
│  - Minecraft    │      │                  │      │                 │
│  - d0ce3-Addons │      │  - Eventos       │      │  - Polling      │
│  - MEGAcmd      │      │  - Reintentos    │      │  - Notifica DM  │
└─────────────────┘      └──────────────────┘      └─────────────────┘
```

### Flujo de Eventos

1. **Generación**: El addon genera un evento (ej: backup completado)
2. **Almacenamiento**: Se guarda en la cola SQLite local
3. **Exposición**: Se expone vía endpoint HTTP en puerto 8080
4. **Polling**: El bot de Discord consulta cada 30 segundos
5. **Procesamiento**: El bot envía notificación al usuario
6. **Confirmación**: El evento se marca como procesado

### Endpoints Disponibles

```
GET  /discord/events           # Obtener eventos pendientes
POST /discord/events/{id}/processed  # Marcar como procesado
POST /discord/events/{id}/failed     # Marcar como fallido
```

### Tipos de Eventos

```python
# Backup exitoso
{
  "event_type": "backup_success",
  "payload": {
    "backup_file": "backup_2024-11-27_22-00.tar.gz",
    "size_mb": 256.4,
    "duration_seconds": 45.2,
    "codespace_name": "legendary-space-disco"
  }
}

# Error en backup
{
  "event_type": "backup_error",
  "payload": {
    "error_type": "compression",
    "error_message": "No space left on device",
    "codespace_name": "legendary-space-disco"
  }
}

# Estado de Minecraft
{
  "event_type": "minecraft_status",
  "payload": {
    "status": "online",
    "ip": "legendary-space-disco-25565.app.github.dev",
    "port": 25565,
    "players_online": 3
  }
}
```

---

---

## 🔌 Integración con Doce-Bt

### Configuración del Bot

1. **En Discord** (con el bot):
   ```
   /setup token:<tu-github-token>
   /vincular codespace:<nombre-de-tu-codespace>
   ```

2. **En MSX** (este addon):
   ```
   menu → 5 → 2  # Configurar integración
   ```

3. **Verificar conexión**:
   ```
   menu → 5 → 3  # Ver información de conexión
   /addon_stats  # En Discord
   ```

### Comandos Discord Relacionados

- `/addon_stats` - Ver estadísticas del sistema de eventos
- `/start` - Iniciar Codespace
- `/stop` - Detener Codespace
- `/status` - Ver estado del Codespace
- `/mc_status` - Estado del servidor Minecraft

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas:

1. Fork el repositorio
2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m 'Agregar nueva funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Abre un Pull Request

### Guías de Contribución

- Sigue el estilo de código existente
- Documenta nuevas funciones
- Agrega tests cuando sea posible
- Actualiza el README si es necesario

---

## 📝 Licencia

Este proyecto es de código abierto bajo la licencia MIT.

---

## 📧 Contacto y Soporte

- **GitHub**: [@d0ce3](https://github.com/d0ce3)
- **Repositorio**: [d0ce3-Addons](https://github.com/d0ce3/d0ce3-Addons)
- **Bot Discord**: [Doce-Bt](https://github.com/d0ce3/Doce-Bt)
- **Issues**: [Reportar problemas](https://github.com/d0ce3/d0ce3-Addons/issues)

---

**⚡ Hecho con ❤️ por d0ce3**

**Versión actual**: 1.0.1  
**Última actualización**: Noviembre 2024
