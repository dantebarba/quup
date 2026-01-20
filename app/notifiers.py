import logging
from typing import Iterable

from .config import Settings


logger = logging.getLogger(__name__)


def notify_telegram(settings: Settings, titles: Iterable[str]) -> None:
    if not settings.ENABLE_TELEGRAM:
        logger.info("Telegram deshabilitado; no se envía notificación.")
        return
    # In a real implementation, send via Telegram Bot API.
    lista = "\n".join(f"• {t}" for t in titles)
    logger.info("🎬 Aquí tienes tus recomendaciones:\n%s", lista)


def update_plex_playlist(settings: Settings, titles: Iterable[str]) -> None:
    if not settings.ENABLE_PLEX_PLAYLIST:
        logger.info("Playlist de Plex deshabilitada; no se actualiza.")
        return
    # In a real implementation, connect to Plex and create/overwrite the playlist.
    logger.info("Actualizando playlist 'Recomendado por IA' con %d títulos.", len(list(titles)))

