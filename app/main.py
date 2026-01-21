"""FastAPI application wiring the Plex AI Curator endpoints."""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, status

from .config import Settings, get_settings
from .core import get_recommendations, sync_library
from . import notifiers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Plex AI Curator", version="1.0.0")


@lru_cache
def get_cached_settings() -> Settings:
    return get_settings()


def require_token(
    x_api_token: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(get_cached_settings),
) -> Settings:
    if not x_api_token or x_api_token != settings.api_auth_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    return settings


@app.post("/sync")
async def sync_endpoint(background_tasks: BackgroundTasks, settings: Settings = Depends(require_token)):
    async def do_sync():
        try:
            await sync_library(settings)
        except Exception as exc:  # pragma: no cover - defensivo
            logger.exception("Error en sincronización: %s", exc)

    # Ejecutamos en un loop separado para cumplir con la tarea en background.
    background_tasks.add_task(lambda: asyncio.run(do_sync()))
    return {"detalle": "Sincronización iniciada"}


@app.post("/recommend")
async def recommend_endpoint(settings: Settings = Depends(require_token)):
    try:
        titles = await get_recommendations(settings)
    except Exception as exc:  # pragma: no cover - defensivo
        logger.exception("Error generando recomendaciones: %s", exc)
        raise HTTPException(status_code=500, detail="No se pudieron generar recomendaciones")

    # Notificaciones opcionales; se ignora el resultado en la respuesta.
    await notifiers.send_telegram_message(settings, titles)
    await notifiers.create_or_update_playlist(settings, [{"title": t} for t in titles])

    return {"recomendaciones": titles}


@app.get("/")
async def root():
    return {"status": "ok"}
