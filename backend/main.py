# STEP 5 — Update main.py to connect the database
# Open backend/main.py and replace everything with this:

from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once when the app starts up.
    Creates the database file and tables if they don't exist.
    """
    create_db_and_tables()
    yield


# Pass the lifespan function to FastAPI so it runs on startup
app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"message": "City Service Triage API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}