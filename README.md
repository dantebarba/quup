# Plex AI Curator (Quup Challenge)

**Model:** GitHub Copilot (Gemini 3 Pro)

## Project Overview

Plex AI Curator is a personalized movie recommendation engine that connects your local Plex Media Server with OpenAI's Assistants API. It analyzes your watch history and recommends unwatched movies from your own library that match the current vibe.

## Features

- **Knowledge Base Sync:** Syncs your Plex movie library to an OpenAI Assistant Vector Store (`/sync`).
- **Smart Recommendations:** Analyzes recent watch history to suggest contextually relevant unwatched movies (`/recommend`).
- **Plex Playlist:** Automatically creates a "Recomendado por IA" playlist in Plex.
- **Telegram Notifications:** Sends recommendations via Telegram in Spanish.

## Architecture

- **Language:** Python 3.13
- **Framework:** FastAPI
- **AI:** OpenAI Assistants API v2 (File Search)
- **Integration:** PlexAPI

## Setup & Configuration

### Prerequisites
- Docker & Docker Compose
- Plex Media Server
- OpenAI API Key

### Environment Variables
Create a `.env` file in the root directory:

```ini
# Security
API_AUTH_TOKEN=your_secure_random_token

# Plex Configuration
PLEX_URL=http://your-plex-ip:32400
PLEX_TOKEN=your_plex_token
PLEX_LIBRARY_NAME=Movies

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4o
OPENAI_ASSISTANT_NAME=PlexCuratorBot

# Feature Toggles
ENABLE_TELEGRAM=True
ENABLE_PLEX_PLAYLIST=True

# Telegram Configuration (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## Deployment

### Using Docker Compose

1. Clone the repository.
2. Create the `.env` file as described above.
3. Build and start the service:

```bash
docker-compose up --build -d
```

The service will be available on port `8000`.

### API Endpoints

- **POST /sync**: Triggers library synchronization (Async). Headers: `x-api-token: <API_AUTH_TOKEN>`
- **POST /recommend**: Generates recommendations. Headers: `x-api-token: <API_AUTH_TOKEN>`
- **GET /health**: Health check.

## Testing

To run the integration tests:

1. Install test dependencies:
```bash
pip install -r requirements.txt
```

2. Run tests:
```bash
pytest tests/
```

Tests verify the endpoints and integration logic using mocks for Plex and OpenAI components.
