# app/core.py
import json
import os
from typing import Any, Dict, List

from .config import get_settings

# In-memory vector store (simulated OpenAI Vector Store)
_VECTOR_STORE: List[Dict[str, Any]] = []


def _library_json_path() -> str:
    repo_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), "samples")
    return os.path.join(repo_root, "movies_library.json")


def load_plex_library() -> List[Dict[str, Any]]:
    path = _library_json_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    # Fallback minimal dataset if file missing or invalid
    return [
        {
            "title": "Inception",
            "Year": 2010,
            "Director": "Christopher Nolan",
            "Genre": "Sci-Fi, Thriller",
            "Plot": "A thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.",
            "Actors": ["Leonardo DiCaprio", "Joseph Gordon-Levitt"],
            "rating": 8.8,
            "viewCount": 5,
        },
        {
            "title": "Interstellar",
            "Year": 2014,
            "Director": "Christopher Nolan",
            "Genre": "Adventure, Drama, Sci-Fi",
            "Plot": "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.",
            "Actors": ["Matthew McConaughey", "Anne Hathaway"],
            "rating": 8.6,
            "viewCount": 0,
        },
        {
            "title": "The Godfather",
            "Year": 1972,
            "Director": "Francis Ford Coppola",
            "Genre": "Crime, Drama",
            "Plot": "The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.",
            "Actors": ["Marlon Brando", "Al Pacino"],
            "rating": 9.2,
            "viewCount": 2,
        },
    ]


def _transform(raw: Dict[str, Any]) -> Dict[str, Any]:
    title = raw.get("title") or raw.get("Title")
    year = raw.get("Year") or raw.get("year")
    director = raw.get("Director")
    genre = raw.get("Genre") or raw.get("genre")
    plot = raw.get("Plot") or raw.get("Plot Summary") or raw.get("Plot Summary")
    actors = raw.get("Actors") or raw.get("Main Actors") or []
    rating = raw.get("rating") or raw.get("Rating")
    view_count = raw.get("viewCount") or raw.get("ViewCount") or 0
    status = "Watched" if int(view_count) > 0 else "Unwatched"
    return {
        "Title": title,
        "Year": year,
        "Director": director,
        "Genre": genre,
        "Plot Summary": plot,
        "Main Actors": actors,
        "Rating": rating,
        "status": status,
    }


def sync_library() -> List[Dict[str, Any]]:
    global _VECTOR_STORE
    library = load_plex_library()
    transformed = [_transform(item) for item in library]
    # Clean existing vector store and upload new data
    _VECTOR_STORE = transformed
    return transformed


def get_recommendations(history: List[str], limit: int = 15) -> List[str]:
    global _VECTOR_STORE
    if not _VECTOR_STORE:
        return []

    # Build user preferences from history by looking up their metadata
    prefs = {"Genres": {}, "Directors": {}}
    for h in history:
        for item in _VECTOR_STORE:
            if item.get("Title") == h:
                genres = item.get("Genre") or ""
                g_list = []
                if isinstance(genres, str):
                    g_list = [g.strip() for g in genres.split(",") if g.strip()]
                elif isinstance(genres, list):
                    g_list = genres
                for g in g_list:
                    prefs["Genres"][g] = prefs["Genres"].get(g, 0) + 1
                director = item.get("Director")
                if director:
                    prefs["Directors"][director] = (
                        prefs["Directors"].get(director, 0) + 1
                    )
                break

    scored: List[tuple] = []  # (item, score)
    for item in _VECTOR_STORE:
        if item.get("status") != "Unwatched":
            continue
        score = 0
        genres = item.get("Genre") or ""
        g_list = []
        if isinstance(genres, str):
            g_list = [g.strip() for g in genres.split(",") if g.strip()]
        elif isinstance(genres, list):
            g_list = genres
        for g in g_list:
            score += prefs["Genres"].get(g, 0)
        director = item.get("Director")
        if director in prefs["Directors"]:
            score += prefs["Directors"][director]
        scored.append((item, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    recs = [it["Title"] for it, _ in scored[:limit]]
    if not recs:
        recs = [it["Title"] for it in _VECTOR_STORE if it.get("status") == "Unwatched"][
            :limit
        ]
    return recs
