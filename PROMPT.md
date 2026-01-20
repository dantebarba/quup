# Project Mission: Plex AI Curator

You are tasked with building a **Personalized Movie Recommendation Engine** that acts as a bridge between a local Plex Media Server and OpenAI's Assistants API.

**The Core Problem:** The user has a massive library of locally stored movies but suffers from "choice paralysis."
**The Solution:** An automated system that analyzes what the user *just watched*, identifies the "mood/vibe," and creates a playlist of **unwatched** movies from their own library that fit that specific mood.

## 1. Business Logic & Data Flow

### A. The Knowledge Base (Sync Process)
The system must maintain an up-to-date "brain" of the user's library in OpenAI.
* **Trigger:** Async background task (via API `/sync`).
* **Source:** Fetch ALL movies from Plex.
* **Data Transformation:** Create a JSON dataset.
    * *Crucial:* Include rich metadata for semantic search: `Title`, `Year`, `Director`, `Genre`, `Plot Summary`, `Main Actors`, `Rating`.
    * *Filter Tag:* Must include a field `status`: "Watched" or "Unwatched" (based on `viewCount`).
* **Destination:** Upload this JSON to an OpenAI **Vector Store** attached to a specific Assistant.
* *Requirement:* Ensure the Vector Store is cleaned (old files removed) before uploading the new version to prevent hallucinations.

### B. The Recommendation Engine (Analysis Process)
The system acts as a "Netflix Algorithm" but for local files.
* **Trigger:** API endpoint `/recommend`.
* **Input Context:** Fetch the last 5-10 items from the user's Plex History.
* **The AI Persona:** The OpenAI Assistant must act as an expert film curator.
* **The Prompt Strategy:**
    1.  Analyze the user's recent history for themes, tone, pacing, and director style (not just simple genre matching).
    2.  Search the Vector Store (Knowledge Base).
    3.  **Constraint:** STRICTLY recommend movies where `status` is "Unwatched".
    4.  **Goal:** Select 10-15 titles that best continue the "session" or "vibe" of the recent history.
    5.  **Output:** A clean list of movie titles.

### C. The Delivery (User Experience)
Once recommendations are generated, the system must act:
1.  **Plex Playlist:** Create/Overwrite a playlist named "Recomendado por IA" with the matched items.
2.  **Notification (Telegram):** Send a message with the list of movies.
3.  **Localization:** All user-facing text (playlist names, telegram messages, logs shown to user) must be in **SPANISH**.

---

## 2. Technical Architecture

### Core Stack
* **Language:** Python 3.13
* **API Framework:** FastAPI (handling async endpoints and `BackgroundTasks`).
* **AI Engine:** OpenAI Assistants API v2 (`file_search` tool enabled).
* **Integration:** `plexapi` wrapper.

### Configuration (Environment Variables)
The app must be 12-factor app compliant. Use `pydantic-settings`.
* **Security:** `API_AUTH_TOKEN` (Header validation).
* **Plex:** URL, Token, Library Name.
* **OpenAI:** Key, Model (default `gpt-4o`), Assistant Name.
* **Features:** Toggles for `ENABLE_TELEGRAM`, `ENABLE_PLEX_PLAYLIST`.
* **Notification Config:** Telegram Bot Token, Chat ID.

### Infrastructure
* **Docker:** Production-ready `Dockerfile` (slim image).
* **Orchestration:** `docker-compose.yml` exposing port 8000.

---

## 3. Implementation Guidelines for the AI Coder

Please generate the solution in this specific order to ensure logical dependencies:

1.  **`app/config.py`**: Define the strict configuration schema.
2.  **`app/core.py` (The Brain)**:
    * Implement the `sync_library` logic (Plex -> JSON -> OpenAI File Upload).
    * Implement the `get_recommendations` logic (History -> OpenAI Prompt -> Title Parsing).
    * *Note:* Handle text cleaning (titles can be messy).
3.  **`app/notifiers.py`**:
    * Implement modular notifications.
    * Ensure **SPANISH** text formatting (e.g., "🎬 Aquí tienes tus recomendaciones...").
4.  **`app/main.py`**:
    * Wire endpoints `/sync` and `/recommend`.
    * Use `x-api-token` header for security.
5.  **`Dockerfile` & `docker-compose.yml`**: Standard setup.

**Code Quality Requirements:**
* Use `logging` instead of `print`.
* Handle exceptions: If Plex is down or OpenAI is out of credits, the app should not crash; it should return a clean error JSON.
* Use Type Hinting throughout the Python code.

### 4. Acceptance criteria

1. The application should be delivered with integration tests.
2. Up to 10 tests are allowed in one or more the test suites.
3. Each exposed endpoint should be tested with at least one success test case.
4. Sample data located in the repository directory `samples/movies_library.json` can be used to mock Plex API.
5. Documentation for deployment, environment configuration and testing configuration should be included.
6. All tests should pass for the application to be considered accepted.
7. THe aplication should deploy succesfully in order to be considered accepted.
