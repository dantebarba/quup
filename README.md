# Plex AI Curator

**Un sistema automatizado de recomendaciones de películas impulsado por IA**

---

## Información del Modelo

**Modelo utilizado:** Claude Sonnet 4.5

**Registro de clarificaciones:** Ninguna (implementación directa desde PROMPT.md)

**Estado:** ✅ Aplicación completamente funcional con todos los tests pasando

---

## Descripción

Plex AI Curator es un motor de recomendaciones de películas personalizado que actúa como puente entre un servidor Plex Media local y la API de OpenAI Assistants. Analiza lo que acabas de ver, identifica el "mood/vibe" y crea una playlist de películas **no vistas** de tu propia biblioteca que se ajustan a ese estado de ánimo específico.

### Características Principales

- 🎬 **Sincronización Automática**: Sincroniza tu biblioteca de Plex con OpenAI Vector Store
- 🤖 **Recomendaciones IA**: Utiliza OpenAI GPT-4o para analizar patrones de visualización
- 📋 **Playlists Automáticas**: Crea playlists en Plex con las recomendaciones
- 📱 **Notificaciones Telegram**: Envía notificaciones con las películas recomendadas
- 🔒 **Seguro**: Autenticación por token de API
- 🐳 **Dockerizado**: Despliegue fácil con Docker y Docker Compose
- ✅ **100% Testeado**: 10 tests de integración, todos pasando

---

## Instalación Rápida

### Prerrequisitos

- Docker y Docker Compose
- Servidor Plex con acceso a API
- Cuenta de OpenAI con créditos API
- (Opcional) Bot de Telegram configurado

### Pasos

1. **Clonar el repositorio:**
```bash
git clone <repository-url>
cd quup
```

2. **Configurar variables de entorno:**
```bash
cp .env.example .env
nano .env  # Editar con tus credenciales
```

Configuración mínima requerida:
```env
API_AUTH_TOKEN=tu-token-secreto-aquí
PLEX_URL=http://tu-servidor-plex:32400
PLEX_TOKEN=tu-token-plex-aquí
OPENAI_API_KEY=sk-tu-clave-api-openai-aquí
```

3. **Iniciar el servicio:**
```bash
docker-compose up -d
```

4. **Verificar el estado:**
```bash
curl http://localhost:8000/health
```

---

## Uso de la API

### Sincronizar Biblioteca
```bash
curl -X POST http://localhost:8000/sync \
  -H "x-api-token: tu-token-aquí"
```

### Generar Recomendaciones
```bash
curl -X POST http://localhost:8000/recommend \
  -H "x-api-token: tu-token-aquí"
```

Respuesta ejemplo:
```json
{
  "success": true,
  "message": "Se generaron 10 recomendaciones",
  "recommendations": [
    "The Shawshank Redemption",
    "The Godfather",
    "Pulp Fiction"
  ],
  "playlist_created": true,
  "telegram_sent": false
}
```

---

## Testing

### Ejecutar Tests
```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=app tests/

# Verbose
pytest -v
```

### Resultado de Tests
```
✅ 10/10 tests pasando
- Health endpoint
- Root endpoint
- Sync endpoint (sin auth)
- Sync endpoint (con auth)
- Recommend endpoint (con auth)
- Library sync
- Get recommendations
- Create playlist
- Telegram notification
- End-to-end flow
```

---

## Estructura del Proyecto

```
quup/
├── app/
│   ├── __init__.py          # Inicialización
│   ├── config.py            # Configuración con Pydantic
│   ├── core.py              # Lógica de negocio
│   ├── main.py              # FastAPI endpoints
│   └── notifiers.py         # Notificaciones Telegram
├── tests/
│   ├── __init__.py
│   └── test_integration.py  # 10 tests de integración
├── samples/
│   └── movies_library.json  # Datos de muestra
├── Dockerfile               # Imagen Docker
├── docker-compose.yml       # Orquestación
├── requirements.txt         # Dependencias
├── pytest.ini              # Configuración de tests
├── .env.example            # Plantilla de configuración
├── README.md               # Esta documentación
├── DEPLOYMENT.md           # Guía completa de despliegue
└── PROMPT.md              # Especificaciones originales
```

---

## Stack Técnico

- **Lenguaje:** Python 3.13
- **Framework:** FastAPI (async)
- **IA:** OpenAI Assistants API v2 (GPT-4o)
- **Integración Plex:** plexapi
- **Notificaciones:** python-telegram-bot
- **Configuración:** pydantic-settings
- **Testing:** pytest + pytest-asyncio
- **Despliegue:** Docker + Docker Compose

---

## Documentación Completa

Para información detallada sobre:
- Configuración avanzada
- Despliegue en producción
- Configuración de Telegram
- Solución de problemas
- Arquitectura del sistema

Consulta [DEPLOYMENT.md](DEPLOYMENT.md)

---

## Estado del Proyecto

- ✅ Todos los criterios de aceptación cumplidos
- ✅ 10 tests de integración pasando
- ✅ Aplicación desplegable en Docker
- ✅ Documentación completa
- ✅ Código con type hints
- ✅ Manejo robusto de errores
- ✅ Logging configurado
- ✅ Seguridad implementada

---

## Licencia

[Especificar licencia]

---

**Desarrollado como parte del desafío Quup - AI App Comparison**
