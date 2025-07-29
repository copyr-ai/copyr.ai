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
import asyncio
import logging

# Import our copyright analyzer and database components
from src.copyright_analyzer import CopyrightAnalyzer
from src.database.cache_manager import CacheManager
from src.background.scheduler import background_scheduler

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="copyr.ai API",
    description="Premium copyright intelligence infrastructure platform - Multi-country copyright analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize copyright analyzer and cache manager
copyright_analyzer = CopyrightAnalyzer("US")
cache_manager = CacheManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Start background scheduler on application startup"""
    background_scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop background scheduler on application shutdown"""
    background_scheduler.shutdown()

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
    Analyze copyright status of a work with intelligent caching
    """
    try:
        # Check cache first
        search_query = f"{request.title} {request.author}"
        cached_results = await cache_manager.get_cached_search(search_query, request.work_type)
        
        if cached_results:
            # Return the first matching result from cache
            for cached_work in cached_results:
                if (cached_work.title.lower() in request.title.lower() or 
                    request.title.lower() in cached_work.title.lower()):
                    return CopyrightAnalysisResponse(
                        title=cached_work.title,
                        author_name=cached_work.author or request.author,
                        publication_year=cached_work.publication_year,
                        published=cached_work.publication_year is not None,
                        country=request.country,
                        year_of_death=cached_work.processed_data.get('year_of_death'),
                        work_type=cached_work.work_type,
                        status=cached_work.copyright_status or "Unknown",
                        enters_public_domain=int(cached_work.public_domain_date) if cached_work.public_domain_date and cached_work.public_domain_date.isdigit() else None,
                        source_links=cached_work.processed_data.get('source_links', {}),
                        notes=f"Retrieved from cache - {cached_work.source_api}",
                        confidence_score=cached_work.processed_data.get('confidence_score', 0.8),
                        queried_at=datetime.utcnow().isoformat()
                    )
        
        # Perform fresh analysis
        result = copyright_analyzer.analyze_work(
            title=request.title,
            author=request.author,
            work_type=request.work_type,
            verbose=request.verbose,
            country=request.country
        )
        
        # Cache the result for future use
        try:
            from src.database.models import WorkCache
            # Use normalized identifier to prevent duplicates
            normalized_id = cache_manager._normalize_work_identifier(request.title, request.author)
            
            work_cache = WorkCache(
                title=result.title,
                author=result.author_name,
                publication_year=result.publication_year,
                work_type=result.work_type,
                copyright_status=result.status,
                public_domain_date=str(result.enters_public_domain) if result.enters_public_domain else None,
                source_api="copyright_analyzer",
                source_id=normalized_id,
                raw_data=result.to_dict(),
                processed_data={
                    'confidence_score': result.confidence_score,
                    'source_links': result.source_links,
                    'year_of_death': result.year_of_death
                }
            )
            
            await cache_manager.cache_work(work_cache, "copyright_analyzer", normalized_id)
        except Exception as cache_error:
            logger.warning(f"Cache operation failed: {cache_error}")
        
        return CopyrightAnalysisResponse(**result.to_dict())
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Analysis failed due to internal error"
        )

@app.post("/api/analyze/batch")
async def analyze_works_batch(request: BatchAnalyzeRequest):
    """
    Analyze multiple works in batch with intelligent caching
    """
    try:
        if not request.works:
            raise HTTPException(status_code=400, detail="No works provided")
        
        results = []
        uncached_works = []
        
        # Separate cached and uncached works
        for work in request.works:
            search_query = f"{work.title} {work.author}"
            cached_results = await cache_manager.get_cached_search(search_query, "auto")
            
            # Look for matching cached result
            cached_match = None
            if cached_results:
                for cached_work in cached_results:
                    if (cached_work.title.lower() in work.title.lower() or 
                        work.title.lower() in cached_work.title.lower()):
                        cached_match = cached_work
                        break
            
            if cached_match:
                results.append({
                    'title': cached_match.title,
                    'author_name': cached_match.author or work.author,
                    'publication_year': cached_match.publication_year,
                    'published': cached_match.publication_year is not None,
                    'country': request.country,
                    'year_of_death': cached_match.processed_data.get('year_of_death'),
                    'work_type': cached_match.work_type,
                    'status': cached_match.copyright_status or "Unknown",
                    'enters_public_domain': int(cached_match.public_domain_date) if cached_match.public_domain_date and cached_match.public_domain_date.isdigit() else None,
                    'source_links': cached_match.processed_data.get('source_links', {}),
                    'notes': f"Retrieved from cache - {cached_match.source_api}",
                    'confidence_score': cached_match.processed_data.get('confidence_score', 0.8),
                    'queried_at': datetime.utcnow().isoformat()
                })
            else:
                uncached_works.append((work.title, work.author))
        
        # Analyze uncached works
        if uncached_works:
            fresh_results = copyright_analyzer.analyze_batch(
                uncached_works, verbose=request.verbose, country=request.country
            )
            
            # Cache and add fresh results
            for i, result in enumerate(fresh_results):
                # Cache the result
                try:
                    from src.database.models import WorkCache
                    original_work = uncached_works[i]
                    normalized_id = cache_manager._normalize_work_identifier(original_work[0], original_work[1])
                    
                    work_cache = WorkCache(
                        title=result.title,
                        author=result.author_name,
                        publication_year=result.publication_year,
                        work_type=result.work_type,
                        copyright_status=result.status,
                        public_domain_date=str(result.enters_public_domain) if result.enters_public_domain else None,
                        source_api="copyright_analyzer",
                        source_id=normalized_id,
                        raw_data=result.to_dict(),
                        processed_data={
                            'confidence_score': result.confidence_score,
                            'source_links': result.source_links,
                            'year_of_death': result.year_of_death
                        }
                    )
                    
                    await cache_manager.cache_work(work_cache, "copyright_analyzer", normalized_id)
                except Exception as cache_error:
                    logger.warning(f"Batch cache operation failed: {cache_error}")
                
                results.append(result.to_dict())
        
        return {
            "total_analyzed": len(results),
            "results": results,
            "analyzed_at": datetime.utcnow().isoformat(),
            "cache_hits": len(request.works) - len(uncached_works),
            "fresh_analyses": len(uncached_works)
        }
        
    except Exception as e:
        logger.error(f"Batch analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Batch analysis failed due to internal error"
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

@app.get("/api/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics and performance metrics
    """
    try:
        from src.database.config import supabase
        
        # Get cache statistics
        work_cache_count = supabase.table("work_cache").select("id", count="exact").execute()
        search_cache_count = supabase.table("cache_search_queries").select("query_hash", count="exact").execute()
        
        return {
            "cached_works": work_cache_count.count if hasattr(work_cache_count, 'count') else 0,
            "cached_searches": search_cache_count.count if hasattr(search_cache_count, 'count') else 0,
            "cache_enabled": True,
            "background_scheduler_running": background_scheduler.scheduler.running if background_scheduler.scheduler else False
        }
    except Exception as e:
        return {
            "error": f"Failed to get cache stats: {str(e)}",
            "cache_enabled": False
        }

