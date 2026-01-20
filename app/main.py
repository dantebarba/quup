import logging
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, status

from .config import Settings, get_settings
from .core import get_recommendations, sync_library
from .notifiers import notify_telegram, update_plex_playlist


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


app = FastAPI(title="Plex AI Curator", version="0.1.0")


def _validate_token(x_api_token: Annotated[str | None, Header(alias="x-api-token")] , settings: Settings) -> None:  # type: ignore[valid-type]
    if not x_api_token or x_api_token != settings.API_AUTH_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "Token inválido"})


def get_secured_settings(
    x_api_token: Annotated[str | None, Header(alias="x-api-token")],
    settings: Settings = Depends(get_settings),
) -> Settings:
    _validate_token(x_api_token, settings)
    return settings


@app.post("/sync")
async def sync_endpoint(background: BackgroundTasks, settings: Settings = Depends(get_secured_settings)):
    # Launch sync in the background to avoid blocking
    background.add_task(sync_library, settings)
    return {"mensaje": "Sincronización iniciada", "started": True}


@app.post("/recommend")
async def recommend_endpoint(settings: Settings = Depends(get_secured_settings)):
    titles = get_recommendations(settings)
    if not titles:
        raise HTTPException(status_code=500, detail={"error": "No se pudieron generar recomendaciones"})
    # Side-effects
    notify_telegram(settings, titles)
    update_plex_playlist(settings, titles)
    return {"mensaje": "Recomendaciones generadas", "peliculas": titles}

