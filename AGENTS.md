# Repository Guidelines

## Project Structure & Module Organization
- Root contains `PROMPT.md` (requirements), `README.md` (rules), and `samples/` (mock data like `samples/movies_library.json`).
- Submission branches should include a working app at the root following the prompt’s Python layout:
  - `app/` (`config.py`, `core.py`, `notifiers.py`, `main.py`)
  - `tests/` (integration tests)
  - `Dockerfile`, `docker-compose.yml`, `.env.example`
- Keep user‑facing text in Spanish where applicable.

## Build, Test, and Development Commands
- Local run (dev): `uvicorn app.main:app --reload` (port 8000 by default).
- Tests (pytest): `pytest -q` (aim for clear, minimal suites per limits).
- Docker: `docker compose up --build` (production‑like run on 8000).
- Optional Makefile: `make run`, `make test`, `make lint` for convenience.

## Coding Style & Naming Conventions
- Python 3.13 + FastAPI, type hints everywhere, use `logging` (no `print`).
- 4‑space indentation; `snake_case` for functions/vars, `PascalCase` for classes.
- Recommend `black` + `ruff` (or similar) for formatting/linting.
- Configuration via `pydantic-settings`; all secrets from env variables.

## Testing Guidelines
- Use `pytest`. Provide integration tests; maximum 10 tests across suites.
- Each exposed endpoint (`/sync`, `/recommend`) must have at least one success test.
- Prefer fixtures/mocks; use `samples/movies_library.json` to simulate Plex.
- Keep tests fast, deterministic, and independent.

## Commit & Pull Request Guidelines
- Branch name: the model used (e.g., `gpt-4.1`, `claude-3.5`).
- Commit raw AI output only; avoid manual edits beyond the model’s generation.
- Include a repo `README.md` with model name, yes/no clarification log, and run instructions.
- PRs should: describe the approach, link issues if any, and add screenshots/logs when helpful.
- Commit messages: concise, imperative (e.g., "add api endpoints").

## Security & Configuration Tips
- Required env: `API_AUTH_TOKEN`, Plex URL/Token/Library, OpenAI Key/Model/Assistant, feature toggles, Telegram config.
- Do not commit secrets; provide `.env.example` and document required keys.
- Validate the `x-api-token` header and handle external failures gracefully.

## Architecture Notes
- Follow the prompt’s build order: `config` → `core` → `notifiers` → `main` → Docker.
- Clean the OpenAI Vector Store before upload; recommenders must only select "Unwatched" items.
