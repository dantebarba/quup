# Plex AI Curator

Un sistema automatizado de recomendaciones de películas que actúa como puente entre tu servidor Plex local y la API de OpenAI Assistants.

## El Problema

Tienes una biblioteca masiva de películas almacenadas localmente, pero sufres de "parálisis por elección". ¿Qué ver a continuación?

## La Solución

Un sistema automatizado que analiza lo que **acabas de ver**, identifica el "mood/vibe" y crea una playlist de películas **no vistas** de tu propia biblioteca que se ajusten a ese estado de ánimo específico.

## Características

### A. Base de Conocimiento (Proceso de Sincronización)
- **Trigger:** Tarea en segundo plano asíncrona (vía API `/sync`)
- **Fuente:** Obtiene TODAS las películas de Plex
- **Transformación de Datos:** 
  - Crea un dataset JSON con metadatos ricos: `Title`, `Year`, `Director`, `Genre`, `Plot Summary`, `Main Actors`, `Rating`
  - Incluye campo `status`: "Watched" o "Unwatched" (basado en `viewCount`)
- **Destino:** Sube el JSON a un **Vector Store** de OpenAI adjunto a un Assistant específico
- **Limpieza:** Elimina archivos antiguos del Vector Store antes de subir la nueva versión

### B. Motor de Recomendaciones (Proceso de Análisis)
- **Trigger:** Endpoint API `/recommend`
- **Contexto de Entrada:** Obtiene los últimos 5-10 elementos del historial de Plex del usuario
- **Persona de IA:** El Asistente de OpenAI actúa como un curador experto de cine
- **Estrategia de Prompt:**
  1. Analiza el historial reciente para temas, tono, ritmo y estilo del director
  2. Busca en el Vector Store (Base de Conocimiento)
  3. **Restricción:** ESTRICTAMENTE recomienda películas donde `status` es "Unwatched"
  4. **Objetivo:** Selecciona 10-15 títulos que mejor continúen la "sesión" o "vibe" del historial reciente
  5. **Salida:** Una lista limpia de títulos de películas

### C. La Entrega (Experiencia del Usuario)
Una vez generadas las recomendaciones, el sistema actúa:
1. **Playlist de Plex:** Crea/Sobrescribe una playlist llamada "Recomendado por IA" con los elementos coincidentes
2. **Notificación (Telegram):** Envía un mensaje con la lista de películas
3. **Localización:** Todo el texto orientado al usuario (nombres de playlist, mensajes de Telegram, logs) está en **ESPAÑOL**

## Arquitectura Técnica

### Stack Principal
- **Lenguaje:** Python 3.13
- **Framework API:** FastAPI (maneja endpoints async y `BackgroundTasks`)
- **Motor de IA:** OpenAI Assistants API v2 (herramienta `file_search` habilitada)
- **Integración:** Wrapper `plexapi`

### Configuración (Variables de Entorno)
La aplicación es compatible con 12-factor app. Usa `pydantic-settings`.

**Seguridad:**
- `API_AUTH_TOKEN` (Validación de cabecera)

**Plex:**
- `PLEX_URL`: URL del servidor Plex
- `PLEX_TOKEN`: Token de autenticación de Plex
- `PLEX_LIBRARY_NAME`: Nombre de la biblioteca (por defecto: "Pelis")

**OpenAI:**
- `OPENAI_API_KEY`: Clave API de OpenAI
- `OPENAI_MODEL`: Modelo a usar (por defecto: `gpt-4o`)
- `OPENAI_ASSISTANT_NAME`: Nombre del asistente (por defecto: "Plex AI Curator")

**Características:**
- `ENABLE_TELEGRAM`: Habilitar notificaciones Telegram (por defecto: `false`)
- `ENABLE_PLEX_PLAYLIST`: Habilitar creación de playlist (por defecto: `true`)

**Configuración de Notificación:**
- `TELEGRAM_BOT_TOKEN`: Token del bot de Telegram (opcional)
- `TELEGRAM_CHAT_ID`: ID del chat de Telegram (opcional)

**Configuración de Aplicación:**
- `RECOMMENDATION_COUNT`: Número de películas a recomendar (por defecto: 10)
- `HISTORY_LOOKBACK`: Número de películas recientes a analizar (por defecto: 5)
- `PLAYLIST_NAME`: Nombre de la playlist (por defecto: "Recomendado por IA")
- `LOG_LEVEL`: Nivel de logging (por defecto: "INFO")

## Instalación y Despliegue

### Requisitos Previos
- Docker y Docker Compose
- Servidor Plex con acceso a API
- Cuenta de OpenAI con créditos API
- (Opcional) Bot de Telegram configurado

### Opción 1: Despliegue con Docker Compose (Recomendado)

1. **Clonar el repositorio:**
```bash
git clone <repository-url>
cd quup
```

2. **Crear archivo de configuración:**
```bash
cp .env.example .env
```

3. **Editar `.env` con tus credenciales:**
```bash
nano .env  # o tu editor preferido
```

Configuración mínima requerida:
```env
API_AUTH_TOKEN=tu-token-secreto-aquí
PLEX_URL=http://tu-servidor-plex:32400
PLEX_TOKEN=tu-token-plex-aquí
OPENAI_API_KEY=sk-tu-clave-api-openai-aquí
```

