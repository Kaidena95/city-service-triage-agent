# Docker Day 2 — Docker Compose
## City Service Triage Agent — DevOps Evolution

> **Purpose:** Documents Docker Compose — what it is, why we need it,
> and how to use it to manage the application stack with one command.

---

## What is Docker Compose?

Docker Compose is a tool for defining and running multi-container
applications. Instead of long `docker run` commands, you define
everything in one `docker-compose.yml` file and start with:

```bash
docker compose up
```

### Why Compose Even With One Service?

Even with just FastAPI right now, Compose is the right practice:
- Documents exactly how the app runs
- Makes environment variables explicit and manageable
- Makes adding a database later trivial (one new block)
- Is what CI/CD pipelines and production environments use

### The Problem It Solves

Without Compose:
```bash
docker run -d -p 8000:8000 --name triage-app \
  -e PYTHONUNBUFFERED=1 \
  -v ./backend/database.db:/app/database.db \
  --restart unless-stopped \
  city-triage-agent:v1
```

With Compose — just:
```bash
docker compose up -d
```

---

## Key Concepts

### Services
Each container is a service. You define each one in docker-compose.yml.
Our app currently has one service: `api`.

### Networks
Compose automatically creates a private network.
Services talk to each other by name, not IP address.
Example: a database service named `db` is reachable at `db:5432`.

### Volumes
Persistent storage that survives container restarts.
Without volumes, data is lost when the container stops.
We mount `database.db` so requests survive restarts.

### Environment Variables
Configuration passed into containers at runtime.
Never hardcoded in the image — that would make the image
environment-specific and prevent reuse.

---

## Files Created

### `docker-compose.yml` (root level)

```yaml
version: "3.8"

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: triage-api
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
      - DATABASE_URL=sqlite:///./database.db
    volumes:
      - ./backend/database.db:/app/database.db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

### Line by Line Explanation

| Section | What it does |
|---------|-------------|
| `version: "3.8"` | Compose file format version |
| `services:` | Defines all containers |
| `api:` | Name of this service |
| `build: context: .` | Build from Dockerfile in current directory |
| `ports: "8000:8000"` | Map Mac port 8000 to container port 8000 |
| `environment:` | Pass variables into the container |
| `volumes:` | Mount host path to container path |
| `restart: unless-stopped` | Auto-restart on crash, not on manual stop |
| `healthcheck:` | Periodically verify the app is alive |

---

### `.env` (root level — NEVER commit to GitHub)

```bash
APP_ENV=development
APP_NAME=city-service-triage-agent
DATABASE_URL=sqlite:///./database.db
API_HOST=0.0.0.0
API_PORT=8000
```

This file is in .gitignore. It holds local configuration.
In production, environment variables are set by the cloud platform.

---

## Commands Reference

### Starting and Stopping

```bash
# Start all services in background
docker compose up -d

# Start and rebuild images first
docker compose up --build -d

# Stop all services
docker compose down

# Stop and delete volumes (careful — deletes data)
docker compose down -v

# Rebuild images without starting
docker compose build
```

### Viewing Status and Logs

```bash
# See running services and their status
docker compose ps

# View all logs
docker compose logs

# Follow logs in real time
docker compose logs -f

# Follow logs for one specific service
docker compose logs -f api
```

### Running Commands Inside Containers

```bash
# Open a shell inside the running container
docker compose exec api bash

# Run pytest inside the container
docker compose exec api pytest tests/ -v

# Run any Python command inside the container
docker compose exec api python3 -c "from triage import classify_request; print(classify_request('broken streetlight'))"
```

---

## The Volume Mount Explained

```yaml
volumes:
  - ./backend/database.db:/app/database.db
