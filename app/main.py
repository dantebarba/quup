"""FastAPI application for Plex AI Curator."""

import logging
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.core import PlexAICurator
from app.notifiers import TelegramNotifier

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting Plex AI Curator API")
    logger.info(f"Plex Library: {settings.plex_library_name}")
    logger.info(f"OpenAI Model: {settings.openai_model}")
    logger.info(f"Telegram enabled: {settings.enable_telegram}")
    logger.info(f"Plex playlist enabled: {settings.enable_plex_playlist}")
    yield
    logger.info("Shutting down Plex AI Curator API")


# Create FastAPI app
app = FastAPI(
    title="Plex AI Curator",
    description="Personalized Movie Recommendation Engine for Plex",
    version="1.0.0",
    lifespan=lifespan
)


# Response models
class SyncResponse(BaseModel):
    """Response model for sync endpoint."""
    success: bool
    message: str
    movies_count: int
    file_id: str
    vector_store_id: str
    assistant_id: str


class RecommendationResponse(BaseModel):
    """Response model for recommend endpoint."""
    success: bool
    message: str
    recommendations: list[str]
    playlist_created: bool
    telegram_sent: bool


class ErrorResponse(BaseModel):
    """Response model for errors."""
    success: bool
    error: str


# Security dependency
async def verify_api_token(x_api_token: str = Header(...)):
    """Verify API token from request header."""
    if x_api_token != settings.api_auth_token:
        logger.warning("Invalid API token provided")
        raise HTTPException(status_code=403, detail="Invalid API token")
    return x_api_token


# Background task for sync
async def sync_library_task():
    """Background task to sync Plex library."""
    try:
        curator = PlexAICurator()
        result = curator.sync_library()
        
        # Send Telegram notification if enabled
        if settings.enable_telegram:
            notifier = TelegramNotifier()
            await notifier.send_sync_notification(result['movies_count'])
        
        logger.info("Background sync completed successfully")
    except Exception as e:
        logger.error(f"Background sync failed: {e}", exc_info=True)


# Background task for recommendations
async def generate_recommendations_task():
    """Background task to generate recommendations."""
    try:
        curator = PlexAICurator()
        recommendations = curator.get_recommendations()
        
        # Create playlist
        playlist_result = None
        if settings.enable_plex_playlist and recommendations:
            playlist_result = curator.create_playlist(recommendations)
        
        # Send Telegram notification
        if settings.enable_telegram and recommendations:
            notifier = TelegramNotifier()
            playlist_created = playlist_result and playlist_result.get('success', False)
            await notifier.send_recommendations(recommendations, playlist_created)
        
        logger.info("Background recommendation task completed successfully")
    except Exception as e:
        logger.error(f"Background recommendation task failed: {e}", exc_info=True)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": "Plex AI Curator",
        "version": "1.0.0",
        "endpoints": {
            "sync": "POST /sync - Sync Plex library to OpenAI",
            "recommend": "POST /recommend - Generate movie recommendations"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Plex AI Curator"}


@app.post("/sync", response_model=SyncResponse, dependencies=[Depends(verify_api_token)])
async def sync_endpoint(background_tasks: BackgroundTasks):
    """
    Sync Plex library to OpenAI Vector Store.
    
    This endpoint triggers a background sync of the Plex library to OpenAI.
    The sync process includes:
    - Fetching all movies from Plex
    - Converting to JSON with rich metadata
    - Uploading to OpenAI Vector Store
    - Cleaning up old files
    
    Requires: x-api-token header
    """
    try:
        # Start sync in background
        background_tasks.add_task(sync_library_task)
        
        logger.info("Sync request received, starting background task")
        
        return JSONResponse(
            status_code=202,
            content={
                "success": True,
                "message": "Sincronización iniciada en segundo plano",
                "movies_count": 0,
                "file_id": "",
                "vector_store_id": "",
                "assistant_id": ""
            }
        )
    except Exception as e:
        logger.error(f"Error in sync endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al iniciar sincronización: {str(e)}"
        )


@app.post("/recommend", response_model=RecommendationResponse, dependencies=[Depends(verify_api_token)])
async def recommend_endpoint(background_tasks: BackgroundTasks, async_mode: bool = False):
    """
    Generate movie recommendations based on watch history.
    
    This endpoint analyzes recent watch history and generates personalized
    movie recommendations. The process includes:
    - Fetching recent watch history
    - Analyzing patterns with OpenAI
    - Recommending unwatched movies
    - Creating Plex playlist (if enabled)
    - Sending Telegram notification (if enabled)
    
    Args:
        async_mode: If True, returns immediately and processes in background
        
    Requires: x-api-token header
    """
    try:
        if async_mode:
            # Process in background
            background_tasks.add_task(generate_recommendations_task)
            
            logger.info("Recommendation request received, starting background task")
            
            return JSONResponse(
                status_code=202,
                content={
                    "success": True,
                    "message": "Generación de recomendaciones iniciada en segundo plano",
                    "recommendations": [],
                    "playlist_created": False,
                    "telegram_sent": False
                }
            )
        else:
            # Process synchronously
            curator = PlexAICurator()
            recommendations = curator.get_recommendations()
            
            if not recommendations:
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": "No se generaron recomendaciones",
                        "recommendations": [],
                        "playlist_created": False,
                        "telegram_sent": False
                    }
                )
            
            # Create playlist
            playlist_created = False
            if settings.enable_plex_playlist:
                playlist_result = curator.create_playlist(recommendations)
                playlist_created = playlist_result.get('success', False)
            
            # Send Telegram notification
            telegram_sent = False
            if settings.enable_telegram:
                notifier = TelegramNotifier()
                telegram_sent = await notifier.send_recommendations(
                    recommendations, 
                    playlist_created
                )
            
            logger.info(f"Generated {len(recommendations)} recommendations")
            
            return {
                "success": True,
                "message": f"Se generaron {len(recommendations)} recomendaciones",
                "recommendations": recommendations,
                "playlist_created": playlist_created,
                "telegram_sent": telegram_sent
            }
            
    except Exception as e:
        logger.error(f"Error in recommend endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar recomendaciones: {str(e)}"
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
