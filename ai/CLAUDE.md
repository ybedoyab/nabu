# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Frontend
```bash
npm run dev          # Vite dev server (port 3000)
npm run build        # TypeScript check + Vite build
npm run lint         # ESLint
npm run test         # Vitest
npm run test:coverage
```

### Backend / AI / Data (Python)
```bash
python -m pytest                        # Run all tests
python -m pytest tests/test_foo.py      # Run a single test file
```

### AI CLI (ai/main.py)
```bash
python main.py process    # Load and process publications from CSV
python main.py analyze    # Run AI analysis with checkpoint support
python main.py recommend  # Get article recommendations for a query
python main.py chat       # Interactive chat about selected articles
python main.py checkpoint # Manage analysis progress
```

### Docker (local full-stack)
```bash
docker-compose up --build -d   # Start all 4 services
.\deploy.ps1 --local           # PowerShell deployment helper
```

Service ports: frontend 3000, backend 8000, data 8081.

## Architecture

Nabu is a scientific research assistant: users submit a research query, receive ranked article recommendations, then chat interactively about selected articles. The flow is: **recommend → summarize → chat**.

The project is split into four services under the repo root:

```
frontend/   React 19 + Vite + Tailwind/DaisyUI SPA
backend/    FastAPI HTTP API — bridges frontend to AI service
ai/         Core AI processing module (hexagonal architecture)
data/       Article scraping from arXiv, Google Scholar, PMC
```

### AI module (`ai/src/`)

Follows **hexagonal (ports & adapters)** architecture:

- `domain/` — core entities (Article, ResearchSession, etc.) and business rules
- `ports/` — abstract interfaces (contracts) for inbound and outbound dependencies
- `application/services/` — orchestrates the recommend → summarize → chat workflow
- `adapters/inbound/` — CLI (`research_cli`) and any future HTTP adapters
- `adapters/outbound/` — OpenAI SDK client, data processor (CSV + scraper)
- `infrastructure/` — config loading, logging setup, signal-based checkpoint handlers

Key behaviors:
- **Checkpoint system**: long-running analysis can be interrupted and resumed; state is persisted to disk via signal handlers.
- **Batch processing**: OpenAI calls are batched with concurrency limits (default: 5 concurrent, 1 s delay) to respect rate limits.
- **Async scraping**: `aiohttp` + `BeautifulSoup4` + `trafilatura` fetch and parse full article text from PMC and other sources.

### Backend (`backend/`)

Thin FastAPI layer. Each use-case (recommendations, summaries, chat) maps to a router that delegates directly to the AI service adapter. Session state is managed by the frontend via a session ID passed in requests.

### Frontend (`frontend/src/` or `src/`)

React SPA with react-router-dom. Axios calls hit the backend API. UI components use DaisyUI over Tailwind CSS.

## Configuration

| File | Purpose |
|------|---------|
| `settings.py` (root) | Model names, temperature, limits, file paths |
| `ai/src/infrastructure/config.py` | Loads `settings.py` + `.env` for the AI module |
| `.env` | `OPENAI_API_KEY`, `SERPAPI_API_KEY` — never commit |
| `env.example` | Template for required env vars |
| `docker-compose.yml` | Multi-service orchestration |
| `pytest.ini` | Python test config |

## Key dependencies

- Python 3.12, FastAPI, Pydantic v2, OpenAI SDK 1.x, LangChain 0.1
- spaCy 3.7, PDFPlumber/PyMuPDF, pandas 2, BeautifulSoup4
- React 19, TypeScript 5.9, Vite 7, Tailwind 4, DaisyUI 5, Vitest
