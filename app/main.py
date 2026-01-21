# app/main.py
from __future__ import annotations
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status, Header
from pydantic import BaseModel

from .config import get_settings
from .core import sync_library, get_recommendations
from .notifiers import format_recommendations_message, notify_telegram

app = FastAPI(title="Plex AI Curator")


class RecRequest(BaseModel):
    history: List[str] = []


def _verify_token(x_api_token: str = Header(..., alias="x-api-token")) -> None:
    settings = get_settings()
    if not x_api_token or x_api_token != settings.api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API token"
        )


@app.post("/sync")
def sync_endpoint(_token: None = Depends(_verify_token)):
    data = sync_library()
    return {"status": "ok", "synced": len(data)}


@app.post("/recommend")
def recommend_endpoint(req: RecRequest, _token: None = Depends(_verify_token)):
    recs = get_recommendations(req.history or [])
    message = format_recommendations_message(recs)
    settings = get_settings()
    notify_telegram(
        message,
        enable=settings.enable_telegram,
        token=settings.telegram_bot_token,
        chat_id=settings.telegram_chat_id,
    )
    return {"titles": recs, "count": len(recs)}
