import json
import logging
import tempfile
import os
from datetime import datetime
from typing import List, Dict, Any

from plexapi.server import PlexServer
from plexapi.video import Movie
from openai import AsyncOpenAI
from app.config import settings
from app.notifiers import notify_recommendations

logger = logging.getLogger(__name__)

class PlexCurator:
    def __init__(self):
        self.plex = PlexServer(settings.plex_url, settings.plex_token)
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    def _get_movie_metadata(self, movie: Movie) -> Dict[str, Any]:
        """Extracts rich metadata from a Plex Movie object."""
        return {
            "Title": movie.title,
            "Year": movie.year,
            "Director": [d.tag for d in movie.directors] if movie.directors else [],
            "Genre": [g.tag for g in movie.genres] if movie.genres else [],
            "Plot Summary": movie.summary,
            "Main Actors": [r.tag for r in movie.roles][:5] if movie.roles else [], # Top 5 actors
            "Rating": movie.rating,
            "status": "Watched" if (movie.viewCount and movie.viewCount > 0) else "Unwatched"
        }

    async def sync_library(self):
        """Fetches all movies from Plex, creates a JSON dataset, and uploads to OpenAI."""
        logger.info("Starting library sync...")
        try:
            library = self.plex.library.section(settings.plex_library_name)
            all_movies = library.all()
            
            movies_data = [self._get_movie_metadata(movie) for movie in all_movies]
            
            # Create a temporary JSON file
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
                json.dump(movies_data, temp_file, indent=2)
                temp_file_path = temp_file.name
            
            logger.info(f"Exported {len(movies_data)} movies to {temp_file_path}")

            await self._update_openai_knowledge_base(temp_file_path)

            os.remove(temp_file_path)
            logger.info("Library sync completed successfully.")

        except Exception as e:
            logger.error(f"Error during library sync: {e}")
            raise

    async def _update_openai_knowledge_base(self, file_path: str):
        """Uploads the JSON file to the Assistant's Vector Store, cleaning old files first."""
        
        # 1. Find the assistant
        assistants = await self.openai_client.beta.assistants.list(limit=100)
        assistant = next((a for a in assistants.data if a.name == settings.openai_assistant_name), None)
        
        if not assistant:
             raise ValueError(f"Assistant '{settings.openai_assistant_name}' not found.")

        # 2. Get or Create Vector Store
        vector_store_id = None
        if assistant.tool_resources and assistant.tool_resources.file_search and assistant.tool_resources.file_search.vector_store_ids:
            vector_store_id = assistant.tool_resources.file_search.vector_store_ids[0]
        
        if not vector_store_id:
            logger.info("Creating new Vector Store...")
            vector_store = await self.openai_client.beta.vector_stores.create(name=f"{settings.openai_assistant_name}_Store")
            vector_store_id = vector_store.id
            # Update assistant to use this vector store
            await self.openai_client.beta.assistants.update(
                assistant_id=assistant.id,
                tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}
            )
        
        # 3. Clean old files in the Vector Store
        # Listing files in vector store and deleting them
        vector_store_files = await self.openai_client.beta.vector_stores.files.list(vector_store_id=vector_store_id)
        for file in vector_store_files.data:
            await self.openai_client.beta.vector_stores.files.delete(vector_store_id=vector_store_id, file_id=file.id)
            # Also delete the actual file from storage to keep it clean (optional but good practice)
            # await self.openai_client.files.delete(file_id=file.id) 
            # Note: Deleting from vector store removes it from the store. Deleting from files.delete removes it from organization.
            # We'll just remove from vector store for now to ensure we don't hit limits.

        # 4. Upload new file
        logger.info("Uploading new library file to OpenAI...")
        file_obj = await self.openai_client.files.create(
            file=open(file_path, "rb"),
            purpose="assistants"
        )

        # 5. Attach to Vector Store
        await self.openai_client.beta.vector_stores.files.create(
            vector_store_id=vector_store_id,
            file_id=file_obj.id
        )
        logger.info("Vector Store updated.")

    async def get_recommendations(self) -> List[str]:
        """Analyzes watch history and generates recommendations."""
        logger.info("Generating recommendations...")
        
        # 1. Fetch History
        history = self.plex.history(limit=10) # last 10 items
        # Filter for movies only if possible, or just take generic history
        movie_history = [h for h in history if h.type == 'movie']
        recent_watches = [f"{h.title} (Rated: {h.rating or 'N/A'})" for h in movie_history][:10]
        
        if not recent_watches:
            logger.warning("No recent watch history found.")
            return []

        history_context = "\n".join(recent_watches)
        
        # 2. Find Assistant
        assistants = await self.openai_client.beta.assistants.list(limit=100)
        assistant = next((a for a in assistants.data if a.name == settings.openai_assistant_name), None)
        
        if not assistant:
             raise ValueError(f"Assistant '{settings.openai_assistant_name}' not found.")

        # 3. Create Thread and Run
        prompt = (
            f"Based on the user's recent watch history:\n{history_context}\n\n"
            "Analyze the mood, themes, and pacing. Search the knowledge base for 'Unwatched' movies "
            "that match this vibe. Select 10-15 titles. Return ONLY a JSON list of strings, e.g., "
            "[\"Movie A\", \"Movie B\"]. No other text."
        )

        thread = await self.openai_client.beta.threads.create(
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        run = await self.openai_client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant.id
        )

        if run.status == 'completed':
            messages = await self.openai_client.beta.threads.messages.list(
                thread_id=thread.id
            )
            response_text = messages.data[0].content[0].text.value
            
            # Clean and parse response
            try:
                # Remove markdown code blocks if present
                clean_text = response_text.replace("```json", "").replace("```", "").strip()
                recommendations = json.loads(clean_text)
                
                if not isinstance(recommendations, list):
                     logger.error(f"OpenAI returned non-list format: {clean_text}")
                     return []

                # Clean titles (strip whitespace)
                recommendations = [str(t).strip() for t in recommendations]

                # 4. Actions
                if settings.enable_plex_playlist:
                    self._create_plex_playlist(recommendations)
                
                if settings.enable_telegram:
                    await notify_recommendations(recommendations)

                return recommendations

            except json.JSONDecodeError:
                logger.error(f"Failed to parse OpenAI response: {response_text}")
                return []
        else:
            logger.error(f"OpenAI run failed with status: {run.status}")
            return []

    def _create_plex_playlist(self, titles: List[str]):
        """Creates or updates a Plex playlist with the recommended movies."""
        logger.info(f"Creating playlist with {len(titles)} items.")
        library = self.plex.library.section(settings.plex_library_name)
        playlist_items = []
        
        for title in titles:
            # Fuzzy match or exact match? 'get' does exact or first match. 
            # 'search' does partial.
            try:
                # Try exact match first
                results = library.search(title=title, libtype='movie')
                if results:
                    playlist_items.append(results[0])
                else:
                    logger.warning(f"Movie '{title}' not found in library during playlist creation.")
            except Exception as e:
                logger.warning(f"Error searching for '{title}': {e}")
        
        if playlist_items:
            playlist_name = "Recomendado por IA"
            try:
                # Check if playlist exists
                existing_playlists = [pl for pl in self.plex.playlists() if pl.title == playlist_name]
                if existing_playlists:
                    playlist = existing_playlists[0]
                    playlist.delete() # Recreating seems safer/easier than clearing + adding
                
                self.plex.createPlaylist(playlist_name, items=playlist_items)
                logger.info("Playlist created successfully.")
            except Exception as e:
                logger.error(f"Failed to create playlist: {e}")
