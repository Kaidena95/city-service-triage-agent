# Day 1 — Development Environment Setup
## City Service Triage Agent

> **Purpose:** Documents the complete local development environment setup, core API concepts, and GitHub portfolio setup for the City Service Triage Agent project.

---

## Project Folder Structure

```
city-service-triage-agent/        ← ROOT: the whole project lives here
├── backend/                       ← all Python/API code goes here
│   ├── venv/                      ← isolated Python packages (never touch manually)
│   └── main.py                    ← your FastAPI app
├── frontend/                      ← UI files (Week 1 Day 4)
├── mcp/                           ← AI agent tools (Week 3)
└── docs/                          ← all markdown documentation
```

---

## Core Concepts

### What is an API?

When you use any app — Uber, Instagram, a city portal — the screen you see (frontend) talks to a separate program running on a server (backend). That conversation happens over **HTTP**, the same protocol your browser uses.

An **API** (Application Programming Interface) is the set of defined "doors" into that backend program.

Each door has:

| Part | What it means | Example |
|------|--------------|---------|
| **URL path** | Which door | `/requests` or `/requests/5` |
| **Method** | What you want to do | `GET` = read, `POST` = create |
| **Request body** | Data you send in | `{"description": "broken streetlight"}` |
| **Response** | Data you get back | `{"id": 1, "status": "open"}` |
| **Status code** | Did it work? | `200` OK, `404` not found, `422` bad input |

### HTTP Methods

| Method | Intent | Real-world analogy |
|--------|--------|--------------------|
| `GET` | Read data, no changes | Looking at a menu |
| `POST` | Create something new | Placing an order |
| `PUT/PATCH` | Update something existing | Modifying your order |
| `DELETE` | Remove something | Cancelling your order |

### Why FastAPI?

Plain Python does not know how to listen for HTTP requests. FastAPI handles all the plumbing — you write Python functions and decorate them to say which URL and method they respond to.

FastAPI auto-generates interactive docs at `/docs` so you can test every endpoint in your browser without building a frontend first.

### What is Uvicorn?

FastAPI is the kitchen (logic). Uvicorn is the front door (server). Uvicorn listens on port 8000 and passes HTTP traffic into FastAPI.

### What is a Virtual Environment?

An isolated Python package space scoped to one project. When you `pip install` something with `(venv)` active, it goes into `venv/` not your system Python. Two projects can use different library versions without conflicting.

---

## Setup Steps

### RULE: Always know where you are
```bash
pwd    # prints your current directory — run this before every command
```

---

### Step 1 — Open VS Code and Create Project Folder

1. Open VS Code
2. File → Open Folder
3. Navigate to Desktop
4. New Folder → name it `city-service-triage-agent`
5. Click Open

---

### Step 2 — Open the Integrated Terminal

Press Ctrl + ` (backtick key, top-left under Escape)

```bash
# WHERE: city-service-triage-agent/
pwd
```

Expected:
```
/Users/yourname/Desktop/city-service-triage-agent
```

---

### Step 3 — Create Folder Structure

```bash
# WHERE: city-service-triage-agent/
mkdir backend frontend mcp docs
ls
```

Expected:
```
backend    docs    frontend    mcp
```

---

### Step 4 — Create Virtual Environment Inside Backend

```bash
# WHERE: city-service-triage-agent/
cd backend
```

```bash
# WHERE: city-service-triage-agent/backend/
python3 -m venv venv
ls
```

Expected:
```
venv
```

---

### Step 5 — Activate Virtual Environment

```bash
# WHERE: city-service-triage-agent/backend/
source venv/bin/activate
```

Your prompt changes to show (venv):
```
(venv) yourname@computer backend %
```

> If you do not see (venv), stop. Do not install packages yet.

---

### Step 6 — Install Packages

```bash
# WHERE: city-service-triage-agent/backend/  (venv active)
pip install fastapi "uvicorn[standard]"
```

Verify:
```bash
pip list | grep -E "fastapi|uvicorn"
```

Expected:
```
fastapi    0.x.x
uvicorn    0.x.x
```

---

### Step 7 — Create main.py

In the VS Code Explorer sidebar:
1. Click `backend` folder to expand it
2. Hover over it → click New File icon
3. Name it `main.py` → press Enter
4. Paste the code below
5. Save with Ctrl + S

```python
from fastapi import FastAPI

# Create the FastAPI application instance
# This is the core object that handles all routing
app = FastAPI()

# @app.get("/") is a decorator
# It tells FastAPI: when someone sends a GET request to /  run this function
@app.get("/")
def read_root():
    return {"message": "City Service Triage API is running"}

# A health check endpoint — standard practice in real APIs
# Used by monitoring tools to verify the app is alive
@app.get("/health")
def health_check():
    return {"status": "ok"}