```

```
Your Mac                    Container
./backend/database.db  ←→  /app/database.db
```

Without this volume:
- Requests get saved inside the container
- Container stops → all data lost
- Container restarts → empty database

With this volume:
- Requests saved to your Mac's database.db
- Container can stop and restart freely
- Data persists permanently

---

## The Health Check Explained

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

| Setting | Meaning |
|---------|---------|
| `test` | Command to run to check health |
| `interval: 30s` | Check every 30 seconds |
| `timeout: 10s` | If no response in 10s, count as failed |
| `retries: 3` | 3 consecutive failures = unhealthy |
| `start_period: 10s` | Wait 10s after start before checking |

When health check passes: `STATUS: Up (healthy)`
When health check fails: `STATUS: Up (unhealthy)` → Docker can restart

In production (AWS ECS, Kubernetes) the orchestrator uses this
to know if your container needs to be replaced.

---

## How to Run pytest Inside Docker

Always verify tests pass inside the container, not just locally:

```bash
docker compose exec api pytest tests/ -v
```

Why this matters:
- Your local machine has packages the container might not
- The container is the real production environment
- CI/CD will run tests inside Docker — verify it works locally first

---

## Project Structure After Day 2

```
city-service-triage-agent/
├── Dockerfile              ← Day 1: build instructions
├── .dockerignore           ← Day 1: files to exclude
├── docker-compose.yml      ← NEW: service definitions
├── .env                    ← NEW: local config (gitignored)
├── .gitignore              ← updated: .env added
├── README.md
├── backend/
│   ├── requirements.txt    ← Day 1: dependencies
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── schemas.py
│   ├── triage.py
│   └── tests/
├── frontend/
├── mcp/
└── docs/
    ├── DOCKER_DAY1_GUIDE.md
    └── DOCKER_DAY2_GUIDE.md  ← this file
```

---

## How Docker Compose Fits the DevOps Pipeline

```
Local Development:
docker compose up --build
→ app running at localhost:8000
→ tests passing inside container

CI/CD (next phase):
GitHub push
→ GitHub Actions checks out code
→ docker compose build (builds image)
→ docker compose exec api pytest tests/ -v
→ if tests pass: push image to AWS ECR

Production (AWS phase):
AWS pulls image from ECR
→ runs as container with same environment variables
→ health check confirms it's alive
→ traffic routed to healthy containers
```

---

## Interview Prep

### What is Docker Compose and why do you use it?
Docker Compose lets me define my entire application stack in one
YAML file and start everything with `docker compose up`. Even with
a single service, it's the right practice because it documents
exactly how the app runs, makes environment variables explicit,
and makes adding new services trivial. My CI/CD pipeline and
production environment both use the same Compose configuration.

### What is a volume and why does your app need one?
A volume connects a path on the host machine to a path inside the
container. Without a volume, data written inside the container
is lost when the container stops. My app uses SQLite which writes
to a file, so I mount `database.db` as a volume — requests persist
even when the container restarts.

### What is a health check in Docker?
A health check is a command Docker runs periodically to verify
the container is working correctly. Mine calls `GET /health` every
30 seconds. If it fails 3 times in a row, Docker marks the
container as unhealthy. In production, AWS ECS uses this to
automatically replace unhealthy containers without human intervention.

### Why is .env in .gitignore?
The .env file holds environment-specific configuration — and in
production would hold secrets like database passwords and API keys.
Committing secrets to GitHub is one of the most common and
damaging security mistakes in software development. The .env file
stays local. In production, environment variables are injected by
the cloud platform, never stored in the repository.

---

## Git Commit

```bash
cd ~/Desktop/city-service-triage-agent
git add docker-compose.yml .gitignore
git commit -m "feat: add Docker Compose with health check and volume mount"
git push
```

Note: .env is NOT committed — it is in .gitignore intentionally.

---

## Day 2 Checklist

- [ ] docker-compose.yml created at root level
- [ ] .env created and added to .gitignore
- [ ] docker compose up --build starts without errors
- [ ] http://127.0.0.1:8000 returns JSON response
- [ ] docker compose ps shows Up (healthy)
- [ ] docker compose exec api pytest tests/ -v passes
- [ ] docker compose down stops cleanly
- [ ] Committed docker-compose.yml to GitHub
- [ ] .env NOT committed to GitHub

---

## Next Step

Day 3: CI/CD with GitHub Actions — automate testing and
Docker builds every time you push code to GitHub.

---

*Project: City Service Triage Agent — DevOps Evolution*
*Phase 2: Docker*
*Day 2 — Docker Compose*
