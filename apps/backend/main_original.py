from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any
import uvicorn
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import asyncio
import logging
from urllib.parse import quote

# Import our copyright analyzer
from src.copyright_analyzer import CopyrightAnalyzer

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

# Initialize copyright analyzer
copyright_analyzer = CopyrightAnalyzer("US")

# Initialize database components with error handling
cache_manager = None
background_scheduler = None

try:
    from src.database.cache_manager import CacheManager
    from src.background.scheduler import background_scheduler
    cache_manager = CacheManager()
    logger.info("Database components initialized successfully")
except Exception as e:
    logger.warning(f"Database initialization failed: {e}. Running without caching.")
    cache_manager = None
    background_scheduler = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "https://copyrai.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Start background scheduler on application startup"""
    if background_scheduler:
        try:
            background_scheduler.start()
            logger.info("Background scheduler started successfully")
        except Exception as e:
            logger.warning(f"Failed to start background scheduler: {e}")
    else:
        logger.info("Background scheduler not available")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop background scheduler on application shutdown"""
    if background_scheduler:
        try:
            background_scheduler.shutdown()
            logger.info("Background scheduler stopped successfully")
        except Exception as e:
            logger.warning(f"Failed to stop background scheduler: {e}")
    else:
        logger.info("Background scheduler was not running")

@app.get("/")
async def root():
    return {"message": "Welcome to copyr.ai API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "copyr.ai API", "environment": os.getenv("PYTHON_ENV", "development")}

# Pydantic models for API requests/responses

class SearchRequest(BaseModel):
    author: Optional[str] = Field(None, description="Author or composer name to search for")
    title: Optional[str] = Field(None, description="Title of the work to search for")
    work_type: Optional[Literal["literary", "musical"]] = Field(None, description="Filter by work type")
    limit: int = Field(default=5, description="Maximum number of results to return", ge=1, le=50)
    country: str = Field(default="US", description="Country for copyright analysis")
    user_id: Optional[str] = Field(None, description="User ID to save search to history (optional)")
    
    @property
    def is_specific_work_query(self) -> bool:
        """Returns True if both author and title are provided (specific work lookup)"""
        return bool(self.author and self.title)


class SearchResultItem(BaseModel):
    title: str
    author_name: str
    publication_year: Optional[int]
    work_type: Optional[str] = None  # Can be "literary", "musical", or None if uncertain
    status: str
    enters_public_domain: Optional[int]
    confidence_score: float
    source: str  # Can be a single URL or comma-separated URLs for merged records
    work_type_confidence: Optional[float] = None  # Confidence in work_type classification
    classification_source: Optional[str] = None   # Source of classification (e.g., "LOC_professional_cataloging")

class SearchResponse(BaseModel):
    query: Dict[str, Any]
    results: List[SearchResultItem]
    total_found: int
    source: Literal["database", "api", "mixed"]
    searched_at: str

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

def merge_duplicate_records(results: List[SearchResultItem]) -> List[SearchResultItem]:
    """
    Merge records that are identical except for source URLs
    """
    if not results:
        return results
    
    # Group records by all fields except source
    record_groups = {}
    
    for result in results:
        # Create a key from all fields except source
        key = (
            result.title.lower().strip(),
            result.author_name.lower().strip(), 
            result.publication_year,
            result.work_type,
            result.status,
            result.enters_public_domain,
            round(result.confidence_score, 2)  # Round to avoid minor floating point differences
        )
        
        if key not in record_groups:
            record_groups[key] = []
        record_groups[key].append(result)
    
    # Merge groups with multiple records
    merged_results = []
    for group in record_groups.values():
        if len(group) == 1:
            # Single record, no merging needed
            merged_results.append(group[0])
        else:
            # Multiple records - merge their source URLs
            base_record = group[0]  # Use first record as base
            
            # Collect all unique source URLs
            source_urls = []
            for record in group:
                if record.source and record.source not in source_urls:
                    source_urls.append(record.source)
            
            # Create merged record with combined sources
            merged_record = SearchResultItem(
                title=base_record.title,
                author_name=base_record.author_name,
                publication_year=base_record.publication_year,
                work_type=base_record.work_type,
                status=base_record.status,
                enters_public_domain=base_record.enters_public_domain,
                confidence_score=base_record.confidence_score,
                source=", ".join(source_urls) if len(source_urls) > 1 else source_urls[0] if source_urls else ""
            )
            
            merged_results.append(merged_record)
    
    return merged_results

@app.post("/api/search", response_model=SearchResponse)
async def search_works(request: SearchRequest):
    """
    Search for works by author and/or title with filtering options
    Returns top matching works from database first, then API if needed
    When both author and title are provided, returns only the single most relevant result
    """
    try:
        # If no title/author provided, return popular works with filters applied
        if not request.author and not request.title:
            # Use the popular works logic with filtering
            from src.database.config import supabase
            
            # Build the query with filters
            query = supabase.table("work_cache").select("*")
            
            # Apply filters
            if request.work_type and request.work_type in ['literary', 'musical']:
                query = query.eq("work_type", request.work_type)
            
            if request.country and request.country != 'US':
                # For now, we'll skip country filtering as most data is US-based
                pass
            
            # Execute query
            response = query.order("created_at", desc=True).limit(request.limit * 2).execute()
            
            # Format results similar to search results
            results = []
            seen_titles = set()
            
            if response.data:
                for work_data in response.data:
                    if len(results) >= request.limit:
                        break
                        
                    title = work_data.get('title', 'Untitled')
                    # Normalize title for comparison
                    import re
                    title_normalized = re.sub(r'[^\w\s]', '', title.lower().strip())
                    title_normalized = re.sub(r'\s+', ' ', title_normalized).strip()
                    
                    # Skip duplicates
                    if title_normalized in seen_titles:
                        continue
                    
                    seen_titles.add(title_normalized)
                    
                    # Get actual source URLs from database
                    source_url = ""
                    raw_data = work_data.get('raw_data', {})
                    processed_data = work_data.get('processed_data', {})
                    
                    # Priority: raw_data.url > processed_data.source_links > fallback to LOC
                    if raw_data and raw_data.get('url'):
                        source_url = raw_data['url']
                    elif processed_data and processed_data.get('source_links'):
                        # If source_links is a dict, get the first URL
                        source_links = processed_data['source_links']
                        if isinstance(source_links, dict):
                            source_url = next(iter(source_links.values()), "")
                        elif isinstance(source_links, str):
                            source_url = source_links
                    else:
                        # Fallback to LOC search if no source URL available
                        source_url = f"https://catalog.loc.gov/search?q={title.replace(' ', '+')}"
                    
                    # Create search result format
                    result = SearchResultItem(
                        title=title,
                        author_name=work_data.get('author', 'Unknown'),
                        publication_year=work_data.get('publication_year'),
                        work_type=work_data.get('work_type', 'literary'),
                        status=work_data.get('copyright_status', 'Unknown'),
                        enters_public_domain=int(work_data.get('public_domain_date')) if work_data.get('public_domain_date') and str(work_data.get('public_domain_date')).isdigit() else None,
                        confidence_score=work_data.get('processed_data', {}).get('confidence_score', 0.8) if work_data.get('processed_data') else 0.8,
                        source=source_url
                    )
                    results.append(result)
            
            # Return response in search format
            return SearchResponse(
                query={
                    "author": request.author,
                    "title": request.title,
                    "work_type": request.work_type,
                    "limit": request.limit
                },
                results=results,
                total_found=len(results),
                source="database",
                searched_at=datetime.utcnow().isoformat()
            )
        
        results = []
        source = "database"
        
        # For specific work queries (both author and title), limit to 1 result
        effective_limit = 1 if request.is_specific_work_query else request.limit
        
        # Build search query for database
        search_query = ""
        if request.author and request.title:
            search_query = f"{request.title} {request.author}"
        elif request.author:
            search_query = request.author
        else:
            search_query = request.title
        
        # Search in cache first - try both cached query results and direct database search
        if cache_manager:
            # First, try to get cached search query results
            cached_results = await cache_manager.get_cached_search(
                search_query, 
                request.work_type or "auto"
            )
            
            # If no cached query results, search database directly by content
            if not cached_results:
                cached_results = await cache_manager.search_works_directly(
                    title=request.title,
                    author=request.author,
                    work_type=request.work_type,
                    limit=effective_limit
                )
            
            if cached_results:
                # Filter and format cached results
                for cached_work in cached_results[:effective_limit]:
                    # Apply filters with improved work type detection
                    if request.work_type:
                        cached_title_lower = cached_work.title.lower()
                        
                        # Detect if cached work is musical
                        cached_is_musical = (
                            # Check existing work_type field first
                            cached_work.work_type == "musical" or
                            # Musical keywords in title
                            any(keyword in cached_title_lower for keyword in [
                                "opera", "symphony", "concerto", "sonata", "quartet", "quintet",
                                "ballet", "suite", "overture", "prelude", "fugue", "cantata",
                                "mass", "requiem", "oratorio", "waltz", "march", "nocturne",
                                "etude", "mazurka", "polonaise", "scherzo", "minuet", "rondo",
                                "flute", "piano", "violin", "cello", "orchestra", "chamber music",
                                "zauberflöte", "magic flute"
                            ])
                        )
                        
                        cached_is_literary = (
                            cached_work.work_type == "literary" or
                            any(keyword in cached_title_lower for keyword in [
                                "novel", "story", "tales", "poems", "poetry", "prose", "essay"
                            ])
                        )
                        
                        # Filter based on requested type
                        if request.work_type == "musical" and not cached_is_musical:
                            continue
                        elif request.work_type == "literary" and not cached_is_literary:
                            continue
                    
                    # Check if search criteria match
                    title_match = not request.title or (
                        request.title.lower() in cached_work.title.lower() or
                        cached_work.title.lower() in request.title.lower()
                    )
                    author_match = not request.author or (
                        request.author.lower() in (cached_work.author or "").lower() or
                        (cached_work.author or "").lower() in request.author.lower()
                    )
                    
                    if title_match and author_match:
                        # Get the source URL from processed_data or construct from LOC
                        source_url = cached_work.processed_data.get('source_links', {}).get('primary_source', '')
                        if not source_url and cached_work.raw_data:
                            source_url = cached_work.raw_data.get('url', '')
                        if not source_url:
                            source_url = f"cache-{cached_work.source_api}"
                        
                        results.append(SearchResultItem(
                            title=cached_work.title,
                            author_name=cached_work.author or "Unknown",
                            publication_year=cached_work.publication_year,
                            work_type=cached_work.work_type,
                            status=cached_work.copyright_status or "Unknown",
                            enters_public_domain=int(cached_work.public_domain_date) if cached_work.public_domain_date and cached_work.public_domain_date.isdigit() else None,
                            confidence_score=cached_work.processed_data.get('confidence_score', 0.8),
                            source=source_url
                        ))
        
        # If we don't have enough results, search via API
        if len(results) < effective_limit:
            try:
                from src.countries.us.api_clients.library_of_congress import LibraryOfCongressClient
                from src.countries.us.api_clients.hathitrust import HathiTrustClient
                
                api_results = []
                remaining_limit = effective_limit - len(results)
                
                # Keep track of existing titles/authors to avoid duplicates
                existing_works = set()
                for result in results:
                    key = (result.title.lower().strip(), result.author_name.lower().strip())
                    existing_works.add(key)
                
                # Search multiple APIs in parallel for comprehensive results
                all_api_works = []
                
                # Search Library of Congress
                try:
                    loc_client = LibraryOfCongressClient()
                    if request.author and request.title:
                        loc_works = loc_client.search_by_title_and_author(request.title, request.author, limit=remaining_limit * 2)
                    elif request.author:
                        loc_works = loc_client.search_by_author(request.author, limit=remaining_limit * 2)  
                    elif request.title:
                        loc_works = loc_client.search_by_title(request.title, limit=remaining_limit * 2)
                    else:
                        loc_works = []
                    
                    # Add source indicator to LOC results
                    for work in loc_works:
                        work['api_source'] = 'library_of_congress'
                    all_api_works.extend(loc_works)
                    
                except Exception as loc_error:
                    logger.warning(f"Library of Congress search failed: {loc_error}")
                
                # Search MusicBrainz for musical works
                if request.work_type == "musical" or not request.work_type:
                    logger.info(f"Attempting MusicBrainz search for: title='{request.title}', author='{request.author}'")
                    try:
                        from src.countries.us.api_clients.musicbrainz import MusicBrainzClient
                        mb_client = MusicBrainzClient()
                        
                        # Try different search combinations
                        mb_response = None
                        if request.author and request.title:
                            logger.info("Searching MusicBrainz with both title and author")
                            mb_response = mb_client.search_works(request.title, request.author)
                        elif request.author:
                            logger.info("Searching MusicBrainz by composer only")
                            # Search by composer name in artist search first to get works
                            artist_response = mb_client.search_artists(request.author)
                            if artist_response.success and artist_response.data:
                                best_artist = artist_response.data.get('best_match')
                                if best_artist:
                                    logger.info(f"Found artist: {best_artist.get('name')}")
                                    # Could search for works by this artist, but that's complex
                                    # For now, just search works with composer name
                                    mb_response = mb_client.search_works("", request.author)
                        elif request.title:
                            logger.info("Searching MusicBrainz by title only")
                            mb_response = mb_client.search_works(request.title, "")
                            
                        if mb_response and mb_response.success and mb_response.data:
                            mb_works = mb_response.data.get('works', [])
                            logger.info(f"MusicBrainz returned {len(mb_works)} works")
                            
                            # Convert MusicBrainz format to our standard format
                            for work in mb_works:
                                composer_names = [c.get('name', '') for c in work.get('composers', [])]
                                composer_str = ', '.join(composer_names) if composer_names else 'Unknown'
                                
                                formatted_work = {
                                    'title': work.get('title', ''),
                                    'author': composer_str,
                                    'publication_year': None,  # MusicBrainz doesn't typically have publication years
                                    'url': work.get('url', ''),
                                    'format': 'music',
                                    'source': 'musicbrainz',
                                    'api_source': 'musicbrainz'
                                }
                                all_api_works.append(formatted_work)
                                logger.info(f"Added MusicBrainz work: {formatted_work['title']} by {formatted_work['author']}")
                        else:
                            logger.info("MusicBrainz search returned no results or failed")
                                    
                    except Exception as mb_error:
                        logger.warning(f"MusicBrainz search failed: {mb_error}")
                        import traceback
                        logger.warning(f"MusicBrainz error traceback: {traceback.format_exc()}")
                
                # Search HathiTrust (primarily for books, but has some music scores)
                try:
                    hathi_client = HathiTrustClient()
                    # HathiTrust search is limited, but try if we have both title and author
                    if request.author and request.title:
                        hathi_response = hathi_client.search_books(request.title, request.author)
                        if hathi_response.success and hathi_response.data:
                            # HathiTrust returns different format, would need to extract OCLC and lookup
                            # For now, we'll mark this as available but note it needs implementation
                            logger.info("HathiTrust search available but requires OCLC lookup implementation")
                    
                except Exception as hathi_error:
                    logger.warning(f"HathiTrust search failed: {hathi_error}")
                
                # Group API results by similarity and aggregate source URLs
                work_groups = {}  # key: (normalized_title, normalized_author) -> list of works
                
                for work in all_api_works:
                    # Create normalized key for grouping similar works
                    title_norm = work.get("title", "").lower().strip()
                    author_norm = work.get("author", "").lower().strip()
                    
                    # More flexible grouping - handle variations in titles
                    import re
                    title_clean = re.sub(r'[^\w\s]', '', title_norm)
                    title_clean = re.sub(r'\s+', ' ', title_clean).strip()
                    author_clean = re.sub(r'[^\w\s]', '', author_norm) 
                    author_clean = re.sub(r'\s+', ' ', author_clean).strip()
                    
                    group_key = (title_clean, author_clean)
                    
                    if group_key not in work_groups:
                        work_groups[group_key] = []
                    work_groups[group_key].append(work)
                
                # Process grouped works
                for group_key, group_works in work_groups.items():
                    if len(api_results) >= remaining_limit:
                        break
                        
                    # Check for duplicates against existing results
                    if group_key in existing_works:
                        continue
                    
                    # Use the first work as the base, but aggregate all source URLs
                    base_work = group_works[0]
                    all_source_urls = []
                    
                    for work in group_works:
                        source_url = work.get("url", "")
                        if source_url and source_url not in all_source_urls:
                            all_source_urls.append(source_url)
                    
                    # If no URLs found, create fallback URL for LOC works
                    if not all_source_urls:
                        for work in group_works:
                            if work.get("api_source") == "library_of_congress":
                                fallback_url = f"https://catalog.loc.gov/vwebv/search?searchCode=GKEY&searchArg={quote(work.get('title', ''))}"
                                all_source_urls.append(fallback_url)
                                break
                    
                    # Apply work type filter with improved logic
                    if request.work_type:
                        # Check if any work in the group matches the requested type
                        type_match = False
                        for work in group_works:
                            format_type = work.get("format", "").lower()
                            title_lower = work.get("title", "").lower()
                            api_source = work.get("api_source", "")
                            
                            # Detect musical works by title keywords, format, and source
                            is_musical = (
                                # MusicBrainz results are always musical
                                api_source == "musicbrainz" or
                                # Musical keywords in title
                                any(keyword in title_lower for keyword in [
                                    "opera", "symphony", "concerto", "sonata", "quartet", "quintet",
                                    "ballet", "suite", "overture", "prelude", "fugue", "cantata",
                                    "mass", "requiem", "oratorio", "waltz", "march", "nocturne",
                                    "etude", "mazurka", "polonaise", "scherzo", "minuet", "rondo",
                                    "flute", "piano", "violin", "cello", "orchestra", "chamber music"
                                ]) or
                                # Musical format types
                                format_type in ["music", "musical score", "score", "sheet music"] or
                                # Assume non-book formats might be musical if title suggests it
                                (format_type not in ["book", "text", "novel", "poetry"] and 
                                 any(keyword in title_lower for keyword in ["flute", "magic flute", "zauberflöte"]))
                            )
                            
                            is_literary = (
                                format_type in ["book", "text", "novel", "poetry", "prose"] or
                                any(keyword in title_lower for keyword in [
                                    "novel", "story", "tales", "poems", "poetry", "prose", "essay"
                                ])
                            )
                            
                            # Check if this work matches requested type
                            if (request.work_type == "musical" and is_musical) or (request.work_type == "literary" and is_literary):
                                type_match = True
                                break
                        
                        if not type_match:
                            continue
                    
                    # Analyze the work for copyright status using the base work
                    try:
                        # CRITICAL: Always use "auto" for classification - never override with user filter
                        analysis_result = copyright_analyzer.analyze_work(
                            title=base_work.get("title", ""),
                            author=base_work.get("author", ""),
                            work_type="auto",  # Always auto - let professional data decide
                            verbose=False,
                            country=request.country
                        )
                        
                        # Combine all source URLs with comma separation
                        combined_source_urls = ", ".join(all_source_urls) if all_source_urls else ""
                        
                        api_results.append(SearchResultItem(
                            title=analysis_result.title,
                            author_name=analysis_result.author_name,
                            publication_year=analysis_result.publication_year,
                            work_type=analysis_result.work_type,
                            status=analysis_result.status,
                            enters_public_domain=analysis_result.enters_public_domain,
                            confidence_score=analysis_result.confidence_score,
                            source=combined_source_urls,
                            work_type_confidence=analysis_result.work_type_confidence,
                            classification_source=analysis_result.classification_source
                        ))
                        
                        # Add to existing works to prevent future duplicates in this search
                        existing_works.add(group_key)
                        
                        # Cache the result with aggregated source information
                        if cache_manager:
                            try:
                                from src.database.models import WorkCache
                                # Use the primary source API (prefer MusicBrainz for musical works, LOC otherwise)
                                primary_source_api = "library_of_congress"
                                for work in group_works:
                                    if work.get("api_source") == "musicbrainz":
                                        primary_source_api = "musicbrainz"
                                        break
                                
                                normalized_id = cache_manager._normalize_work_identifier(
                                    analysis_result.title, analysis_result.author_name
                                )
                                
                                work_cache = WorkCache(
                                    title=analysis_result.title,
                                    author=analysis_result.author_name,
                                    publication_year=analysis_result.publication_year,
                                    work_type=analysis_result.work_type,
                                    copyright_status=analysis_result.status,
                                    public_domain_date=str(analysis_result.enters_public_domain) if analysis_result.enters_public_domain else None,
                                    source_api=primary_source_api,
                                    source_id=normalized_id,
                                    raw_data=base_work,
                                    processed_data={
                                        'confidence_score': analysis_result.confidence_score,
                                        'source_links': {
                                            **analysis_result.source_links, 
                                            'primary_source': combined_source_urls,
                                            'all_sources': [{'api': work.get('api_source'), 'url': work.get('url')} for work in group_works if work.get('url')]
                                        },
                                        'year_of_death': analysis_result.year_of_death
                                    }
                                )
                                
                                await cache_manager.cache_work(work_cache, primary_source_api, normalized_id)
                            except Exception as cache_error:
                                logger.warning(f"Failed to cache API result: {cache_error}")
                                
                    except Exception as analysis_error:
                        logger.warning(f"Failed to analyze work from API: {analysis_error}")
                        continue
                
                # Add API results to final results
                results.extend(api_results[:remaining_limit])
                
                if api_results:
                    source = "mixed" if len([r for r in results if r.source.startswith("cache")]) > 0 else "api"
                    
                    # Cache the search query if we got results
                    if cache_manager and api_results:
                        try:
                            # Convert API results to WorkCache objects for caching
                            works_to_cache = []
                            for result in api_results:
                                work_cache = WorkCache(
                                    title=result.title,
                                    author=result.author_name,
                                    publication_year=result.publication_year,
                                    work_type=result.work_type,
                                    copyright_status=result.status,
                                    public_domain_date=str(result.enters_public_domain) if result.enters_public_domain else None,
                                    source_api="library_of_congress",
                                    source_id=cache_manager._normalize_work_identifier(result.title, result.author_name),
                                    raw_data={},
                                    processed_data={'confidence_score': result.confidence_score}
                                )
                                works_to_cache.append(work_cache)
                            
                            await cache_manager.cache_search_results(search_query, request.work_type or "auto", works_to_cache)
                        except Exception as cache_error:
                            logger.warning(f"Failed to cache search results: {cache_error}")
                            
            except Exception as api_error:
                logger.warning(f"API search failed: {api_error}")
                if not results:  # If no cache results and API failed
                    raise HTTPException(
                        status_code=503,
                        detail="Search service temporarily unavailable"
                    )
        
        # Merge duplicate records with different source URLs
        merged_results = merge_duplicate_records(results)
        
        # Apply work_type filter AFTER classification (never override classifications)
        if request.work_type and request.work_type in ['literary', 'musical']:
            filtered_results = []
            for result in merged_results:
                if result.work_type == request.work_type:
                    filtered_results.append(result)
                # If work_type is None, we don't know - exclude from filtered results
            merged_results = filtered_results
        
        # Prepare response
        response = SearchResponse(
            query={
                "author": request.author,
                "title": request.title,
                "work_type": request.work_type,
                "limit": request.limit
            },
            results=merged_results[:effective_limit],
            total_found=len(merged_results),
            source=source,
            searched_at=datetime.utcnow().isoformat()
        )
        
        # Save to user history if user_id provided and we have results
        if request.user_id and merged_results:
            try:
                # Create query text for history
                query_parts = []
                if request.author:
                    query_parts.append(f"author: {request.author}")
                if request.title:
                    query_parts.append(f"title: {request.title}")
                if request.work_type:
                    query_parts.append(f"type: {request.work_type}")
                
                query_text = ", ".join(query_parts)
                
                # Convert results to dict format for storage
                results_for_history = []
                for result in merged_results[:effective_limit]:
                    results_for_history.append({
                        "title": result.title,
                        "author_name": result.author_name,
                        "publication_year": result.publication_year,
                        "work_type": result.work_type,
                        "status": result.status,
                        "enters_public_domain": result.enters_public_domain,
                        "confidence_score": result.confidence_score,
                        "source": result.source
                    })
                
                # Save to history using the existing endpoint logic
                from src.database.config import supabase_admin
                
                supabase_admin.table('user_search_history').insert({
                    'user_id': request.user_id,
                    'query_text': query_text,
                    'filters': {
                        'author': request.author,
                        'title': request.title,
                        'work_type': request.work_type,
                        'country': request.country
                    },
                    'results': results_for_history,
                    'result_count': len(results_for_history)
                }).execute()
                
                logger.info(f"Saved search to history for user {request.user_id}: {query_text}")
                
            except Exception as history_error:
                # Don't fail the search if history saving fails
                logger.warning(f"Failed to save search to user history: {history_error}")
        
        return response
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Search failed due to internal error"
        )

@app.get("/api/popular-works")
async def get_popular_works(
    limit: int = 6,
    work_type: Optional[str] = None,
    country: Optional[str] = None,
    status: Optional[str] = None
):
    """
    Get popular/recently analyzed works from the database with filtering support
    
    Args:
        limit: Number of works to return (max 50)
        work_type: Filter by content type ('literary' or 'musical')
        country: Filter by country (e.g., 'US')
        status: Filter by copyright status ('Public Domain', 'Under Copyright', etc.)
    """
    try:
        # Get more works than needed to filter for unique titles and apply filters
        from src.database.config import supabase
        
        # Build the query with filters
        query = supabase.table("work_cache").select("*")
        
        # Apply filters
        if work_type and work_type in ['literary', 'musical']:
            query = query.eq("work_type", work_type)
        
        if country:
            # Note: This assumes we have a country field, might need to adjust based on actual schema
            pass  # For now, skip country filtering as it might not be in the current schema
        
        if status:
            query = query.eq("copyright_status", status)
        
        # Execute query with ordering and limit
        response = query.order("created_at", desc=True).limit(limit * 3).execute()
        
        logger.info(f"Database returned {len(response.data) if response.data else 0} records")
        
        # Format works for frontend display with unique titles
        formatted_works = []
        seen_titles = set()
        
        if response.data:
            for work_data in response.data:
                # Skip if we already have enough works
                if len(formatted_works) >= limit:
                    break
                    
                title = work_data.get('title', 'Untitled')
                # Normalize title for comparison - remove extra spaces, punctuation, etc.
                import re
                title_normalized = re.sub(r'[^\w\s]', '', title.lower().strip())
                title_normalized = re.sub(r'\s+', ' ', title_normalized).strip()
                
                # Skip if we've already seen this title
                if title_normalized in seen_titles:
                    continue
                
                seen_titles.add(title_normalized)
                
                # Create slug from title
                slug = title.lower().replace(' ', '-').replace("'", "").replace('"', '')
                import re
                slug = re.sub(r'[^a-z0-9\-]', '', slug)[:50]
                
                # Map work_type to category for frontend
                work_type_val = work_data.get('work_type', 'literary')
                category = "Music" if work_type_val == "musical" else "Literature"
                
                # Get actual copyright status
                copyright_status = work_data.get('copyright_status', 'Unknown')
                
                # Get actual public domain date
                pd_date = work_data.get('public_domain_date')
                enters_pd = None
                if pd_date and str(pd_date).isdigit():
                    enters_pd = int(pd_date)
                
                formatted_work = {
                    "id": work_data.get('id', ''),
                    "slug": slug,
                    "title": title,
                    "author_name": work_data.get('author', 'Unknown'),
                    "publication_year": work_data.get('publication_year'),
                    "published": True,
                    "country": "US",  # Default for now
                    "work_type": work_type_val,
                    "status": copyright_status,
                    "enters_public_domain": enters_pd,
                    "source": f"https://catalog.loc.gov/search?q={title.replace(' ', '+')}",
                    "notes": f"Work from {work_data.get('source_api', 'database')}",
                    "confidence_score": work_data.get('processed_data', {}).get('confidence_score', 0.8) if work_data.get('processed_data') else 0.8,
                    "queried_at": work_data.get('created_at'),
                    "category": category
                }
                formatted_works.append(formatted_work)
        
        logger.info(f"Returning {len(formatted_works)} formatted works")
        return {
            "works": formatted_works,
            "total": len(formatted_works)
        }
        
    except Exception as e:
        logger.error(f"Failed to get popular works: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"works": [], "total": 0}




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


# User Authentication and Search History Models
class UserProfile(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

class SearchHistoryItem(BaseModel):
    query_text: str
    filters: Dict[str, Any] = {}
    results: List[Dict[str, Any]] = []
    result_count: int = 0

class SearchHistoryResponse(BaseModel):
    id: str
    query_text: str
    filters: Dict[str, Any]
    results: List[Dict[str, Any]]
    result_count: int
    searched_at: str

# User Authentication Endpoints
@app.get("/api/user/{user_id}/profile")
async def get_user_profile(user_id: str):
    """
    Get user profile information
    """
    try:
        from src.database.config import supabase_admin
        
        result = supabase_admin.table('user_profiles').select('*').eq('id', user_id).execute()
        
        if not result.data:
            # User profile doesn't exist, try to get user info from auth and create profile
            try:
                # Get user from auth system
                auth_user = supabase_admin.auth.admin.get_user_by_id(user_id)
                if auth_user.user:
                    # Create profile from auth user data
                    profile_data = {
                        'id': user_id,
                        'email': auth_user.user.email,
                        'full_name': auth_user.user.user_metadata.get('full_name') or auth_user.user.user_metadata.get('name'),
                        'avatar_url': auth_user.user.user_metadata.get('avatar_url') or auth_user.user.user_metadata.get('picture')
                    }
                    
                    create_result = supabase_admin.table('user_profiles').insert(profile_data).execute()
                    if create_result.data:
                        return create_result.data[0]
            except Exception as create_error:
                logger.error(f"Failed to create user profile: {str(create_error)}")
            
            raise HTTPException(status_code=404, detail="User profile not found and could not be created")
        
        return result.data[0]
    except Exception as e:
        logger.error(f"Failed to get user profile: {str(e)}")
        logger.error(f"User ID: {user_id}")
        logger.error(f"Query result: {result if 'result' in locals() else 'No result'}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user profile: {str(e)}")

@app.post("/api/user/{user_id}/search-history")
async def save_search_history(user_id: str, search_data: SearchHistoryItem):
    """
    Save a search to user's history
    """
    try:
        from src.database.config import supabase_admin
        
        result = supabase_admin.table('user_search_history').insert({
            'user_id': user_id,
            'query_text': search_data.query_text,
            'filters': search_data.filters,
            'results': search_data.results,
            'result_count': search_data.result_count
        }).execute()
        
        return {
            "message": "Search saved to history successfully",
            "search_id": result.data[0]['id'] if result.data else None
        }
    except Exception as e:
        logger.error(f"Failed to save search history: {str(e)}")
        logger.error(f"User ID: {user_id}")
        logger.error(f"Search data: {search_data}")
        raise HTTPException(status_code=500, detail=f"Failed to save search to history: {str(e)}")

@app.get("/api/user/{user_id}/search-history", response_model=List[SearchHistoryResponse])
async def get_user_search_history(user_id: str, limit: int = 20):
    """
    Get user's search history
    """
    try:
        from src.database.config import supabase
        
        result = supabase.table('user_search_history')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('searched_at', desc=True)\
            .limit(limit)\
            .execute()
        
        # Convert datetime to string for JSON serialization
        history_items = []
        for item in result.data:
            history_items.append({
                'id': item['id'],
                'query_text': item['query_text'],
                'filters': item['filters'] or {},
                'results': item['results'] or [],
                'result_count': item['result_count'],
                'searched_at': item['searched_at']
            })
        
        return history_items
    except Exception as e:
        logger.error(f"Failed to get search history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve search history")

@app.delete("/api/user/{user_id}/search-history/{search_id}")
async def delete_search_history_item(user_id: str, search_id: str):
    """
    Delete a specific search from user's history
    """
    try:
        from src.database.config import supabase
        
        result = supabase.table('user_search_history')\
            .delete()\
            .eq('id', search_id)\
            .eq('user_id', user_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Search history item not found")
        
        return {"message": "Search history item deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete search history item: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete search history item")

@app.delete("/api/user/{user_id}/search-history")
async def clear_user_search_history(user_id: str):
    """
    Clear all search history for a user
    """
    try:
        from src.database.config import supabase
        
        result = supabase.table('user_search_history')\
            .delete()\
            .eq('user_id', user_id)\
            .execute()
        
        return {
            "message": "Search history cleared successfully",
            "items_deleted": len(result.data) if result.data else 0
        }
    except Exception as e:
        logger.error(f"Failed to clear search history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear search history")

@app.get("/api/autocomplete")
async def get_autocomplete_suggestions(q: str = "", limit: int = 10):
    """
    Get autocomplete suggestions from database for titles, authors, and categories
    Filters suggestions based on query parameter
    """
    try:
        from src.database.config import supabase
        
        if not q or len(q.strip()) < 2:
            return {"sections": []}
        
        query_lower = q.lower().strip()
        
        # Get titles and authors from work_cache that match the query
        response = supabase.table("work_cache").select("title, author, work_type").limit(500).execute()
        
        if not response.data:
            return {"sections": []}
        
        # Filter and collect matching titles, authors, and categories
        matching_titles = set()
        matching_authors = set()
        categories = set()
        
        for work in response.data:
            # Check titles
            if work.get('title'):
                title = work['title'].strip()
                if query_lower in title.lower():
                    matching_titles.add(title)
            
            # Check authors  
            if work.get('author'):
                author = work['author'].strip()
                if query_lower in author.lower():
                    matching_authors.add(author)
            
            # Always include available categories
            if work.get('work_type'):
                if work['work_type'] == 'literary':
                    categories.add('Literature')
                elif work['work_type'] == 'musical':
                    categories.add('Music')
        
        # Convert to sorted lists and limit
        title_list = sorted(list(matching_titles))[:limit]
        author_list = sorted(list(matching_authors))[:limit]
        category_list = sorted(list(categories))
        
        # Only include sections that have matches
        sections = []
        
        if title_list:
            sections.append({
                "title": "Work Titles",
                "icon": "📖",
                "items": title_list
            })
        
        if author_list:
            sections.append({
                "title": "Authors", 
                "icon": "👤",
                "items": author_list
            })
        
        if category_list and any(query_lower in cat.lower() for cat in category_list):
            sections.append({
                "title": "Categories",
                "icon": "🏷️", 
                "items": [cat for cat in category_list if query_lower in cat.lower()]
            })
        
        return {"sections": sections}
        
    except Exception as e:
        logger.error(f"Failed to get autocomplete suggestions: {str(e)}")
        return {"sections": []}

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )