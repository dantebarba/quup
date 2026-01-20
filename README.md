# Plex AI Curator (modelo: gpt-4.1-mini)

## Clarificaciones (sí/no)
1) ¿Mock de Plex en tests con sample? **Sí**  
2) ¿Mock de OpenAI en tests? **No** (se usa modo local sin llamadas externas)  
3) ¿Persistir vector store solo en memoria? **Sí**  
4) ¿Mock de Telegram en tests? **Sí**  
5) ¿Solo happy-path tests? **No** (pero se entregan happy-path mínimos solicitados)

## Requisitos
- Python 3.13
- Variables de entorno mínimas: `API_AUTH_TOKEN`
- Opcional para producción: `PLEX_URL`, `PLEX_TOKEN`, `PLEX_LIBRARY_NAME`, `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- Para correr con datos de ejemplo: `USE_SAMPLE_DATA=true` (usa `samples/movies_library.json`)

## Instalación
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecución local
```bash
export API_AUTH_TOKEN=secret
export USE_SAMPLE_DATA=true
uvicorn app.main:app --reload --port 8000
```

Con credenciales reales de Plex, exporta además `PLEX_URL`, `PLEX_TOKEN` y `PLEX_LIBRARY_NAME`; para OpenAI, exporta `OPENAI_API_KEY`.

## Endpoints
- `POST /sync` — inicia sincronización en background. Header: `x-api-token`.
- `POST /recommend` — retorna recomendaciones y dispara notificaciones. Header: `x-api-token`.

Las respuestas están localizadas en español y se manejan errores con JSON limpio.

## Notificaciones
- Telegram: activar con `ENABLE_TELEGRAM=true` + `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`.
- Playlist Plex: activar con `ENABLE_PLEX_PLAYLIST=true` (stub informativo; se deja listo para mapear `ratingKey`).

## Tests
```bash
export API_AUTH_TOKEN=secret
export USE_SAMPLE_DATA=true
pytest -q
```
Happy-path cubre `/sync` y `/recommend` y la heurística local.

El sample de películas está en `samples/movies_library.json` y se usa para simular Plex en los tests.

## Docker
```bash
docker build -t plex-ai-curator .
docker run -e API_AUTH_TOKEN=secret -e USE_SAMPLE_DATA=true -p 8000:8000 plex-ai-curator
```

## docker-compose
```bash
API_AUTH_TOKEN=secret USE_SAMPLE_DATA=true docker-compose up --build
```

## Notas de diseño
- Modo local (sin OPENAI_API_KEY) usa heurística `LocalRecommender` con vector store en memoria.
- Sincronización limpia y recrea vector store (o cache local).
- Logs y textos de usuario en español.
- Manejo de errores: fallos externos no derriban la app; se registran y se responde JSON limpio.