4. **Iniciar el servicio:**
```bash
docker-compose up -d
```

5. **Verificar el estado:**
```bash
docker-compose logs -f
```

### Opción 2: Instalación Local (Para Desarrollo)

1. **Crear entorno virtual:**
```bash
python3.13 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

4. **Ejecutar la aplicación:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Uso de la API

### Health Check
```bash
curl http://localhost:8000/health
```

### Sincronizar Biblioteca
```bash
curl -X POST http://localhost:8000/sync \
  -H "x-api-token: tu-token-aquí"
```

Respuesta:
```json
{
  "success": true,
  "message": "Sincronización iniciada en segundo plano",
  "movies_count": 0,
  "file_id": "",
  "vector_store_id": "",
  "assistant_id": ""
}
```

### Generar Recomendaciones
```bash
curl -X POST http://localhost:8000/recommend \
  -H "x-api-token: tu-token-aquí"
```

Respuesta:
```json
{
  "success": true,
  "message": "Se generaron 10 recomendaciones",
  "recommendations": [
    "The Shawshank Redemption",
    "The Godfather",
    "Pulp Fiction",
    ...
  ],
  "playlist_created": true,
  "telegram_sent": false
}
```

### Modo Asíncrono (Recomendado para producción)
```bash
curl -X POST "http://localhost:8000/recommend?sync_mode=true" \
  -H "x-api-token: tu-token-aquí"
```

## Testing

### Ejecutar Tests
```bash
# Instalar dependencias de testing
pip install -r requirements.txt

# Ejecutar todos los tests
pytest

# Ejecutar con cobertura
pytest --cov=app tests/

# Ejecutar con verbose
pytest -v
```

### Tests Incluidos
1. Health endpoint
2. Root endpoint  
3. Sync endpoint sin autenticación
4. Sync endpoint con autenticación válida
5. Recommend endpoint con autenticación válida
6. PlexAICurator library sync
7. PlexAICurator get recommendations
8. PlexAICurator create playlist
9. Notificación Telegram (mockeada)
10. Flujo completo end-to-end

## Estructura del Proyecto

```
quup/
├── app/
│   ├── __init__.py          # Inicialización del paquete
│   ├── config.py            # Gestión de configuración con Pydantic
│   ├── core.py              # Lógica de negocio principal
│   ├── main.py              # Endpoints FastAPI
│   └── notifiers.py         # Servicios de notificación
├── tests/
│   ├── __init__.py          # Inicialización de tests
│   └── test_integration.py # Tests de integración
├── samples/
│   └── movies_library.json  # Datos de muestra para testing
├── Dockerfile               # Imagen Docker de producción
├── docker-compose.yml       # Orquestación de servicios
├── requirements.txt         # Dependencias Python
├── .env.example            # Plantilla de configuración
├── README.md               # Esta documentación
└── PROMPT.md               # Especificaciones originales
```

## Solución de Problemas

### Error: "Cannot connect to Plex server"
- Verifica que `PLEX_URL` sea correcto y accesible
- Verifica que `PLEX_TOKEN` sea válido
- Asegúrate de que el servidor Plex esté en ejecución

### Error: "OpenAI API error"
- Verifica que `OPENAI_API_KEY` sea válida
- Verifica que tengas créditos suficientes en tu cuenta de OpenAI
- Verifica la conectividad a internet

### Error: "No movies found in history"
- Reproduce algunas películas en Plex para generar historial
- Verifica que `PLEX_LIBRARY_NAME` coincida con el nombre de tu biblioteca

### Los tests fallan
- Verifica que todas las dependencias estén instaladas: `pip install -r requirements.txt`
- Asegúrate de tener Python 3.13 instalado
- Verifica que el archivo `samples/movies_library.json` exista

## Configuración de Telegram (Opcional)

1. **Crear un bot:**
   - Habla con @BotFather en Telegram
   - Usa el comando `/newbot` y sigue las instrucciones
   - Guarda el token proporcionado

2. **Obtener tu Chat ID:**
   - Envía un mensaje a tu bot
   - Visita: `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`
   - Busca el valor `chat.id`

3. **Configurar en `.env`:**
```env
ENABLE_TELEGRAM=true
TELEGRAM_BOT_TOKEN=tu-token-aquí
TELEGRAM_CHAT_ID=tu-chat-id-aquí
```

## Calidad del Código

- **Type Hinting:** Todo el código Python usa anotaciones de tipo
- **Logging:** Usa el módulo `logging` en lugar de `print`
- **Manejo de Errores:** Manejo robusto de excepciones con mensajes de error limpios
- **Documentación:** Docstrings completos en todas las funciones y clases

## Seguridad

- Autenticación por token de API requerida para todos los endpoints
- Las credenciales se gestionan mediante variables de entorno
- Usuario no-root en el contenedor Docker
- Health checks configurados

## Licencia

[Especificar licencia]

## Contribución

[Instrucciones de contribución si aplica]

## Soporte

Para problemas y preguntas, por favor abre un issue en el repositorio.
