from fastapi import FastAPI

# Create the FastAPI application instance
# This is the core object that handles all routing
app = FastAPI()

# @app.get("/") is a decorator
# It tells FastAPI: "when someone sends a GET request to /  run this function"
@app.get("/")
def read_root():
    return {"message": "City Service Triage API is running"}

# A health check endpoint — standard practice in real APIs
# Used by servers/monitoring tools to verify the app is alive
@app.get("/health")
def health_check():
    return {"status": "ok"}

