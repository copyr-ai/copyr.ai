from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
import uvicorn
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# Import our copyright analyzer
from src.copyright_analyzer import CopyrightAnalyzer

load_dotenv()

app = FastAPI(
    title="copyr.ai API",
    description="Premium copyright intelligence infrastructure platform - Multi-country copyright analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize copyright analyzer (default to US)
copyright_analyzer = CopyrightAnalyzer("US")

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

# Pydantic models for API requests/responses
class AnalyzeRequest(BaseModel):
    title: str = Field(..., description="Title of the work", min_length=1, max_length=500)
    author: str = Field(..., description="Author or composer name", min_length=1, max_length=200)
    work_type: Literal["literary", "musical", "auto"] = Field(default="auto", description="Type of work or auto-detect")
    country: str = Field(default="US", description="Country for copyright analysis")
    verbose: bool = Field(default=False, description="Include detailed analysis steps")

class WorkItem(BaseModel):
    title: str = Field(..., description="Title of the work")
    author: str = Field(..., description="Author or composer name")

class BatchAnalyzeRequest(BaseModel):
    works: List[WorkItem] = Field(..., description="List of works with title and author")
    country: str = Field(default="US", description="Country for copyright analysis")
    verbose: bool = Field(default=False, description="Include detailed analysis steps")

class CopyrightAnalysisResponse(BaseModel):
    title: str
    author_name: str
    publication_year: Optional[int]
    published: bool
    country: str
    year_of_death: Optional[int]
    work_type: str
    status: str
    enters_public_domain: Optional[int]
    source_links: dict
    notes: str
    confidence_score: float
    queried_at: str

@app.get("/api/status")
async def api_status():
    return {
        "api": "operational",
        "services": {
            "copyright_analyzer": "ready",
            "library_of_congress": "ready",
            "hathitrust": "ready",
            "musicbrainz": "ready"
        },
        "supported_countries": CopyrightAnalyzer.get_all_supported_countries(),
        "supported_work_types": ["literary", "musical"],
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/analyze", response_model=CopyrightAnalysisResponse)
async def analyze_work(request: AnalyzeRequest):
    """
    Analyze copyright status of a literary or musical work
    
    This endpoint queries multiple reliable APIs (Library of Congress, HathiTrust, MusicBrainz)
    to gather metadata and calculate public domain status based on US copyright law.
    """
    try:
        result = copyright_analyzer.analyze_work(
            title=request.title,
            author=request.author,
            work_type=request.work_type,
            verbose=request.verbose,
            country=request.country
        )
        
        return CopyrightAnalysisResponse(**result.to_dict())
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

@app.post("/api/analyze/batch")
async def analyze_works_batch(request: BatchAnalyzeRequest):
    """
    Analyze multiple works in batch
    
    Accepts a list of works and returns copyright analysis for each.
    Useful for processing multiple titles efficiently.
    """
    try:
        # Convert request format to expected format
        works = [(work.title, work.author) for work in request.works]
        
        if not works:
            raise HTTPException(status_code=400, detail="No works provided")
        
        results = copyright_analyzer.analyze_batch(works, verbose=request.verbose, country=request.country)
        
        return {
            "total_analyzed": len(results),
            "results": [result.to_dict() for result in results],
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch analysis failed: {str(e)}"
        )

@app.get("/api/examples")
async def get_examples():
    """
    Get example works for testing the API
    """
    return {
        "literary_works": [
            {"title": "Pride and Prejudice", "author": "Jane Austen", "expected_status": "Public Domain"},
            {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "expected_status": "Public Domain"},
            {"title": "Dracula", "author": "Bram Stoker", "expected_status": "Public Domain"}
        ],
        "musical_works": [
            {"title": "Symphony No. 9", "author": "Ludwig van Beethoven", "expected_status": "Public Domain"},
            {"title": "The Magic Flute", "author": "Wolfgang Amadeus Mozart", "expected_status": "Public Domain"},
            {"title": "Carmen", "author": "Georges Bizet", "expected_status": "Public Domain"}
        ]
    }

@app.get("/api/countries")
async def get_supported_countries():
    """
    Get list of supported countries for copyright analysis
    """
    countries = []
    for country_code in CopyrightAnalyzer.get_all_supported_countries():
        country_info = CopyrightAnalyzer.get_country_information(country_code)
        countries.append({
            "code": country_code,
            "name": country_info["name"] if country_info else country_code
        })
    
    return {
        "supported_countries": countries,
        "total_count": len(countries)
    }

@app.get("/api/copyright-info/{country_code}")
async def get_copyright_info(country_code: str = "US"):
    """
    Get information about copyright law rules for a specific country
    """
    try:
        analyzer = CopyrightAnalyzer(country_code.upper())
        return analyzer.get_copyright_info()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/copyright-info")
async def get_default_copyright_info():
    """
    Get information about US copyright law rules (default)
    """
    return await get_copyright_info("US")

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )