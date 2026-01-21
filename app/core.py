"""Core business logic for syncing and recommendations."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from .config import Settings

logger = logging.getLogger(__name__)


# In-memory cache that behaves like a lightweight vector store.
class LocalVectorStore:
	def __init__(self) -> None:
		self.movies: list[Movie] = []

	def load_movies(self, movies: list[Movie]) -> None:
		self.movies = movies
		logger.info("Vector store recargado con %s películas", len(movies))

	def has_data(self) -> bool:
		return len(self.movies) > 0

	def recommend(self, history: list[Movie], limit: int = 15) -> list[Movie]:
		if not self.movies:
			return []

		unwatched = [m for m in self.movies if m.status == "Unwatched"]
		if not history:
			return unwatched[:limit]

		history_genres = _flatten([m.genres for m in history])
		history_directors = {m.director for m in history if m.director}
		history_actors = _flatten([m.actors for m in history])
		avg_year = _average([m.year for m in history if m.year])
		avg_rating = _average([m.rating for m in history if m.rating is not None])

		scored: list[tuple[Movie, float]] = []
		for movie in unwatched:
			score = 0.0
			genre_overlap = len(set(movie.genres) & set(history_genres))
			score += genre_overlap * 2.5

			if movie.director and movie.director in history_directors:
				score += 3.5

			actor_overlap = len(set(movie.actors) & set(history_actors))
			score += actor_overlap * 0.6

			if movie.rating is not None and avg_rating is not None:
				score += 1.2 * (movie.rating - avg_rating)

			if movie.year and avg_year:
				score -= abs(movie.year - avg_year) * 0.02

			score += (movie.rating or 0) * 0.4

			scored.append((movie, score))

		scored.sort(key=lambda item: item[1], reverse=True)
		return [item[0] for item in scored[:limit]]


local_store = LocalVectorStore()


@dataclass
class Movie:
	title: str
	year: Optional[int]
	director: Optional[str]
	genres: list[str]
	plot: str
	actors: list[str]
	rating: Optional[float]
	status: str
	rating_key: Optional[str] = None

	@staticmethod
	def from_dict(data: dict) -> "Movie":
		return Movie(
			title=clean_title(data.get("title") or data.get("Title") or ""),
			year=_coerce_int(data.get("year") or data.get("Year")),
			director=(data.get("director") or data.get("Director") or None),
			genres=_ensure_list(data.get("genre") or data.get("Genre") or []),
			plot=data.get("plot") or data.get("Plot Summary") or data.get("summary") or "",
			actors=_ensure_list(data.get("actors") or data.get("Main Actors") or []),
			rating=_coerce_float(data.get("rating") or data.get("Rating")),
			status=data.get("status") or _status_from_view_count(data.get("viewCount")),
			rating_key=data.get("ratingKey"),
		)


class PlexClient:
	async def fetch_library(self) -> list[Movie]:
		raise NotImplementedError

	async def fetch_history(self, limit: int = 8) -> list[Movie]:
		raise NotImplementedError


class SamplePlexClient(PlexClient):
	def __init__(self, sample_path: Path) -> None:
		self.sample_path = sample_path

	async def fetch_library(self) -> list[Movie]:
		raw = self._load_json()
		library = raw.get("library") if isinstance(raw, dict) else raw
		if not isinstance(library, list):
			logger.warning("Estructura inesperada en sample; usando lista vacía")
			return []
		return [Movie.from_dict(item) for item in library]

	async def fetch_history(self, limit: int = 8) -> list[Movie]:
		raw = self._load_json()
		history_items: list[dict] = []
		if isinstance(raw, dict) and isinstance(raw.get("history"), list):
			history_items = raw["history"][:limit]
		elif isinstance(raw, list):
			history_items = [item for item in raw if (item.get("viewCount") or 0) > 0][:limit]

		return [Movie.from_dict(item) for item in history_items]

	def _load_json(self) -> dict:
		if not self.sample_path.exists():
			logger.error("Archivo de muestra no encontrado: %s", self.sample_path)
			return {}
		with self.sample_path.open("r", encoding="utf-8") as fh:
			try:
				return json.load(fh)
			except json.JSONDecodeError:
				logger.error("No se pudo parsear el archivo de muestra")
				return {}


class PlexApiClient(PlexClient):
	def __init__(self, settings: Settings) -> None:
		self.settings = settings
		self._server = None

	def _connect(self):
		if self._server:
			return self._server
		try:
			from plexapi.server import PlexServer
		except ImportError:  # pragma: no cover - solo aplica si falta dependencia
			raise RuntimeError("plexapi no está instalado")

		self._server = PlexServer(str(self.settings.plex_url), str(self.settings.plex_token))
		return self._server

	async def fetch_library(self) -> list[Movie]:
		server = self._connect()
		section = server.library.section(self.settings.plex_library_name)
		movies = section.all()
		parsed: list[Movie] = []
		for item in movies:
			parsed.append(
				Movie(
					title=clean_title(item.title),
					year=item.year,
					director=getattr(item, "director", None) or None,
					genres=[g.tag for g in getattr(item, "genres", [])],
					plot=item.summary or "",
					actors=[a.tag for a in getattr(item, "actors", [])],
					rating=item.audienceRating or item.rating,
					status="Watched" if (getattr(item, "viewCount", 0) or 0) > 0 else "Unwatched",
					rating_key=str(getattr(item, "ratingKey", "")) or None,
				)
			)
		return parsed

	async def fetch_history(self, limit: int = 8) -> list[Movie]:
		server = self._connect()
		section = server.library.section(self.settings.plex_library_name)
		history_items = section.history(maxresults=limit)
		parsed: list[Movie] = []
		for item in history_items:
			movie = item.ratingKey if hasattr(item, "ratingKey") else item
			parsed.append(
				Movie(
					title=clean_title(getattr(movie, "title", "")),
					year=getattr(movie, "year", None),
					director=getattr(movie, "director", None),
					genres=[g.tag for g in getattr(movie, "genres", [])],
					plot=getattr(movie, "summary", ""),
					actors=[a.tag for a in getattr(movie, "actors", [])],
					rating=getattr(movie, "audienceRating", None) or getattr(movie, "rating", None),
					status="Watched",
					rating_key=str(getattr(movie, "ratingKey", "")) or None,
				)
			)
		return parsed


def build_plex_client(settings: Settings) -> PlexClient:
	if settings.should_use_sample:
		return SamplePlexClient(settings.sample_data_path)
	return PlexApiClient(settings)


async def sync_library(settings: Settings) -> dict:
	"""Load movies from Plex or sample data and refresh the local vector store."""

	plex_client = build_plex_client(settings)
	movies = await plex_client.fetch_library()
	local_store.load_movies(movies)

	upload_result = await _upload_vector_store_if_possible(movies, settings)

	return {
		"peliculas": len(movies),
		"fuente": "sample" if settings.should_use_sample else "plex",
		"openai_sync": upload_result,
	}


async def get_recommendations(settings: Settings, limit: int = 12) -> list[str]:
	"""Generate a list of recommended movie titles."""

	if not local_store.has_data():
		await sync_library(settings)

	plex_client = build_plex_client(settings)
	history = await plex_client.fetch_history()
	recommendations = local_store.recommend(history, limit=limit)

	titles = [clean_title(movie.title) for movie in recommendations]
	return _unique_preserve_order(titles)


async def _upload_vector_store_if_possible(movies: list[Movie], settings: Settings) -> str:
	if not settings.has_openai:
		return "omitido (sin OPENAI_API_KEY)"

	try:
		from openai import OpenAI  # type: ignore
	except Exception as exc:  # pragma: no cover - solo aplica si falta dependencia
		logger.warning("OpenAI SDK no disponible: %s", exc)
		return "omitido (sdk no disponible)"

	client = OpenAI(api_key=settings.openai_api_key)

	payload = [movie.__dict__ for movie in movies]
	file_content = json.dumps(payload, ensure_ascii=False).encode("utf-8")

	try:
		vector_store = client.beta.vector_stores.create(name=settings.openai_assistant_name)
		with open("/tmp/plex_movies.json", "wb") as temp:
			temp.write(file_content)
		with open("/tmp/plex_movies.json", "rb") as temp:
			batch = client.beta.vector_stores.file_batches.upload_and_poll(
				vector_store_id=vector_store.id,
				files=[temp],
			)
		logger.info("Vector store sincronizado: %s (archivos subidos: %s)", vector_store.id, batch.file_counts)
		return f"ok ({batch.file_counts})"
	except Exception as exc:  # pragma: no cover - accesos remotos se omiten en tests
		logger.error("Fallo al sincronizar OpenAI: %s", exc)
		return "error"


def clean_title(raw_title: str) -> str:
	if not raw_title:
		return ""
	cleaned = re.sub(r"\s*\(\d{4}\)$", "", raw_title).strip()
	cleaned = re.sub(r"\s+", " ", cleaned)
	return cleaned


def _ensure_list(value: Optional[Iterable[str]]) -> list[str]:
	if value is None:
		return []
	if isinstance(value, str):
		return [v.strip() for v in value.split(",") if v.strip()]
	return [str(v).strip() for v in value]


def _status_from_view_count(view_count) -> str:
	try:
		return "Watched" if int(view_count or 0) > 0 else "Unwatched"
	except Exception:
		return "Unwatched"


def _coerce_int(value) -> Optional[int]:
	try:
		return int(value)
	except Exception:
		return None


def _coerce_float(value) -> Optional[float]:
	try:
		if value is None:
			return None
		return float(value)
	except Exception:
		return None


def _average(values: Iterable[Optional[float]]) -> Optional[float]:
	nums = [v for v in values if v is not None]
	if not nums:
		return None
	return sum(nums) / len(nums)


def _flatten(items: Iterable[Iterable[str]]) -> list[str]:
	flat: list[str] = []
	for sub in items:
		flat.extend(sub)
	return flat


def _unique_preserve_order(items: List[str]) -> List[str]:
	seen = set()
	unique: list[str] = []
	for item in items:
		if item not in seen:
			seen.add(item)
			unique.append(item)
	return unique
