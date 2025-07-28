from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="copyr.ai API",
    description="Premium copyright intelligence infrastructure platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to copyr.ai API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "copyr.ai API", "environment": os.getenv("PYTHON_ENV", "development")}

@app.get("/api/status")
async def api_status():
    return {
        "api": "operational",
        "database": "connected",
        "services": {
            "scraper": "ready",
            "analytics": "ready",
            "export": "ready"
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )