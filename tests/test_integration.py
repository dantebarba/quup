import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
import os
import json

# Setup environment variables for testing
os.environ["API_AUTH_TOKEN"] = "test-token"
os.environ["PLEX_URL"] = "http://localhost:32400"
os.environ["PLEX_TOKEN"] = "plextoken"
os.environ["PLEX_LIBRARY_NAME"] = "Movies"
os.environ["OPENAI_API_KEY"] = "sk-test"
os.environ["OPENAI_ASSISTANT_NAME"] = "CuratorBot"
os.environ["ENABLE_TELEGRAM"] = "False"

from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_plex():
    with patch("app.core.PlexServer") as mock:
        server_instance = mock.return_value
        library_section = MagicMock()
        server_instance.library.section.return_value = library_section
        
        # Mock Movies
        movie1 = MagicMock()
        movie1.title = "The Matrix"
        movie1.year = 1999
        movie1.directors = [MagicMock(tag="Lana Wachowski")]
        movie1.genres = [MagicMock(tag="Sci-Fi")]
        movie1.summary = "Red pill or blue pill."
        movie1.roles = [MagicMock(tag="Keanu Reeves")]
        movie1.rating = 8.7
        movie1.viewCount = 1 # Watched

        movie2 = MagicMock()
        movie2.title = "Inception"
        movie2.year = 2010
        movie2.directors = [MagicMock(tag="Christopher Nolan")]
        movie2.genres = [MagicMock(tag="Sci-Fi")]
        movie2.summary = "Dreams within dreams."
        movie2.roles = [MagicMock(tag="Leonardo DiCaprio")]
        movie2.rating = 8.8
        movie2.viewCount = 0 # Unwatched

        library_section.all.return_value = [movie1, movie2]
        
        # Mock History
        history_item = MagicMock()
        history_item.title = "The Matrix"
        history_item.rating = 8.7
        history_item.type = 'movie'
        server_instance.history.return_value = [history_item]

        # Mock Search/Playlist
        library_section.search.return_value = [movie2]
        
        yield server_instance

@pytest.fixture
def mock_openai():
    with patch("app.core.AsyncOpenAI") as mock:
        client_instance = mock.return_value
        
        # Mock Assistants List (Async)
        assistant_mock = MagicMock()
        assistant_mock.id = "asst_123"
        assistant_mock.name = "CuratorBot"
        assistant_mock.tool_resources.file_search.vector_store_ids = ["vs_123"]
        
        assistants_list = MagicMock()
        assistants_list.data = [assistant_mock]
        client_instance.beta.assistants.list = AsyncMock(return_value=assistants_list)
        
        # Mock Vector Store Create (Async)
        vs_mock = MagicMock()
        vs_mock.id = "vs_new"
        client_instance.beta.vector_stores.create = AsyncMock(return_value=vs_mock)

        # Mock Vector Store Files List (Async)
        vs_files_list = MagicMock()
        vs_files_list.data = []
        client_instance.beta.vector_stores.files.list = AsyncMock(return_value=vs_files_list)
        
        client_instance.beta.vector_stores.files.delete = AsyncMock()
        client_instance.beta.assistants.update = AsyncMock()
        client_instance.beta.vector_stores.files.create = AsyncMock()

        # Mock File Upload (Async)
        file_mock = MagicMock()
        file_mock.id = "file_123"
        client_instance.files.create = AsyncMock(return_value=file_mock)
        
        # Mock Thread/Run (Async)
        thread_mock = MagicMock()
        thread_mock.id = "thread_123"
        client_instance.beta.threads.create = AsyncMock(return_value=thread_mock)
        
        run_mock = MagicMock()
        run_mock.status = "completed"
        client_instance.beta.threads.runs.create_and_poll = AsyncMock(return_value=run_mock)
        
        # Mock Messages (Async)
        message_mock = MagicMock()
        message_mock.content = [MagicMock()]
        message_mock.content[0].text.value = '["Inception"]'
        
        messages_list = MagicMock()
        messages_list.data = [message_mock]
        client_instance.beta.threads.messages.list = AsyncMock(return_value=messages_list)

        yield client_instance

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_sync_library(mock_plex, mock_openai):
    headers = {"x-api-token": "test-token"}
    response = client.post("/sync", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"

@pytest.mark.asyncio
async def test_recommend_endpoint(mock_plex, mock_openai):
    headers = {"x-api-token": "test-token"}
    response = client.post("/recommend", headers=headers)
    
    if response.status_code != 200:
        print("Error response:", response.json())
        
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Inception" in data["recommendations"]

def test_auth_failure():
    response = client.post("/recommend", headers={"x-api-token": "wrong"})
    assert response.status_code == 403
