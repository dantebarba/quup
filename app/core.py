import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from .config import Settings


logger = logging.getLogger(__name__)


DATA_DIR = Path(".data")
VECTOR_STORE_FILE = DATA_DIR / "vector_store.json"
SAMPLES_FILE = Path("samples/movies_library.json")


@dataclass
class Movie:
    title: str
    year: Optional[int]
    director: List[str]
    genre: List[str]
    plot_summary: str
    main_actors: List[str]
    rating: Optional[float]
    status: str  # "Watched" or "Unwatched"
    last_viewed_at: Optional[int] = None


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _parse_movies_from_plex_dump(raw: dict) -> List[Movie]:
    metadata = raw.get("MediaContainer", {}).get("Metadata", [])
    movies: List[Movie] = []
    for item in metadata:
        title = item.get("title", "")
        year = item.get("year")
        director = [d.get("tag", "") for d in item.get("Director", []) if d.get("tag")]
        genre = [g.get("tag", "") for g in item.get("Genre", []) if g.get("tag")]
        plot_summary = item.get("summary", "")
        main_actors = [r.get("tag", "") for r in item.get("Role", []) if r.get("tag")]
        rating = item.get("rating")
        view_count = item.get("viewCount", 0) or 0
        status = "Watched" if view_count > 0 else "Unwatched"
        last_viewed_at = item.get("lastViewedAt")
        movies.append(
            Movie(
                title=title,
                year=year,
                director=director,
                genre=genre,
                plot_summary=plot_summary,
                main_actors=main_actors,
                rating=rating,
                status=status,
                last_viewed_at=last_viewed_at,
            )
        )
    return movies


def _load_sample_library() -> List[Movie]:
    with SAMPLES_FILE.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return _parse_movies_from_plex_dump(raw)


def _load_vector_store() -> List[Movie]:
    if not VECTOR_STORE_FILE.exists():
        return []
    with VECTOR_STORE_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    movies: List[Movie] = []
    for m in data:
        movies.append(
            Movie(
                title=m.get("Title", ""),
                year=m.get("Year"),
                director=m.get("Director", []),
                genre=m.get("Genre", []),
                plot_summary=m.get("Plot Summary", ""),
                main_actors=m.get("Main Actors", []),
                rating=m.get("Rating"),
                status=m.get("status", "Unwatched"),
                last_viewed_at=m.get("lastViewedAt"),
            )
        )
    return movies


def _dump_vector_store(movies: Iterable[Movie]) -> None:
    _ensure_data_dir()
    # Clean previous store (single file approach)
    if VECTOR_STORE_FILE.exists():
        VECTOR_STORE_FILE.unlink()
    payload = [
        {
            "Title": m.title,
            "Year": m.year,
            "Director": m.director,
            "Genre": m.genre,
            "Plot Summary": m.plot_summary,
            "Main Actors": m.main_actors,
            "Rating": m.rating,
            "status": m.status,
            "lastViewedAt": m.last_viewed_at,
        }
        for m in movies
    ]
    with VECTOR_STORE_FILE.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)


def sync_library(settings: Settings) -> dict:
    """Build the Knowledge Base from Plex and store it locally.

    In production, this would fetch Plex -> build JSON -> upload to OpenAI Vector Store,
    cleaning any old files first. Here, we simulate by persisting a local vector store file.
    """
    try:
        movies = _load_sample_library()
        _dump_vector_store(movies)
        logger.info("Vector store actualizado con %d películas", len(movies))
        return {"ok": True, "count": len(movies)}
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error al sincronizar biblioteca: %s", exc)
        return {"ok": False, "error": "Error al sincronizar la biblioteca"}


def _top_recent(movies: List[Movie], n: int = 10) -> List[Movie]:
    viewed = [m for m in movies if m.last_viewed_at]
    return sorted(viewed, key=lambda m: m.last_viewed_at or 0, reverse=True)[:n]


def _score_candidate(recent_genres: set, recent_directors: set, candidate: Movie) -> int:
    score = 0
    score += 2 * len(recent_directors.intersection(set(candidate.director)))
    score += 1 * len(recent_genres.intersection(set(candidate.genre)))
    return score


def get_recommendations(settings: Settings, limit: int = 15) -> List[str]:
    """Heuristic recommender using recent views' vibe (genres/directors) over local store."""
    try:
        store = _load_vector_store()
        if not store:
            # Fallback to sample if vector store not initialized
            store = _load_sample_library()

        recent = _top_recent(store, n=10)
        recent_genres = {g for m in recent for g in m.genre}
        recent_directors = {d for m in recent for d in m.director}

        candidates = [m for m in store if m.status == "Unwatched"]
        ranked = sorted(
            candidates,
            key=lambda m: (_score_candidate(recent_genres, recent_directors, m), m.rating or 0.0),
            reverse=True,
        )
        titles = []
        for m in ranked:
            if len(titles) >= limit:
                break
            # Basic dedupe/cleaning
            clean_title = m.title.strip()
            if clean_title and clean_title not in titles:
                titles.append(clean_title)
        return titles
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error al obtener recomendaciones: %s", exc)
        return []

