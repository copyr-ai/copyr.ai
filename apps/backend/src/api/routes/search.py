from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from pydantic import BaseModel, Field
from ...auth.middleware import optional_auth
from ...core.exceptions import SearchError, ValidationError
from ...core.security import sanitize_search_request, InputSanitizer
from ...repositories.work_repository import WorkRepository
from ...services.external_api_service import external_api_service
# from ...copyright_analyzer import CopyrightAnalyzer  # Import moved to avoid issues
from ...core.logging_config import log_performance, get_logger
from datetime import datetime

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["search"])

# Initialize dependencies
work_repo = WorkRepository()

class SearchRequest(BaseModel):
    author: Optional[str] = Field(None, description="Author or composer name to search for")
    title: Optional[str] = Field(None, description="Title of the work to search for")
    work_type: Optional[str] = Field(None, description="Filter by work type (literary/musical)")
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
    work_type: Optional[str] = None
    status: str
    enters_public_domain: Optional[int]
    confidence_score: float
    source: str
    work_type_confidence: Optional[float] = None
    classification_source: Optional[str] = None

class SearchResponse(BaseModel):
    query: dict
    results: List[SearchResultItem]
    total_found: int
    source: str
    searched_at: str

@router.post("/search", response_model=SearchResponse)
@log_performance("search_works")
async def search_works(
    request: SearchRequest,
    current_user: Optional[dict] = Depends(optional_auth)
):
    """
    Enhanced search endpoint with improved architecture
    """
    try:
        # Input validation and sanitization
        search_data = sanitize_search_request(request.dict())
        
        # Validate search query
        if not search_data.get("author") and not search_data.get("title"):
            # Return popular works if no search criteria
            return await get_popular_works_internal(
                limit=search_data.get("limit", 5),
                work_type=search_data.get("work_type"),
                country=search_data.get("country")
            )
        
        # Search in database first
        results = []
        source = "database"
        
        # For specific work queries, limit to 1 result
        effective_limit = 1 if request.is_specific_work_query else search_data.get("limit", 5)
        
        # Database search
        cached_works = await work_repo.search_by_content(
            title=search_data.get("title"),
            author=search_data.get("author"),
            work_type=search_data.get("work_type"),
            limit=effective_limit
        )
        
        # Convert cached works to search results
        for cached_work in cached_works:
            if len(results) >= effective_limit:
                break
                
            # Apply work type filter if specified
            if (search_data.get("work_type") and 
                cached_work.work_type != search_data["work_type"]):
                continue
            
            # Get source URL from processed data
            source_url = ""
            if cached_work.processed_data and cached_work.processed_data.get('source_links'):
                source_links = cached_work.processed_data['source_links']
                if isinstance(source_links, dict):
                    source_url = source_links.get('primary_source', '')
                elif isinstance(source_links, str):
                    source_url = source_links
            
            if not source_url:
                source_url = f"cache-{cached_work.source_api}"
            
            results.append(SearchResultItem(
                title=cached_work.title,
                author_name=cached_work.author or "Unknown",
                publication_year=cached_work.publication_year,
                work_type=cached_work.work_type,
                status=cached_work.copyright_status or "Unknown",
                enters_public_domain=cached_work.effective_public_domain_year,
                confidence_score=cached_work.processed_data.get('confidence_score', 0.8) if cached_work.processed_data else 0.8,
                source=source_url
            ))
        
        # If not enough results, search external APIs
        if len(results) < effective_limit:
            remaining_limit = effective_limit - len(results)
            
            try:
                # Use the new external API service
                async with external_api_service:
                    api_works = await external_api_service.search_all_sources(
                        title=search_data.get("title"),
                        author=search_data.get("author"),
                        work_type=search_data.get("work_type"),
                        limit=remaining_limit * 2
                    )
                
                # Group and merge similar works
                work_groups = external_api_service.group_similar_works(api_works)
                
                # Process each group
                for group_key, work_group in work_groups.items():
                    if len(results) >= effective_limit:
                        break
                    
                    # Merge works from different sources
                    merged_work = external_api_service.merge_work_sources(work_group)
                    
                    if not merged_work:
                        continue
                    
                    # Apply work type filter
                    if search_data.get("work_type"):
                        # Check if work matches requested type
                        is_match = False
                        title_lower = merged_work.get("title", "").lower()
                        
                        if search_data["work_type"] == "musical":
                            is_match = (
                                merged_work.get("api_source") == "musicbrainz" or
                                any(keyword in title_lower for keyword in [
                                    "opera", "symphony", "concerto", "sonata", "quartet"
                                ])
                            )
                        elif search_data["work_type"] == "literary":
                            is_match = (
                                merged_work.get("format", "").lower() in ["book", "text"] or
                                any(keyword in title_lower for keyword in [
                                    "novel", "story", "tales", "poems"
                                ])
                            )
                        
                        if not is_match:
                            continue
                    
                    # Extract publication year from raw data if not available
                    publication_year = merged_work.get('publication_year')
                    if not publication_year and 'raw_data' in merged_work:
                        # Try to extract from nested data
                        if isinstance(merged_work, dict) and merged_work.get('publication_year'):
                            publication_year = merged_work['publication_year']
                    
                    # Analyze work for copyright status
                    try:
                        # Import here to avoid circular dependency
                        from ...copyright_analyzer import CopyrightAnalyzer
                        copyright_analyzer = CopyrightAnalyzer("US")
                        
                        analysis_result = await copyright_analyzer.analyze_work(
                            title=merged_work.get("title", ""),
                            author=merged_work.get("author", ""),
                            work_type="auto",
                            verbose=False,
                            country=search_data.get("country", "US")
                        )
                        
                        # Get combined source URLs
                        source_urls = merged_work.get('source_urls', [])
                        combined_source = ", ".join(source_urls) if source_urls else merged_work.get('url', '')
                        
                        # Use publication year from API if analysis doesn't provide it
                        effective_pub_year = analysis_result.publication_year or publication_year
                        
                        results.append(SearchResultItem(
                            title=analysis_result.title or merged_work.get("title", ""),
                            author_name=analysis_result.author_name or merged_work.get("author", "Unknown"),
                            publication_year=effective_pub_year,
                            work_type=analysis_result.work_type or "musical",
                            status=analysis_result.status or "Unknown", 
                            enters_public_domain=analysis_result.enters_public_domain,
                            confidence_score=analysis_result.confidence_score or 0.5,
                            source=combined_source,
                            work_type_confidence=getattr(analysis_result, 'work_type_confidence', None),
                            classification_source=getattr(analysis_result, 'classification_source', None)
                        ))
                        
                        # Cache the result for future use
                        try:
                            from ...database.models import WorkCache
                            work_cache = WorkCache(
                                title=analysis_result.title or merged_work.get("title", ""),
                                author=analysis_result.author_name or merged_work.get("author", "Unknown"),
                                publication_year=effective_pub_year,
                                work_type=analysis_result.work_type or "musical",
                                copyright_status=analysis_result.status or "Unknown",
                                public_domain_year=analysis_result.enters_public_domain,
                                source_api=merged_work.get('api_source', 'unknown'),
                                source_id=f"{merged_work.get('title', 'unknown')}_{merged_work.get('author', 'unknown')}".replace(' ', '_'),
                                raw_data=merged_work,
                                processed_data={
                                    'confidence_score': analysis_result.confidence_score or 0.5,
                                    'source_links': {'primary_source': combined_source},
                                    'work_type_confidence': getattr(analysis_result, 'work_type_confidence', None),
                                    'classification_source': getattr(analysis_result, 'classification_source', None)
                                },
                                confidence_score=analysis_result.confidence_score or 0.5
                            )
                            
                            await work_repo.create_work(work_cache)
                            
                        except Exception as cache_error:
                            logger.warning(f"Failed to cache API result: {cache_error}")
                            logger.error(f"Cache error details: {str(cache_error)}")
                    
                    except Exception as analysis_error:
                        logger.error(f"Failed to analyze work from API: {analysis_error}")
                        # Create a basic result without full copyright analysis
                        try:
                            source_urls = merged_work.get('source_urls', [])
                            combined_source = ", ".join(source_urls) if source_urls else merged_work.get('url', '')
                            
                            # Extract year from raw data if available
                            pub_year = merged_work.get('publication_year')
                            
                            results.append(SearchResultItem(
                                title=merged_work.get("title", ""),
                                author_name=merged_work.get("author", "Unknown"),
                                publication_year=pub_year,
                                work_type="musical" if merged_work.get('api_source') == 'musicbrainz' else "literary",
                                status="Unknown",
                                enters_public_domain=None,
                                confidence_score=0.3,  # Lower confidence for failed analysis
                                source=combined_source,
                                work_type_confidence=None,
                                classification_source=None
                            ))
                        except Exception as fallback_error:
                            logger.error(f"Fallback result creation failed: {fallback_error}")
                            continue
                
                if results:
                    source = "mixed" if any(r.source.startswith("cache") for r in results) else "api"
                
            except Exception as api_error:
                logger.warning(f"External API search failed: {api_error}")
                if not results:
                    raise SearchError("Search service temporarily unavailable")
        
        # Prepare response
        response = SearchResponse(
            query={
                "author": search_data.get("author"),
                "title": search_data.get("title"),
                "work_type": search_data.get("work_type"),
                "limit": search_data.get("limit")
            },
            results=results[:effective_limit],
            total_found=len(results),
            source=source,
            searched_at=datetime.utcnow().isoformat()
        )
        
        # Save to user history if authenticated
        if current_user and search_data.get("user_id"):
            try:
                from ...repositories.work_repository import SearchHistoryRepository
                history_repo = SearchHistoryRepository()
                
                query_parts = []
                if search_data.get("author"):
                    query_parts.append(f"author: {search_data['author']}")
                if search_data.get("title"):
                    query_parts.append(f"title: {search_data['title']}")
                if search_data.get("work_type"):
                    query_parts.append(f"type: {search_data['work_type']}")
                
                query_text = ", ".join(query_parts)
                
                results_for_history = [
                    {
                        "title": result.title,
                        "author_name": result.author_name,
                        "publication_year": result.publication_year,
                        "work_type": result.work_type,
                        "status": result.status,
                        "enters_public_domain": result.enters_public_domain,
                        "confidence_score": result.confidence_score,
                        "source": result.source
                    }
                    for result in results[:effective_limit]
                ]
                
                await history_repo.create_search_history(
                    user_id=search_data["user_id"],
                    query_text=query_text,
                    filters={
                        'author': search_data.get("author"),
                        'title': search_data.get("title"),
                        'work_type': search_data.get("work_type"),
                        'country': search_data.get("country")
                    },
                    results=results_for_history
                )
                
            except Exception as history_error:
                logger.warning(f"Failed to save search to user history: {history_error}")
        
        return response
        
    except ValidationError:
        raise
    except SearchError:
        raise
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise SearchError(f"Search failed due to internal error: {str(e)}")

async def get_popular_works_internal(
    limit: int = 6,
    work_type: Optional[str] = None,
    country: Optional[str] = None
) -> SearchResponse:
    """
    Internal function to get popular works
    """
    try:
        works = await work_repo.get_popular_works(
            limit=limit,
            work_type=work_type
        )
        
        results = []
        for work in works:
            results.append(SearchResultItem(
                title=work.title,
                author_name=work.author or "Unknown",
                publication_year=work.publication_year,
                work_type=work.work_type,
                status=work.copyright_status or "Unknown",
                enters_public_domain=work.effective_public_domain_year,
                confidence_score=work.processed_data.get('confidence_score', 0.8) if work.processed_data else 0.8,
                source=f"https://catalog.loc.gov/search?q={work.title.replace(' ', '+')}"
            ))
        
        return SearchResponse(
            query={
                "author": None,
                "title": None,
                "work_type": work_type,
                "limit": limit
            },
            results=results,
            total_found=len(results),
            source="database",
            searched_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to get popular works: {e}")
        raise SearchError("Failed to retrieve popular works")