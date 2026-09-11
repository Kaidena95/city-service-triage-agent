# CI/CD Day 3 — GitHub Actions Pipeline
## City Service Triage Agent — DevOps Evolution

> **Purpose:** Documents the CI/CD pipeline built with GitHub Actions —
> what CI/CD is, why it matters, and how to automate testing and
> Docker builds on every push to GitHub.

---

## What is CI/CD?

CI/CD stands for Continuous Integration / Continuous Deployment.
It is the practice of automatically testing, building, and deploying
your code every time you push to GitHub.

### Without CI/CD
```
You write code
    ↓
You manually run pytest
    ↓
You manually build Docker image
    ↓
You manually deploy
    ↓
You forget a step → production breaks
```

### With CI/CD
```
You write code
    ↓
git push
    ↓
GitHub automatically:
  → checks out your code
  → installs dependencies
  → runs pytest
  → builds Docker image
  → reports pass or fail
```

---

## The Three Terms

| Term | What it means | In your project |
|------|--------------|----------------|
| **Continuous Integration** | Every push triggers automated tests | pytest runs on every push |
| **Continuous Delivery** | Code is always in a deployable state | Docker image built and verified |
| **Continuous Deployment** | Auto-deploys to production | AWS deployment (Phase 5) |

---

## GitHub Actions Key Concepts

| Term | What it is |
|------|-----------|
| **Workflow** | The entire automated process in one YAML file |
| **Trigger** | What starts the workflow (push, pull request) |
| **Job** | A group of steps on the same machine |
| **Step** | One individual task inside a job |
| **Runner** | Fresh Linux VM GitHub provides to run your job |
| **Action** | A reusable pre-built step (like actions/checkout) |

---

## File Created

### `.github/workflows/ci.yml`

Location: `city-service-triage-agent/.github/workflows/ci.yml`

```yaml
name: CI Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:

  test:
    name: Run Tests
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Cache pip packages
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('backend/requirements.txt') }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.txt

      - name: Run pytest
        run: |
          cd backend
          pytest tests/ -v

  docker:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: test

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          dockerfile: Dockerfile
          push: false
          load: true
          tags: city-triage-agent:ci

      - name: Run tests inside Docker
        run: |
          docker run --rm city-triage-agent:ci \
            pytest tests/ -v

      - name: Verify health endpoint
        run: |
          docker run -d -p 8000:8000 --name test-container city-triage-agent:ci
          sleep 5
          curl -f http://localhost:8000/health
          docker rm -f test-container
```

---

## Pipeline Flow Explained

```
git push to main
        ↓
GitHub Actions triggered
        ↓
Job 1: test (runs on fresh Ubuntu VM)
  → checkout code
  → install Python 3.11
  → install pip packages (cached for speed)
  → run pytest tests/ -v
  → if any test fails: STOP, mark commit ❌
        ↓
Job 2: docker (only runs if test passes)
  → checkout code
  → build Docker image from Dockerfile
  → run pytest INSIDE the container
  → start container, curl /health
  → if anything fails: STOP, mark commit ❌
        ↓
All jobs pass: mark commit ✅
```

---

## Why Two pytest Runs?

We run pytest twice on purpose:

**Run 1 — directly with Python:**
- Fast (no Docker build needed)
- Catches Python logic errors immediately
- If this fails we don't waste time building Docker

**Run 2 — inside Docker container:**
- Confirms the container environment is correct
- Verifies Dockerfile installs all packages correctly
- Confirms the app actually works in production-like environment
- Catches issues that only appear in containers

If tests pass locally but fail in Docker — your Dockerfile has a problem.

---

## What needs: test Does

```yaml
docker:
  needs: test    ← only run if test job passes
```

Without this both jobs run simultaneously.
If tests fail you'd waste 3 minutes building a Docker image
for broken code.

With `needs: test`:
- Jobs run in sequence: test first, then docker
- If tests fail, Docker job is skipped entirely
- Faster feedback, no wasted compute time

---

## The pip Cache Step Explained

```yaml
- name: Cache pip packages
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('backend/requirements.txt') }}
```

Every GitHub Actions run starts on a fresh VM.
Without caching: pip downloads all packages every single run (30-60 seconds).
With caching: pip reuses downloaded packages if requirements.txt hasn't changed (2-3 seconds).

The cache key includes a hash of requirements.txt.
If you change requirements.txt the hash changes → cache invalidated → fresh download.
If requirements.txt is unchanged → cache hit → fast install.

---

## YAML Structure Reference

```
name:           (workflow name — shown in GitHub UI)
on:             (trigger definition)
  push:
    branches: [main]
jobs:           (all jobs in this workflow)
  job-name:     (name your job)
    runs-on:    (ubuntu-latest, macos-latest, windows-latest)
    needs:      (other jobs that must pass first)
    steps:      (list of steps)
      - name:   (human readable step name)
        uses:   (pre-built GitHub Action)
        with:   (parameters for the action)
        run:    (shell command to execute)
```

YAML rules:
- Always use spaces, never tabs
- Indentation level determines hierarchy
- Lists start with dash and space: `- item`
- Key-value pairs use colon and space: `key: value`

---

## Status Badge

Add this to README.md right after the title:

```markdown
![CI Pipeline](https://github.com/Kaidena95/city-service-triage-agent/actions/workflows/ci.yml/badge.svg)
```

Shows live pipeline status on your GitHub repo front page:
- Green = all tests passing
- Red = something is broken

Employers and reviewers see this immediately when they visit your repo.

---

## GitHub Actions Tab

After pushing, go to:
`https://github.com/Kaidena95/city-service-triage-agent/actions`

You will see:
- List of all workflow runs
- Status of each run (green check or red X)
- Duration of each run
- Click any run to see detailed step-by-step output

This is your audit trail — every push, every test result, permanently recorded.

---

## Commands Reference

```bash
# Create the workflows directory
mkdir -p .github/workflows

# Create the workflow file
touch .github/workflows/ci.yml

# Push to trigger the pipeline
git add .github/
git commit -m "feat: add GitHub Actions CI pipeline"
git push

# Add status badge to README
# Edit README.md and add the badge line after the title

# Push the badge
git add README.md
git commit -m "docs: add CI status badge to README"
git push
```

---

## How This Connects to the Full DevOps Pipeline

```
Current state after Day 3:

You push code
    ↓
GitHub Actions runs automatically:
  → pytest passes ✅
  → Docker image builds ✅
  → Tests pass inside Docker ✅
  → Health endpoint responds ✅

Coming in Phase 5 (AWS):

After all tests pass:
  → Docker image pushed to AWS ECR
  → AWS pulls new image
  → Container updated in production
  → Zero downtime deployment
```

---

## Project Structure After Day 3

```
city-service-triage-agent/
├── .github/
│   └── workflows/
│       └── ci.yml          ← NEW: CI/CD pipeline
├── Dockerfile
├── .dockerignore
├── docker-compose.yml
├── .env                    (gitignored)
├── README.md               ← updated: CI badge added
├── backend/
│   ├── requirements.txt
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
    ├── DOCKER_DAY2_GUIDE.md
    └── CICD_DAY3_GUIDE.md  ← this file
```

---

## Interview Prep

### What is CI/CD and why does it matter?
CI/CD automates the process of testing and building software on
every code change. Without it, developers manually run tests and
build deployments — steps get skipped, mistakes reach production.
With CI/CD, every push to GitHub automatically triggers tests and
a Docker build. If anything fails the commit is marked with a red
X and no broken code reaches production. My pipeline runs pytest
twice — once directly in Python and once inside the Docker container
— to catch both logic errors and container configuration issues.

### What is GitHub Actions?
GitHub Actions is GitHub's built-in CI/CD system. You define
workflows as YAML files inside .github/workflows/. GitHub reads
these and runs them automatically on triggers you define — like
pushing to main or opening a pull request. Each workflow runs on
a fresh Linux virtual machine called a runner, which GitHub
provides for free for public repositories.

### Why do you run tests twice in your pipeline?
The first run uses Python directly and catches logic errors fast
without waiting for a Docker build. The second run executes pytest
inside the Docker container, which is the actual production
environment. Tests can pass locally but fail in Docker if the
Dockerfile is missing a package or has incorrect configuration.
Running both catches different categories of problems.

### What does the needs keyword do in GitHub Actions?
It defines job dependencies. My docker job has `needs: test`,
which means it only runs after the test job completes successfully.
Without this, both jobs would run simultaneously — wasting 3
minutes building a Docker image for code that has failing tests.
With needs, broken code stops the pipeline at the test stage
and the Docker build is skipped entirely.

---

## Git Commit

```bash
cd ~/Desktop/city-service-triage-agent
git add .github/ README.md docs/CICD_DAY3_GUIDE.md
git commit -m "feat: add GitHub Actions CI pipeline with test and Docker build jobs"
git push
```

---

## Day 3 Checklist

- [ ] .github/workflows/ directory created
- [ ] ci.yml created with test and docker jobs
- [ ] Pushed to GitHub
- [ ] Actions tab shows pipeline running
- [ ] Both jobs show green checkmarks
- [ ] Status badge added to README.md
- [ ] Badge shows green on GitHub repo page

---

## Next Step

Phase 4: Terraform — define your AWS infrastructure as code
so you can provision and destroy cloud resources with one command.

---

*Project: City Service Triage Agent — DevOps Evolution*
*Phase 3: CI/CD*
*Day 3 — GitHub Actions Pipeline*
