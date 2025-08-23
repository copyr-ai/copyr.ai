from fastapi import APIRouter, Query, Depends
from typing import Optional, List, Dict, Any
from ...repositories.work_repository import WorkRepository
from ...core.exceptions import ValidationError
from ...core.security import InputSanitizer
from ...auth.middleware import optional_auth, rate_limit_check
from ...core.logging_config import get_logger, log_performance
from ...copyright_analyzer import CopyrightAnalyzer

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["works"])

work_repo = WorkRepository()

@router.get("/popular-works")
@log_performance("get_popular_works")
async def get_popular_works(
    limit: int = Query(default=6, ge=1, le=50),
    work_type: Optional[str] = Query(default=None),
    country: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    current_user: Optional[dict] = Depends(optional_auth)
):
    """
    Get popular/recently analyzed works from the database with filtering support
    """
    try:
        # Validate inputs
        limit = InputSanitizer.validate_limit(limit, max_limit=50)
        
        if work_type:
            work_type = InputSanitizer.validate_work_type(work_type)
        
        if country:
            country = InputSanitizer.validate_country_code(country)
        
        if status:
            status = InputSanitizer.sanitize_string(status, max_length=100)
        
        # Get works from repository
        works = await work_repo.get_popular_works(
            limit=limit,
            work_type=work_type,
            copyright_status=status
        )
        
        # Format works for frontend display
        formatted_works = []
        
        for work in works:
            # Create slug from title
            slug = work.title.lower().replace(' ', '-').replace("'", "").replace('"', '')
            import re
            slug = re.sub(r'[^a-z0-9\-]', '', slug)[:50]
            
            # Map work_type to category for frontend
            category = "Music" if work.work_type == "musical" else "Literature"
            
            # Get actual public domain date using improved method
            enters_pd = work.effective_public_domain_year
            
            # Get source URL from processed data or generate fallback
            source_url = ""
            if work.processed_data and work.processed_data.get('source_links'):
                source_links = work.processed_data['source_links']
                if isinstance(source_links, dict):
                    source_url = source_links.get('primary_source', '')
                elif isinstance(source_links, str):
                    source_url = source_links
            
            if not source_url:
                source_url = f"https://catalog.loc.gov/search?q={work.title.replace(' ', '+')}"
            
            formatted_work = {
                "id": work.id or "",
                "slug": slug,
                "title": work.title,
                "author_name": work.author or "Unknown",
                "publication_year": work.publication_year,
                "published": True,
                "country": country or "US",
                "work_type": work.work_type,
                "status": work.copyright_status or "Unknown",
                "enters_public_domain": enters_pd,
                "source": source_url,
                "notes": f"Work from {work.source_api}",
                "confidence_score": work.processed_data.get('confidence_score', 0.8) if work.processed_data else 0.8,
                "queried_at": work.created_at.isoformat() if work.created_at else None,
                "category": category
            }
            formatted_works.append(formatted_work)
        
        return {
            "works": formatted_works,
            "total": len(formatted_works)
        }
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Failed to get popular works: {e}")
        return {"works": [], "total": 0}

@router.get("/countries")
async def get_supported_countries():
    """
    Get list of supported countries for copyright analysis
    """
    try:
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
    except Exception as e:
        logger.error(f"Failed to get supported countries: {e}")
        return {
            "supported_countries": [],
            "total_count": 0
        }

@router.get("/copyright-info/{country_code}")
async def get_copyright_info(country_code: str = "US"):
    """
    Get information about copyright law rules for a specific country
    """
    try:
        country_code = InputSanitizer.validate_country_code(country_code)
        analyzer = CopyrightAnalyzer(country_code)
        return analyzer.get_copyright_info()
    except ValidationError:
        raise
    except ValueError as e:
        raise ValidationError(str(e))
    except Exception as e:
        logger.error(f"Failed to get copyright info for {country_code}: {e}")
        raise ValidationError("Failed to retrieve copyright information")

@router.get("/copyright-info")
async def get_default_copyright_info():
    """
    Get information about US copyright law rules (default)
    """
    return await get_copyright_info("US")

@router.get("/autocomplete")
@log_performance("get_autocomplete")
async def get_autocomplete_suggestions(
    q: str = Query(default="", min_length=2),
    limit: int = Query(default=10, ge=1, le=20)
):
    """
    Get autocomplete suggestions from database for titles, authors, and categories
    """
    try:
        # Validate and sanitize query
        if len(q.strip()) < 2:
            return {"sections": []}
        
        query = InputSanitizer.sanitize_string(q, max_length=100)
        limit = InputSanitizer.validate_limit(limit, max_limit=20)
        
        # Search for matching works in database
        works = await work_repo.search_by_content(
            title=query,
            author=query,
            limit=50  # Get more works to extract suggestions
        )
        
        # Extract suggestions
        matching_titles = set()
        matching_authors = set()
        categories = set()
        
        query_lower = query.lower()
        
        for work in works:
            # Check titles
            if work.title and query_lower in work.title.lower():
                matching_titles.add(work.title.strip())
            
            # Check authors
            if work.author and query_lower in work.author.lower():
                matching_authors.add(work.author.strip())
            
            # Add available categories
            if work.work_type == 'literary':
                categories.add('Literature')
            elif work.work_type == 'musical':
                categories.add('Music')
        
        # Convert to sorted lists and limit
        title_list = sorted(list(matching_titles))[:limit]
        author_list = sorted(list(matching_authors))[:limit]
        category_list = sorted(list(categories))
        
        # Build response sections
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
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Failed to get autocomplete suggestions: {e}")
        return {"sections": []}