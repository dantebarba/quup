"""Notification services for Plex AI Curator."""

import logging
from typing import List, Optional
import asyncio

from telegram import Bot
from telegram.error import TelegramError

from app.config import settings

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Telegram notification service."""
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """Initialize Telegram notifier."""
        self.bot_token = bot_token or settings.telegram_bot_token
        self.chat_id = chat_id or settings.telegram_chat_id
        self.bot: Optional[Bot] = None
        
        if settings.enable_telegram and self.bot_token:
            self.bot = Bot(token=self.bot_token)
    
    async def send_recommendations(self, movie_titles: List[str], playlist_created: bool = False) -> bool:
        """
        Send movie recommendations via Telegram.
        
        Args:
            movie_titles: List of recommended movie titles
            playlist_created: Whether a Plex playlist was created
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        if not settings.enable_telegram:
            logger.info("Telegram notifications are disabled")
            return False
        
        if not self.bot or not self.chat_id:
            logger.warning("Telegram bot or chat_id not configured")
            return False
        
        try:
            # Build message
            message = self._build_recommendations_message(movie_titles, playlist_created)
            
            # Send message
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            
            logger.info(f"Sent Telegram notification with {len(movie_titles)} recommendations")
            return True
            
        except TelegramError as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram notification: {e}", exc_info=True)
            return False
    
    def _build_recommendations_message(self, movie_titles: List[str], playlist_created: bool) -> str:
        """Build formatted message for Telegram."""
        lines = ["🎬 <b>Aquí tienes tus recomendaciones de hoy:</b>\n"]
        
        for i, title in enumerate(movie_titles, 1):
            lines.append(f"{i}. {title}")
        
        if playlist_created:
            lines.append(f"\n✨ <i>Las películas han sido añadidas a tu playlist '{settings.playlist_name}' en Plex</i>")
        
        return "\n".join(lines)
    
    async def send_sync_notification(self, movies_count: int) -> bool:
        """
        Send notification about library sync completion.
        
        Args:
            movies_count: Number of movies synchronized
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        if not settings.enable_telegram or not self.bot or not self.chat_id:
            return False
        
        try:
            message = (
                f"📚 <b>Biblioteca sincronizada exitosamente</b>\n\n"
                f"Se sincronizaron <b>{movies_count}</b> películas con la IA"
            )
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            
            logger.info("Sent sync completion notification")
            return True
            
        except TelegramError as e:
            logger.error(f"Error sending Telegram sync notification: {e}")
            return False


# Synchronous wrapper for backward compatibility
def send_telegram_notification(movie_titles: List[str], playlist_created: bool = False) -> bool:
    """
    Synchronous wrapper for sending Telegram notifications.
    
    Args:
        movie_titles: List of recommended movie titles
        playlist_created: Whether a Plex playlist was created
        
    Returns:
        True if message was sent successfully, False otherwise
    """
    notifier = TelegramNotifier()
    return asyncio.run(notifier.send_recommendations(movie_titles, playlist_created))
