# Docker Day 1 — Fundamentals & First Dockerfile
## City Service Triage Agent — DevOps Evolution

> **Purpose:** Documents everything learned and built on Docker Day 1 —
> what Docker is, why it matters, and how to containerize a FastAPI app.

---

## The Problem Docker Solves

Before Docker, deploying an app meant:
- "It works on my machine but not the server"
- Python version mismatches
- Missing packages
- Wrong folder structure
- Different operating systems behaving differently

Docker solves this by packaging your app and everything it needs
into a single self-contained unit called a **container**.
That container runs identically on your Mac, on Linux, on AWS — anywhere.

---

## Core Concepts

### Image vs Container

| Term | Analogy | What it is |
|------|---------|-----------|
| **Dockerfile** | A recipe | Text file with build instructions |
| **Image** | A cake mold | The built, reusable template |
| **Container** | A cake | A running instance of the image |

You build an image once. You can run many containers from one image.

```
Dockerfile
    ↓  docker build
Image
    ↓  docker run
Container (your running app)
```

### Why This Matters for DevOps

In CI/CD your pipeline will:
1. Build a Docker image from your Dockerfile
2. Run pytest inside that image
3. Push the image to AWS ECR (a registry)
4. Deploy it to AWS as a running container

Everything from your laptop to production uses the exact same image.
No surprises. No "works on my machine" problems.

### Layers and Caching

Every instruction in a Dockerfile creates a layer.
Docker caches each layer. If nothing changed in that layer,
Docker reuses the cache instead of rebuilding.

This is why we copy requirements.txt BEFORE copying code:
```
COPY requirements.txt .    ← layer 1: only rebuilds if requirements change
RUN pip install ...        ← layer 2: only rebuilds if requirements change
COPY backend/ .            ← layer 3: rebuilds every time code changes
```

If you change main.py, Docker reuses the cached pip install layer
and only rebuilds the code copy layer. Builds go from 45s to 2s.

---

## Files Created

### File 1 — `.dockerignore` (root level)

Tells Docker which files NOT to copy into the image.
Just like .gitignore tells Git what to ignore.

```
# Python
venv/
.venv/
__pycache__/
*.pyc
*.pyo

# Database (local data stays out of the image)
backend/database.db

# Git
.git/
.gitignore

# Environment files (NEVER put secrets in Docker image)
.env
*.env

# Mac system files
.DS_Store
```

Why each entry:
- venv/ — Docker installs packages fresh, venv not needed
- database.db — local test data, not part of the app
- .git/ — version history wastes image space
- .env — secrets must NEVER be baked into images

Location: `city-service-triage-agent/.dockerignore`

---

### File 2 — `Dockerfile` (root level)

```dockerfile
# Start from official Python 3.11 slim image
# "slim" = smaller image without unnecessary tools
# This brings its own Python — local version doesn't matter
FROM python:3.11-slim

# Set working directory inside the container
# All commands from here run inside /app
WORKDIR /app

# Copy requirements FIRST (for layer caching)
# If requirements don't change, Docker reuses the cached pip install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
# This layer rebuilds when code changes — fast because no downloads
COPY backend/ .

# Environment variables
# PYTHONDONTWRITEBYTECODE: don't write .pyc files
# PYTHONUNBUFFERED: show logs immediately (no buffering)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Document that the app listens on port 8000
# EXPOSE is documentation only — doesn't actually publish the port
EXPOSE 8000

# Start command
# --host 0.0.0.0 means listen on all network interfaces
# Without this the app only listens inside the container
# and you cannot reach it from your browser
# No --reload in production (development only)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Location: `city-service-triage-agent/Dockerfile`

---

### File 3 — `backend/requirements.txt`

```
fastapi>=0.100.0
uvicorn[standard]>=0.20.0
sqlmodel>=0.0.14
httpx>=0.24.0
pytest>=7.0.0
mcp>=1.0.0
```

Why this file:
- Docker needs this to know what to install
- Standard Python way to declare dependencies
- CI/CD uses this
- Every Python project should have it

Location: `city-service-triage-agent/backend/requirements.txt`

---

## Dockerfile Instructions Reference

| Instruction | What it does | When to use |
|-------------|-------------|-------------|
| `FROM` | Base image to start from | Always first line |
| `WORKDIR` | Sets working directory inside container | Before copying files |
| `COPY` | Copies files from machine into image | After WORKDIR |
| `RUN` | Executes command during build | Installing packages |
| `ENV` | Sets environment variables | Configuration |
| `EXPOSE` | Documents which port the app uses | Before CMD |
| `CMD` | The command that starts your app | Always last line |

---

## Commands Reference

### Build an image

```bash
# WHERE: city-service-triage-agent/ (root)
docker build -t city-triage-agent:v1 .
```

| Part | Meaning |
|------|---------|
| `docker build` | Build an image from a Dockerfile |
| `-t city-triage-agent:v1` | Tag with name:version |
| `.` | Build context is current directory |

First build takes 1-2 minutes (downloads Python image).
Subsequent builds are much faster due to layer caching.

---

### List your images

```bash
docker images
```

Expected output:
```
REPOSITORY          TAG    IMAGE ID       SIZE
city-triage-agent   v1     abc123def456   180MB
```

---

### Run a container

```bash
# Run in foreground (you see logs)
docker run -p 8000:8000 city-triage-agent:v1

# Run in background (detached mode)
docker run -d -p 8000:8000 --name triage-app city-triage-agent:v1
```

| Flag | Meaning |
|------|---------|
| `-p 8000:8000` | Connect Mac port 8000 to container port 8000 |
| `-d` | Detached — runs in background |
| `--name triage-app` | Give the container a memorable name |

### What -p 8000:8000 means

```
-p HOST_PORT:CONTAINER_PORT
-p 8000:8000
    ↑         ↑
 Your Mac   Inside container
```

Without -p you cannot reach the app from your browser.
The app runs inside an isolated network unless you open a port.

---

### Manage running containers

```bash
# See running containers
docker ps

# See all containers (including stopped)
docker ps -a

# View container logs
docker logs triage-app

# Follow logs in real time
docker logs -f triage-app

# Stop a container
docker stop triage-app

# Remove a container
docker rm triage-app

# Stop and remove in one command
docker rm -f triage-app
```

---

### Clean up

```bash
# Remove an image
docker rmi city-triage-agent:v1

# Remove all stopped containers
docker container prune

# Remove all unused images
docker image prune

# Nuclear option — remove everything unused
docker system prune
```

---

## Verification Steps

After building and running the image:

| URL | Expected result |
|-----|----------------|
| `http://127.0.0.1:8000` | `{"message": "City Service Triage API is running"}` |
| `http://127.0.0.1:8000/docs` | Swagger UI with all endpoints |
| `http://127.0.0.1:8000/health` | `{"status": "ok"}` |

---

## How Docker Fits Into the DevOps Pipeline

```
You write code
    ↓
git push to GitHub
    ↓
GitHub Actions checks out code
    ↓
docker build (builds image from Dockerfile)
    ↓
docker run pytest (runs tests inside container)
    ↓
docker push to AWS ECR (stores the image)
    ↓
AWS pulls image and runs container
    ↓
Users access the live app
```

Every step uses the same Dockerfile you wrote today.

---

## Key Things to Understand

### Why python:3.11-slim and not just python:3.11?

The full python:3.11 image is ~900MB.
The slim version is ~180MB.
Smaller images:
- Build faster
- Push/pull faster
- Cost less to store in AWS ECR
- Have a smaller security attack surface (fewer installed tools)

### Why --no-cache-dir in pip install?

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

pip normally caches downloaded packages for reuse.
Inside Docker that cache just wastes space — we never reuse it.
--no-cache-dir keeps the image smaller.

### Why COPY backend/ . and not COPY . .?

Your Dockerfile's WORKDIR is /app inside the container.
You only want your Python backend code there — not docs/, frontend/, mcp/.
The container only needs what it runs: your FastAPI app.

### Why no --reload in CMD?

```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

--reload watches for file changes and restarts automatically.
In production files never change while running — the container
is replaced entirely when you deploy a new version.
--reload also adds overhead and is a development-only tool.

---

## Project Structure After Day 1

```
city-service-triage-agent/
├── Dockerfile                ← NEW: container build instructions
├── .dockerignore             ← NEW: files to exclude from image
├── README.md
├── backend/
│   ├── requirements.txt      ← NEW: Python dependencies
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── schemas.py
│   ├── triage.py
│   └── tests/
├── frontend/
├── mcp/
└── docs/
    └── DOCKER_DAY1_GUIDE.md  ← this file
```

---

## Interview Prep

### What is Docker and why do you use it?
Docker packages an application and all its dependencies into a
container that runs identically anywhere. I use it to eliminate
environment differences between my laptop, CI/CD, and production.
My FastAPI app runs the same way on my Mac as it does on AWS
because both use the same Docker image built from the same Dockerfile.

### What is the difference between an image and a container?
An image is a built, immutable template — like a blueprint.
A container is a running instance created from that image — like
a building constructed from the blueprint. You can run many
containers from one image simultaneously.

### Why do you copy requirements.txt before copying the code?
Docker builds in layers and caches each layer. If I copy
requirements.txt first and run pip install, that layer gets cached.
When I change my code, Docker reuses the cached pip install layer
and only rebuilds the code copy layer. This turns a 45-second build
into a 2-second build during development.

### What does --host 0.0.0.0 do?
By default a server listens on localhost — only accessible from
inside the same machine or container. In a Docker container,
that means the app is only reachable from inside the container
itself. Setting --host 0.0.0.0 tells the server to listen on
all network interfaces, which allows traffic to reach it through
the container's published port from the outside world.

---

## Git Commit

```bash
cd ~/Desktop/city-service-triage-agent
git add Dockerfile .dockerignore backend/requirements.txt docs/DOCKER_DAY1_GUIDE.md
git commit -m "feat: add Dockerfile, .dockerignore, and requirements.txt"
git push
```

---

## Day 1 Checklist

- [ ] .dockerignore created at root level
- [ ] Dockerfile created at root level
- [ ] backend/requirements.txt created
- [ ] docker build completes without errors
- [ ] docker images shows city-triage-agent:v1
- [ ] docker run -p 8000:8000 starts the app
- [ ] http://127.0.0.1:8000 returns JSON response
- [ ] http://127.0.0.1:8000/docs shows Swagger UI
- [ ] Committed and pushed to GitHub

---

## Next Step

Day 2: Docker Compose — run the entire app with one command,
add environment variables, and understand container networking.

---

*Project: City Service Triage Agent — DevOps Evolution*
*Phase 2: Docker*
*Day 1 — Fundamentals and First Dockerfile*
