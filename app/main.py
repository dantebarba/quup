from fastapi import FastAPI, Header, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
import logging
from typing import Annotated

from app.config import settings
from app.core import PlexCurator

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PlexCurator")

app = FastAPI(title="Plex AI Curator")

async def verify_token(x_api_token: Annotated[str, Header()]):
    if x_api_token != settings.api_auth_token:
        raise HTTPException(status_code=403, detail="Invalid API Token")

def get_curator():
    # Helper to instantiate curator. Could be a singleton if needed.
    # Check if necessary configs are present is handled by pydantic on startup
    return PlexCurator()

@app.post("/sync", dependencies=[Depends(verify_token)])
async def sync_library_endpoint(background_tasks: BackgroundTasks):
    """
    Triggers an async background task to sync Plex library to OpenAI.
    """
    try:
        curator = get_curator()
        background_tasks.add_task(curator.sync_library)
        return {"status": "accepted", "message": "Library sync started in background."}
    except Exception as e:
        logger.error(f"Failed to initiate sync: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.post("/recommend", dependencies=[Depends(verify_token)])
async def recommend_endpoint():
    """
    Generates recommendations based on recent history.
    """
    try:
        curator = get_curator()
        recommendations = await curator.get_recommendations()
        return {"status": "success", "recommendations": recommendations}
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.get("/health")
def health_check():
    return {"status": "healthy"}
