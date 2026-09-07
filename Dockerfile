# ── Stage: Base Python Image ─────────────────────────────────────
# We start from the official Python 3.11 slim image.
# "slim" means it's a smaller version without unnecessary tools.
# This is why your local Python version doesn't matter —
# Docker brings its own Python.
FROM python:3.11-slim

# ── Working Directory ─────────────────────────────────────────────
# All commands from here run inside /app inside the container.
# Think of this as doing "cd /app" inside the container.
WORKDIR /app

# ── Install Dependencies FIRST ────────────────────────────────────
# We copy requirements.txt BEFORE copying all the code.
# Why? Docker caches each layer. If you change your code but not
# your dependencies, Docker reuses the cached pip install layer
# and only rebuilds what changed. This makes builds much faster.
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy Application Code ─────────────────────────────────────────
# Now we copy the actual application files.
# This layer rebuilds every time code changes — that's fine
# because it's fast (just a file copy, no downloads).
COPY backend/ .

# ── Environment Variables ─────────────────────────────────────────
# Tell Python not to write .pyc files (not needed in containers)
# and not to buffer output (so logs appear immediately)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ── Port ──────────────────────────────────────────────────────────
# Document that this container listens on port 8000.
# EXPOSE doesn't actually publish the port — it's documentation.
# We publish it when running with -p 8000:8000
EXPOSE 8000

# ── Start Command ─────────────────────────────────────────────────
# This runs when the container starts.
# --host 0.0.0.0 means "listen on all network interfaces"
# Without this the app only listens inside the container
# and you can't reach it from your browser.
# We do NOT use --reload in production (only for development).
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
