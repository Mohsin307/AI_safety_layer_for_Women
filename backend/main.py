"""
AI Safety Layer for Women - Main FastAPI Application
"""

from fastapi import FastAPI

app = FastAPI(
    title="AI Safety Layer for Women",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {
        "message": "AI Safety Layer Running Successfully"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }