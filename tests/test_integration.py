"""Integration tests for Plex AI Curator."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path

from fastapi.testclient import TestClient
from openai.types.beta import Assistant, VectorStore
from openai.types.beta.threads import Run, Message, MessageContent
from openai.types.beta.threads.text import Text
from openai.types import FileObject
from plexapi.exceptions import NotFound

from app.main import app
from app.core import PlexAICurator
from app.config import settings
from app.notifiers import TelegramNotifier


# Test client
client = TestClient(app)


# Fixtures
@pytest.fixture
def mock_plex_server():
    """Mock Plex server with sample data."""
    # Load sample data
    sample_file = Path(__file__).parent.parent / "samples" / "movies_library.json"
    with open(sample_file) as f:
        data = json.load(f)
    
    movies = []
    for movie_data in data["MediaContainer"]["Metadata"][:20]:  # Use first 20 movies
        movie = Mock()
        movie.title = movie_data["title"]
        movie.year = movie_data.get("year")
        movie.rating = movie_data.get("rating", 0.0)
        movie.summary = movie_data.get("summary", "")
        movie.ratingKey = movie_data["ratingKey"]
        movie.viewCount = movie_data.get("viewCount", 0)
        
        # Mock genres
        genres = []
        for genre in movie_data.get("Genre", []):
            g = Mock()
            g.tag = genre["tag"]
            genres.append(g)
        movie.genres = genres
        
        # Mock directors
        directors = []
        for director in movie_data.get("Director", []):
            d = Mock()
            d.tag = director["tag"]
            directors.append(d)
        movie.directors = directors
        
        # Mock roles
        roles = []
        for role in movie_data.get("Role", [])[:3]:
            r = Mock()
            r.tag = role["tag"]
            roles.append(r)
        movie.roles = roles
        
        movies.append(movie)
    
    # Create mock library
    library = Mock()
    library.all.return_value = movies
    library.search.return_value = movies[:5]  # Return first 5 as history
    
    # Create mock server
    server = Mock()
    server.library.section.return_value = library
    server.createPlaylist.return_value = Mock()
    server.playlist.side_effect = NotFound("Playlist not found")
    
    return server


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    client = Mock()
    
    # Mock assistants
    assistant = Mock(spec=Assistant)
    assistant.id = "asst_test123"
    assistant.name = "Plex AI Curator"
    
    client.beta.assistants.list.return_value = Mock(data=[])
    client.beta.assistants.create.return_value = assistant
    client.beta.assistants.update.return_value = assistant
    
    # Mock vector stores
    vector_store = Mock(spec=VectorStore)
    vector_store.id = "vs_test123"
    vector_store.name = "Plex AI Curator - Library"
    
    client.beta.vector_stores.list.return_value = Mock(data=[])
    client.beta.vector_stores.create.return_value = vector_store
    client.beta.vector_stores.files.list.return_value = Mock(data=[])
    client.beta.vector_stores.files.create.return_value = Mock()
    client.beta.vector_stores.files.delete.return_value = Mock()
    
    # Mock file upload
    file_obj = Mock(spec=FileObject)
    file_obj.id = "file_test123"
    client.files.create.return_value = file_obj
    
    # Mock threads and runs
    thread = Mock()
    thread.id = "thread_test123"
    client.beta.threads.create.return_value = thread
    client.beta.threads.messages.create.return_value = Mock()
    
    # Mock run
    run = Mock(spec=Run)
    run.id = "run_test123"
    run.status = "completed"
    client.beta.threads.runs.create.return_value = run
    client.beta.threads.runs.retrieve.return_value = run
    
    # Mock messages response
    text_content = Mock(spec=Text)
    text_content.value = "The Shawshank Redemption\nThe Godfather\nPulp Fiction"
    
    message_content = Mock(spec=MessageContent)
    message_content.text = text_content
    
    message = Mock(spec=Message)
    message.content = [message_content]
    
    client.beta.threads.messages.list.return_value = Mock(data=[message])
    
    return client


@pytest.fixture
def mock_telegram_bot():
    """Mock Telegram bot."""
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=Mock())
    return bot


# Test 1: Health endpoint
def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Plex AI Curator"


# Test 2: Root endpoint
def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert data["app"] == "Plex AI Curator"
    assert "endpoints" in data


# Test 3: Sync endpoint without authentication
def test_sync_endpoint_no_auth():
    """Test sync endpoint rejects requests without valid token."""
    response = client.post("/sync")
    assert response.status_code == 422  # Missing header


# Test 4: Sync endpoint with valid authentication
def test_sync_endpoint_with_auth(mock_plex_server, mock_openai_client):
    """Test sync endpoint with valid authentication."""
    with patch("app.core.PlexServer", return_value=mock_plex_server):
        with patch("app.core.OpenAI", return_value=mock_openai_client):
            response = client.post(
                "/sync",
                headers={"x-api-token": settings.api_auth_token}
            )
            
            assert response.status_code == 202
            data = response.json()
            assert data["success"] is True
            assert "Sincronización iniciada" in data["message"]


# Test 5: Recommend endpoint with valid authentication
def test_recommend_endpoint_with_auth(mock_plex_server, mock_openai_client):
    """Test recommend endpoint with valid authentication."""
    with patch("app.core.PlexServer", return_value=mock_plex_server):
        with patch("app.core.OpenAI", return_value=mock_openai_client):
            response = client.post(
                "/recommend",
                headers={"x-api-token": settings.api_auth_token}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["recommendations"]) > 0


# Test 6: PlexAICurator library sync
def test_curator_sync_library(mock_plex_server, mock_openai_client):
    """Test PlexAICurator sync_library method."""
    curator = PlexAICurator(
        plex_server=mock_plex_server,
        openai_client=mock_openai_client
    )
    
    result = curator.sync_library()
    
    assert result["success"] is True
    assert result["movies_count"] == 20
    assert "file_id" in result
    assert "vector_store_id" in result


# Test 7: PlexAICurator get recommendations
def test_curator_get_recommendations(mock_plex_server, mock_openai_client):
    """Test PlexAICurator get_recommendations method."""
    curator = PlexAICurator(
        plex_server=mock_plex_server,
        openai_client=mock_openai_client
    )
    
    recommendations = curator.get_recommendations()
    
    assert len(recommendations) > 0
    assert isinstance(recommendations, list)
    assert all(isinstance(title, str) for title in recommendations)


# Test 8: PlexAICurator create playlist
def test_curator_create_playlist(mock_plex_server, mock_openai_client):
    """Test PlexAICurator create_playlist method."""
    curator = PlexAICurator(
        plex_server=mock_plex_server,
        openai_client=mock_openai_client
    )
    
    movie_titles = ["2 Fast 2 Furious", "2 Guns"]
    result = curator.create_playlist(movie_titles)
    
    assert result["success"] is True
    assert "playlist_name" in result


# Test 9: Telegram notification (mocked)
@pytest.mark.asyncio
async def test_telegram_notification(mock_telegram_bot):
    """Test Telegram notification sending."""
    # Temporarily enable Telegram for this test
    original_telegram_setting = settings.enable_telegram
    settings.enable_telegram = True
    
    try:
        with patch.object(TelegramNotifier, '__init__', lambda x, **kwargs: None):
            notifier = TelegramNotifier()
            notifier.bot = mock_telegram_bot
            notifier.chat_id = "123456"
            
            movie_titles = ["Movie 1", "Movie 2", "Movie 3"]
            result = await notifier.send_recommendations(movie_titles, playlist_created=True)
            
            # Verify send_message was called
            mock_telegram_bot.send_message.assert_called_once()
    finally:
        settings.enable_telegram = original_telegram_setting


# Test 10: End-to-end recommendation flow
def test_end_to_end_recommendation_flow(mock_plex_server, mock_openai_client, mock_telegram_bot):
    """Test complete recommendation flow from API to notification."""
    with patch("app.core.PlexServer", return_value=mock_plex_server):
        with patch("app.core.OpenAI", return_value=mock_openai_client):
            with patch("app.notifiers.Bot", return_value=mock_telegram_bot):
                # Disable Telegram for this test
                original_telegram_setting = settings.enable_telegram
                settings.enable_telegram = False
                
                try:
                    response = client.post(
                        "/recommend",
                        headers={"x-api-token": settings.api_auth_token}
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    
                    assert data["success"] is True
                    assert len(data["recommendations"]) > 0
                    assert "playlist_created" in data
                    
                finally:
                    settings.enable_telegram = original_telegram_setting


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
