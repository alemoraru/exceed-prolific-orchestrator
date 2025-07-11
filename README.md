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
[User] ⇄ [Nginx] ⇄ [Frontend (Next.js)] ⇄ [Backend (FastAPI)] ⇄ [Postgres]
                                         ⇂
                                      [Ollama]
```

- Only the frontend is exposed externally (via Nginx reverse proxy - configuration for that is separate).
- The `backend`, `db`, and `ollama` services are isolated within the Docker network (i.e., no external iznbound ports
  exposed).

## Prerequisites

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Nginx](https://nginx.org/) (installed on your VM, not in Docker)

## Setup Instructions

1. **Clone the repository:**
   ```sh
   # Or SSH clone if you have SSH access set up
   git clone https://alemoraru/exceed-prolific-orchestrator.git
   cd exceed-prolific-orchestrator
   ```

2. **Start all services:**

    * If you want to deploy the full stack application on your local machine, then run:
      ```sh
      docker compose up -d -f docker-compose-local.yml
      ```
    * If you want to deploy the full stack application on a remote webserver, then run:
      ```shell
      docker compose up -d -f docker-compose.yml
      ```

**Note**: In either case (local vs. remote), this will start the frontend, backend, database, and Ollama services in
detached mode (i.e., running containers in the background).

## Development

- Frontend code: `exceed-prolific-frontend/`
- Backend code: `exceed-prolific-backend/`
- To make changes, edit the respective code and rebuild the containers. This should only be done in development mode
  for quick changes. If you want to properly make changes, then the recommended way is to actually commit those changes
  in the respective repositories and then pull them in here.

If you want to pull in the latest changes from the frontend or backend repositories, you can do so by running:

```sh
git submodule update --remote --merge
```

## Notes

- There are several expectations regarding environment variables for both the frontend and backend services.
    - For the frontend, you will need to set `NEXT_PUBLIC_BACKEND_URL` to the backend URL (e.g.,
      `http://localhost:8000` if running locally).
    - For the backend, you will need to set:
        - `DATABASE_URL`
        - `OLLAMA_URL`
        - `PROLIFIC_FRONTEND_URL`
- Ollama will automatically pull the `llama3.1:8b` model on startup (for now).
- Database data is persisted in Docker volumes.

## License

MIT License
