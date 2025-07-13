# EXCEED Prolific Orchestrator

This repository orchestrates a full-stack application for code evaluation and survey collection, using Docker Compose to
manage all services. It includes:

- **Frontend**: Next.js app ([exceed-prolific-frontend](https://github.com/alemoraru/exceed-prolific-frontend))
- **Backend**: FastAPI app ([exceed-prolific-backend](https://github.com/alemoraru/exceed-prolific-backend))
- **Database**: PostgreSQL
- **LLM Service**: Ollama (for running LLMs locally/server)
- **Nginx**: for setting up a reverse-proxy (for server deployment)

## Architecture

```
[User] ⇄ [Nginx (Reverse Proxy)] ⇄ [Frontend (Next.js)] ⇄ [Backend (FastAPI)] ⇄ [Postgres]
                                                                ⇂
                                                             [Ollama]
```

- Only the frontend (via nginx) is exposed externally (port 80).
- The `backend`, `db`, and `ollama` services are isolated within the Docker network (no external inbound ports exposed
  except for development convenience).
- The backend connects to the database using the internal hostname `db` and to Ollama using the internal hostname
  `ollama` - this is intentional to ensure that the backend can communicate with these services without exposing them
  externally.
- The frontend connects to the backend via nginx using the `/api` path (e.g., `/api/participants/consent`).
- Nginx proxies `/api` requests to the backend and all other requests to the frontend.
- Nginx caches static assets for improved performance.

## Prerequisites

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

## Running Both on Local and Server Setup

1. Clone the repository.
2. Build and start all services:
   ```sh
   docker compose up --build
   ```
3. Access the application at [http://localhost](http://localhost)

## Environment Variables

- **Frontend**: Uses `NEXT_PUBLIC_BACKEND_HOST` (set to empty) so API calls resolve to `/api/...` and are routed by
  nginx.
- **Backend**: Uses `CORS_ORIGINS` (set to `http://localhost`) to allow requests from the frontend via nginx.

## Notes

- If you need to change the allowed CORS origins, update the `CORS_ORIGINS` environment variable in the backend service
  in `docker-compose.yml`.
- If your backend endpoints are long-running, nginx timeouts for `/api` are increased to 5 minutes by default.
- For development, you can still access backend and frontend containers directly on their respective ports if needed.