```

---

### Step 8 — Verify main.py is in the Right Place

```bash
# WHERE: city-service-triage-agent/backend/
ls
```

Expected:
```
main.py    venv
```

Cross-check (ignores venv folders):
```bash
find .. -name "main.py" -not -path "*/venv/*"
```

Expected:
```
../backend/main.py
```

---

### Step 9 — Run the Server

```bash
# WHERE: city-service-triage-agent/backend/  (venv active)
uvicorn main:app --reload
```

| Part | Meaning |
|------|---------|
| `uvicorn` | Start the server |
| `main` | Look in `main.py` |
| `:app` | Find the variable named `app` inside it |
| `--reload` | Auto-restart on file save (development only) |

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

---

### Step 10 — Test in Browser

| URL | Expected result |
|-----|----------------|
| `http://127.0.0.1:8000` | `{"message": "City Service Triage API is running"}` |
| `http://127.0.0.1:8000/docs` | Swagger UI interactive testing page |

---

## Key Things to Understand (Interview Prep)

### What does @app.get("/") mean?

- `@` means it is a decorator — a function that wraps another function
- `app.get` means "register a GET method route on this app"
- `"/"` is the URL path — the root of the API
- Together: "when a GET request comes in to `/`, run the function below"

### What is the difference between / and /docs?

- `/` is your actual API endpoint — returns raw JSON data
- `/docs` is the Swagger UI page — FastAPI generates this automatically so you can test your API visually without writing a frontend

### What does --reload do?

It tells uvicorn to watch your files for changes and restart automatically when you save. Development only — in production you never use `--reload` because you do not want the server restarting unexpectedly.

---

## Git Setup — Push to GitHub for Portfolio

### Core Git Concepts

| Term | Plain English |
|------|--------------|
| **Repository** | Your project folder tracked by Git |
| **Commit** | A saved snapshot of your code |
| **Push** | Upload your commits to GitHub |
| **Branch** | A parallel version of your code |
| **.gitignore** | Tells Git which files/folders to never track |

---

### Step 1 — Stop the Server

```bash
Ctrl + C
```

---

### Step 2 — Go to Root Folder

```bash
# WHERE: city-service-triage-agent/backend/
cd ..
pwd
```

Expected:
```
/Users/yourname/Desktop/city-service-triage-agent
```

---

### Step 3 — Create .gitignore

```bash
# WHERE: city-service-triage-agent/
cat > .gitignore << 'EOF'
# Virtual environments
venv/
.venv/

# Python cache files
__pycache__/
*.pyc
*.pyo

# Environment variables (never push secrets)
.env

# Mac system files
.DS_Store
EOF
```

Verify:
```bash
cat .gitignore
```

---

### Step 4 — Initialize Git

```bash
# WHERE: city-service-triage-agent/
git init
```

---

### Step 5 — Configure Identity (one time only)

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

---

### Step 6 — Stage and Commit

```bash
# WHERE: city-service-triage-agent/
git add .
git status
```

You should see green files. You should NOT see venv/.

```bash
git commit -m "Day 1: project structure, FastAPI hello world, environment setup"
git log --oneline
```

---

### Step 7 — Create GitHub Repository

1. Go to github.com and log in
2. Click + icon (top right) → New repository
3. Name: city-service-triage-agent
4. Set to Public
5. Do NOT add README, .gitignore, or license — you already have them locally
6. Click Create repository

---

### Step 8 — Connect and Push

```bash
# WHERE: city-service-triage-agent/
git remote add origin https://github.com/YOUR_USERNAME/city-service-triage-agent.git
git branch -M main
git push -u origin main
```

> GitHub requires a Personal Access Token instead of your regular password.
> Go to: Settings → Developer Settings → Personal Access Tokens → Tokens (classic) → Generate new token
> Check the repo scope. Use the token as your password when git prompts you.

---

### Daily Git Workflow (use this every day going forward)

```bash
# WHERE: city-service-triage-agent/  (root folder always)
git add .
git commit -m "Day X: describe what you built today"
git push
```

Three commands. Every day. Your portfolio grows automatically.

---

## VS Code Extensions to Install

| Extension | Publisher | Purpose |
|-----------|-----------|---------|
| Python | Microsoft | Syntax highlighting, autocomplete, venv support |
| Pylance | Microsoft | Better Python language server |
| GitLens | GitKraken | Visualize git history inline in code |

Install via Ctrl + Shift + X → search by name.

---

## Day 1 Checklist

- [ ] Project folder structure created
- [ ] Virtual environment created inside backend/
- [ ] (venv) shows in terminal prompt
- [ ] FastAPI and uvicorn installed
- [ ] main.py created inside backend/ (not root, not inside venv)
- [ ] Server runs without errors at http://127.0.0.1:8000
- [ ] Both / and /docs return expected content in browser
- [ ] .gitignore created
- [ ] First commit made
- [ ] Pushed to GitHub — visible at your profile URL

---

## Next Step

Day 2: Define the database schema — the ServiceRequest table using SQLModel + SQLite.

---

*Project: City Service Triage Agent*
*Internship: City of Los Angeles — Department of General Services*
*Day 1 — Environment Setup and FastAPI Introduction*
