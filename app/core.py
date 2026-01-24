"""Core business logic for Plex AI Curator."""

import json
import logging
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from openai import OpenAI
from plexapi.server import PlexServer
from plexapi.video import Movie

from app.config import settings

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PlexAICurator:
    """Main class for Plex AI Curator operations."""
    
    def __init__(self, plex_server: Optional[PlexServer] = None, openai_client: Optional[OpenAI] = None):
        """Initialize the curator with Plex and OpenAI clients."""
        self.plex = plex_server or PlexServer(settings.plex_url, settings.plex_token)
        self.openai_client = openai_client or OpenAI(api_key=settings.openai_api_key)
        self.assistant_id: Optional[str] = None
        self.vector_store_id: Optional[str] = None
        
    def _get_plex_library(self):
        """Get the configured Plex library section."""
        try:
            return self.plex.library.section(settings.plex_library_name)
        except Exception as e:
            logger.error(f"Error accessing Plex library '{settings.plex_library_name}': {e}")
            raise
    
    def _movie_to_dict(self, movie: Movie) -> Dict[str, Any]:
        """Convert Plex movie object to dictionary with rich metadata."""
        # Determine watch status
        status = "Watched" if getattr(movie, 'viewCount', 0) > 0 else "Unwatched"
        
        # Extract genres
        genres = [genre.tag for genre in getattr(movie, 'genres', [])]
        
        # Extract directors
        directors = [director.tag for director in getattr(movie, 'directors', [])]
        
        # Extract actors (top 3)
        actors = [role.tag for role in getattr(movie, 'roles', [])[:3]]
        
        return {
            "title": movie.title,
            "year": getattr(movie, 'year', None),
            "director": ", ".join(directors) if directors else "Unknown",
            "genre": ", ".join(genres) if genres else "Unknown",
            "plot": getattr(movie, 'summary', "No plot available"),
            "actors": ", ".join(actors) if actors else "Unknown",
            "rating": getattr(movie, 'rating', 0.0),
            "status": status,
            "ratingKey": movie.ratingKey
        }
    
    def sync_library(self) -> Dict[str, Any]:
        """
        Sync Plex library to OpenAI Vector Store.
        
        Returns:
            Dictionary with sync results including file_id and vector_store_id
        """
        logger.info("Starting library sync process...")
        
        try:
            # Fetch all movies from Plex
            library = self._get_plex_library()
            movies = library.all()
            logger.info(f"Found {len(movies)} movies in Plex library")
            
            # Convert movies to JSON dataset
            movies_data = [self._movie_to_dict(movie) for movie in movies]
            json_content = json.dumps(movies_data, indent=2, ensure_ascii=False)
            
            # Create or get assistant
            self._ensure_assistant()
            
            # Create or get vector store
            self._ensure_vector_store()
            
            # Upload JSON file to OpenAI
            logger.info("Uploading movie library to OpenAI...")
            file_response = self.openai_client.files.create(
                file=("movies_library.json", json_content.encode('utf-8')),
                purpose="assistants"
            )
            
            # Add file to vector store
            self.openai_client.beta.vector_stores.files.create(
                vector_store_id=self.vector_store_id,
                file_id=file_response.id
            )
            
            logger.info(f"Successfully synced {len(movies_data)} movies to OpenAI")
            logger.info(f"File ID: {file_response.id}, Vector Store ID: {self.vector_store_id}")
            
            return {
                "success": True,
                "movies_count": len(movies_data),
                "file_id": file_response.id,
                "vector_store_id": self.vector_store_id,
                "assistant_id": self.assistant_id
            }
            
        except Exception as e:
            logger.error(f"Error during library sync: {e}", exc_info=True)
            raise
    
    def _ensure_assistant(self):
        """Create or retrieve the OpenAI assistant."""
        try:
            # List existing assistants
            assistants = self.openai_client.beta.assistants.list()
            
            # Find existing assistant by name
            for assistant in assistants.data:
                if assistant.name == settings.openai_assistant_name:
                    self.assistant_id = assistant.id
                    logger.info(f"Found existing assistant: {self.assistant_id}")
                    return
            
            # Create new assistant if not found
            logger.info("Creating new OpenAI assistant...")
            assistant = self.openai_client.beta.assistants.create(
                name=settings.openai_assistant_name,
                instructions=(
                    "Eres un curador experto de cine con un profundo conocimiento de películas, "
                    "directores, géneros y estilos cinematográficos. Tu trabajo es analizar el "
                    "historial de visualización del usuario y recomendar películas NO VISTAS que "
                    "continúen con la misma vibra, tono o estilo. Considera no solo los géneros, "
                    "sino también el ritmo, la dirección, la atmósfera y los temas. Recomienda "
                    "SOLO películas que tengan status='Unwatched'."
                ),
                model=settings.openai_model,
                tools=[{"type": "file_search"}]
            )
            self.assistant_id = assistant.id
            logger.info(f"Created new assistant: {self.assistant_id}")
            
        except Exception as e:
            logger.error(f"Error managing assistant: {e}", exc_info=True)
            raise
    
    def _ensure_vector_store(self):
        """Create or retrieve the vector store."""
        try:
            # List existing vector stores
            vector_stores = self.openai_client.beta.vector_stores.list()
            
            # Find existing vector store by name
            store_name = f"{settings.openai_assistant_name} - Library"
            for vs in vector_stores.data:
                if vs.name == store_name:
                    self.vector_store_id = vs.id
                    logger.info(f"Found existing vector store: {self.vector_store_id}")
                    
                    # Clean up old files
                    self._cleanup_vector_store_files()
                    return
            
            # Create new vector store if not found
            logger.info("Creating new vector store...")
            vector_store = self.openai_client.beta.vector_stores.create(
                name=store_name
            )
            self.vector_store_id = vector_store.id
            logger.info(f"Created new vector store: {self.vector_store_id}")
            
            # Update assistant to use this vector store
            self.openai_client.beta.assistants.update(
                assistant_id=self.assistant_id,
                tool_resources={"file_search": {"vector_store_ids": [self.vector_store_id]}}
            )
            
        except Exception as e:
            logger.error(f"Error managing vector store: {e}", exc_info=True)
            raise
    
    def _cleanup_vector_store_files(self):
        """Remove old files from vector store."""
        try:
            logger.info("Cleaning up old vector store files...")
            files = self.openai_client.beta.vector_stores.files.list(
                vector_store_id=self.vector_store_id
            )
            
            for file in files.data:
                self.openai_client.beta.vector_stores.files.delete(
                    vector_store_id=self.vector_store_id,
                    file_id=file.id
                )
                logger.debug(f"Deleted file {file.id} from vector store")
                
        except Exception as e:
            logger.warning(f"Error cleaning up vector store files: {e}")
    
    def get_recommendations(self) -> List[str]:
        """
        Get movie recommendations based on recent watch history.
        
        Returns:
            List of movie titles recommended
        """
        logger.info("Starting recommendation process...")
        
        try:
            # Ensure assistant and vector store exist
            self._ensure_assistant()
            self._ensure_vector_store()
            
            # Get recent watch history
            library = self._get_plex_library()
            history = library.search(sort='lastViewedAt:desc', limit=settings.history_lookback)
            
            if not history:
                logger.warning("No watch history found")
                return []
            
            # Build context from history
            history_context = self._build_history_context(history)
            logger.info(f"Analyzing {len(history)} recent movies")
            
            # Create thread and message
            thread = self.openai_client.beta.threads.create()
            
            prompt = (
                f"El usuario ha visto recientemente estas películas:\n\n{history_context}\n\n"
                f"Basándote en este historial, analiza el patrón de preferencias (tono, estilo, "
                f"género, directores similares, ritmo) y recomienda {settings.recommendation_count} "
                f"películas NO VISTAS de la biblioteca que continúen con esta vibra. "
                f"IMPORTANTE: Solo recomienda películas con status='Unwatched'. "
                f"Responde SOLO con los títulos de las películas, uno por línea, sin números ni explicaciones."
            )
            
            self.openai_client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=prompt
            )
            
            # Run assistant
            run = self.openai_client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            
            # Wait for completion
            run = self._wait_for_run_completion(thread.id, run.id)
            
            if run.status != 'completed':
                logger.error(f"Run failed with status: {run.status}")
                return []
            
            # Get recommendations
            messages = self.openai_client.beta.threads.messages.list(thread_id=thread.id)
            
            if not messages.data:
                logger.warning("No messages returned from assistant")
                return []
            
            # Extract movie titles from response
            response_text = messages.data[0].content[0].text.value
            recommendations = self._parse_recommendations(response_text)
            
            logger.info(f"Generated {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", exc_info=True)
            raise
    
    def _build_history_context(self, history: List[Movie]) -> str:
        """Build a text context from watch history."""
        context_lines = []
        for movie in history:
            movie_dict = self._movie_to_dict(movie)
            context_lines.append(
                f"- {movie_dict['title']} ({movie_dict['year']}) - "
                f"Director: {movie_dict['director']}, Género: {movie_dict['genre']}"
            )
        return "\n".join(context_lines)
    
    def _wait_for_run_completion(self, thread_id: str, run_id: str, timeout: int = 60):
        """Wait for assistant run to complete."""
        import time
        elapsed = 0
        
        while elapsed < timeout:
            run = self.openai_client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            
            if run.status in ['completed', 'failed', 'cancelled', 'expired']:
                return run
            
            time.sleep(2)
            elapsed += 2
        
        logger.error(f"Run timed out after {timeout} seconds")
        return run
    
    def _parse_recommendations(self, response_text: str) -> List[str]:
        """Parse movie titles from assistant response."""
        # Clean up the response
        lines = response_text.strip().split('\n')
        titles = []
        
        for line in lines:
            # Remove numbering, bullets, and extra whitespace
            cleaned = re.sub(r'^[\d\.\-\*\•]\s*', '', line.strip())
            if cleaned and len(cleaned) > 2:
                titles.append(cleaned)
        
        return titles[:settings.recommendation_count]
    
    def create_playlist(self, movie_titles: List[str]) -> Dict[str, Any]:
        """
        Create or update a Plex playlist with recommended movies.
        
        Args:
            movie_titles: List of movie titles to add to playlist
            
        Returns:
            Dictionary with playlist creation results
        """
        if not settings.enable_plex_playlist:
            logger.info("Plex playlist creation is disabled")
            return {"success": False, "message": "Feature disabled"}
        
        try:
            library = self._get_plex_library()
            
            # Find movies in Plex
            movies_found = []
            movies_not_found = []
            
            for title in movie_titles:
                try:
                    # Try exact match first
                    results = library.search(title=title, limit=1)
                    if results:
                        movies_found.append(results[0])
                    else:
                        movies_not_found.append(title)
                except Exception as e:
                    logger.warning(f"Error searching for '{title}': {e}")
                    movies_not_found.append(title)
            
            if not movies_found:
                logger.warning("No movies found in Plex library")
                return {
                    "success": False,
                    "message": "No se encontraron películas en la biblioteca",
                    "not_found": movies_not_found
                }
            
            # Delete existing playlist if it exists
            try:
                existing_playlist = self.plex.playlist(settings.playlist_name)
                existing_playlist.delete()
                logger.info(f"Deleted existing playlist '{settings.playlist_name}'")
            except:
                pass  # Playlist doesn't exist
            
            # Create new playlist
            playlist = self.plex.createPlaylist(settings.playlist_name, items=movies_found)
            logger.info(f"Created playlist '{settings.playlist_name}' with {len(movies_found)} movies")
            
            return {
                "success": True,
                "playlist_name": settings.playlist_name,
                "movies_added": len(movies_found),
                "movies_not_found": movies_not_found
            }
            
        except Exception as e:
            logger.error(f"Error creating playlist: {e}", exc_info=True)
            raise
