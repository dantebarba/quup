"""Notification helpers for Telegram and Plex playlist stubs."""

from __future__ import annotations

import logging
from typing import Iterable, List

import httpx

from .config import Settings

logger = logging.getLogger(__name__)

PLAYLIST_NAME = "Recomendado por IA"


async def send_telegram_message(settings: Settings, titles: Iterable[str]) -> bool:
    """Send a Spanish message with the recommended titles using Telegram API.

    Returns True when the call was attempted and succeeded; False when skipped or failed.
    """

    if not settings.has_telegram:
        logger.info("Telegram desactivado; se omite notificación")
        return False

    titles_list = list(titles)
    if not titles_list:
        return False

    message = "\ud83c\udfa5 Aqu\u00ed tienes tus recomendaciones de la IA:\n" + "\n".join(
        f"{idx+1}. {title}" for idx, title in enumerate(titles_list)
    )

    url = (
        f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    )
    payload = {"chat_id": settings.telegram_chat_id, "text": message}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info("Mensaje de Telegram enviado")
                return True
            logger.error("Error al enviar Telegram: %s - %s", response.status_code, response.text)
            return False
    except Exception as exc:  # pragma: no cover - depende de la red
        logger.error("Fallo al enviar Telegram: %s", exc)
        return False


async def create_or_update_playlist(settings: Settings, movies: List[dict]) -> bool:
    """Stub for playlist creation on Plex.

    In sample/testing mode this only logs the intended playlist content.
    """

    if not settings.enable_plex_playlist:
        logger.info("Creaci\u00f3n de playlist desactivada")
        return False

    logger.info("Playlist '%s' preparada con %s elementos", PLAYLIST_NAME, len(movies))
    return True
