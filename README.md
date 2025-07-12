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
[User] ⇄ [Frontend (Next.js)] ⇄ [Backend (FastAPI)] ⇄ [Postgres]
                                 ⇂
                              [Ollama]
```

- Only the frontend is exposed externally (via port 3000).
- The `backend`, `db`, and `ollama` services are isolated within the Docker network (no external inbound ports exposed
  except for development convenience).
- The backend connects to the database using the internal hostname `db` and to Ollama using the internal hostname
  `ollama`.
- The frontend connects to the backend using the build-time environment variable `NEXT_PUBLIC_BACKEND_HOST` (set to
  `http://localhost:8000` for local development).

## Prerequisites

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

## Running Locally

1. Clone the repository.
2. Build and start all services:
   ```sh
   docker compose -f docker-compose-local.yml up --build
   ```
3. Access the frontend at [http://localhost:3000](http://localhost:3000).

## Service Details

- **Database**: Accessible only within the Docker network as `db:5432`.
- **Backend**: Accessible as `backend:8000` within the Docker network, and as `localhost:8000` on the host.
- **Ollama**: Accessible as `ollama:11434` within the Docker network. The backend uses the `OLLAMA_URL` environment
  variable set to `http://ollama:11434`.
- **Frontend**: Accessible at [http://localhost:3000](http://localhost:3000). The frontend is built with
  `NEXT_PUBLIC_BACKEND_HOST` set to `http://localhost:8000` for browser requests.

## Notes

- If you change the backend or frontend host/port, update the corresponding environment variables and build args in
  `docker-compose-local.yml`.
- For production, use Nginx as a reverse proxy (see separate configuration in `docker-compose-server.yml`).
