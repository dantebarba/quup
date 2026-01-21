import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

async def send_telegram_notification(message: str):
    if not settings.enable_telegram:
        return

    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.warning("Telegram enabled but credentials missing.")
        return

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            logger.info("Telegram notification sent successfully.")
        except httpx.HTTPError as e:
            logger.error(f"Failed to send Telegram notification: {e}")

async def notify_recommendations(movie_titles: list[str]):
    if not movie_titles:
        logger.info("No recommendations to notify.")
        return
    
    formatted_list = "\n".join([f"• {title}" for title in movie_titles])
    message = f"🎬 *Aquí tienes tus recomendaciones de hoy:*\n\n{formatted_list}\n\n🍿 ¡Que lo disfrutes!"
    
    await send_telegram_notification(message)