@app.post("/api/cache/refresh/{source_api}/{source_id}")
async def manually_refresh_cache(source_api: str, source_id: str):
    """
    Manually refresh a specific work's cache
    """
    try:
        success = await background_scheduler.manual_refresh_work(source_api, source_id)
        
        if success:
            return {
                "message": f"Successfully refreshed cache for {source_api}:{source_id}",
                "success": True
            }
        else:
            return {
                "message": f"Failed to refresh cache for {source_api}:{source_id}",
                "success": False
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cache refresh failed: {str(e)}"
        )

@app.delete("/api/cache/clear")
async def clear_all_cache():
    """
    Clear all cache entries (works and search queries)
    """
    try:
        from src.database.config import supabase
        
        # Clear work cache
        work_result = supabase.table("work_cache").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        work_count = len(work_result.data) if work_result.data else 0
        
        # Clear search query cache  
        search_result = supabase.table("cache_search_queries").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        search_count = len(search_result.data) if search_result.data else 0
        
        return {
            "message": "Cache cleared successfully",
            "works_cleared": work_count,
            "search_queries_cleared": search_count,
            "success": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cache clear failed: {str(e)}"
        )

@app.delete("/api/cache/clear/works")
async def clear_works_cache():
    """
    Clear only work cache entries
    """
    try:
        from src.database.config import supabase
        
        result = supabase.table("work_cache").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        count = len(result.data) if result.data else 0
        
        return {
            "message": "Work cache cleared successfully",
            "works_cleared": count,
            "success": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Work cache clear failed: {str(e)}"
        )

@app.delete("/api/cache/clear/searches")
async def clear_search_cache():
    """
    Clear only search query cache entries
    """
    try:
        from src.database.config import supabase
        
        result = supabase.table("cache_search_queries").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        count = len(result.data) if result.data else 0
        
        return {
            "message": "Search cache cleared successfully",
            "search_queries_cleared": count,
            "success": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search cache clear failed: {str(e)}"
        )

@app.delete("/api/cache/clear/expired")
async def clear_expired_cache():
    """
    Clear only expired cache entries
    """
    try:
        deleted_count = await cache_manager.cleanup_expired_cache(days_old=0)  # Clear all expired
        
        return {
            "message": "Expired cache cleared successfully",
            "entries_cleared": deleted_count,
            "success": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Expired cache clear failed: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )