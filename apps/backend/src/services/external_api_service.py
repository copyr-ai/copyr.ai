import asyncio
import aiohttp
from typing import Optional, List, Dict, Any, Tuple
import logging
from ..core.exceptions import ExternalServiceError
from ..countries.us.api_clients.library_of_congress import LibraryOfCongressClient
# from ..countries.us.api_clients.hathitrust import HathiTrustClient  # Removed
from ..countries.us.api_clients.musicbrainz import MusicBrainzClient

logger = logging.getLogger(__name__)

class ExternalAPIService:
    """
    Service layer for external API integrations with connection pooling and async operations
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        # Initialize API clients (they will use our shared session)
        self.loc_client = LibraryOfCongressClient()
        # self.hathi_client = HathiTrustClient()  # Removed
        self.musicbrainz_client = MusicBrainzClient()
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_session()
    
    async def start_session(self):
        """Start the HTTP session with connection pooling"""
        if not self.session or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,  # Total connection limit
                limit_per_host=30,  # Per-host connection limit
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout,
                headers={
                    'User-Agent': 'copyr.ai/1.0 (Copyright Analysis Service)'
                }
            )
    
    async def close_session(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def search_all_sources(
        self, 
        title: Optional[str] = None, 
        author: Optional[str] = None,
        work_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search all external sources concurrently
        """
        await self.start_session()
        
        try:
            # Create search tasks for concurrent execution
            tasks = []
            
            # Library of Congress search
            if title or author:
                tasks.append(self._search_library_of_congress(title, author, limit))
            
            # MusicBrainz search (for musical works)
            if work_type == "musical" or not work_type:
                if title or author:
                    tasks.append(self._search_musicbrainz(title, author, limit))
            
            # HathiTrust search removed - using only LOC and MusicBrainz
            
            # Execute all searches concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results from all sources
            all_works = []
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"External API search failed: {result}")
                    continue
                
                if isinstance(result, list):
                    all_works.extend(result)
            
            return all_works
            
        except Exception as e:
            logger.error(f"Error in search_all_sources: {e}")
            raise ExternalServiceError("search", str(e), e)
    
    async def _search_library_of_congress(
        self, 
        title: Optional[str], 
        author: Optional[str], 
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Search Library of Congress with proper error handling
        """
        try:
            if author and title:
                works = await self.loc_client.search_by_title_and_author(title, author, limit=limit * 2, session=self.session)
            elif author:
                works = await self.loc_client.search_by_author(author, limit=limit * 2, session=self.session)
            elif title:
                works = await self.loc_client.search_by_title(title, limit=limit * 2, session=self.session)
            else:
                return []
            
            # Add source indicator
            for work in works:
                work['api_source'] = 'library_of_congress'
                work['source_priority'] = 1  # High priority for LOC
            
            return works[:limit]
            
        except Exception as e:
            logger.warning(f"Library of Congress search failed: {e}")
            raise ExternalServiceError("Library of Congress", str(e), e)
    
    async def _search_musicbrainz(
        self, 
        title: Optional[str], 
        author: Optional[str], 
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Search MusicBrainz with proper error handling
        """
        try:
            works = []
            
            if author and title:
                logger.info("Searching MusicBrainz with both title and author")
                mb_response = await self.musicbrainz_client.search_works(title, author, session=self.session)
            elif author:
                logger.info("Searching MusicBrainz by composer only")
                # First search for the artist
                artist_response = await self.musicbrainz_client.search_artists(author, session=self.session)
                if artist_response.success and artist_response.data:
                    best_artist = artist_response.data.get('best_match')
                    if best_artist:
                        mb_response = await self.musicbrainz_client.search_works("", author, session=self.session)
                    else:
                        return []
                else:
                    return []
            elif title:
                logger.info("Searching MusicBrainz by title only")
                mb_response = await self.musicbrainz_client.search_works(title, "", session=self.session)
            else:
                return []
            
            if mb_response and mb_response.success and mb_response.data:
                mb_works = mb_response.data.get('works', [])
                
                for work in mb_works:
                    composer_names = [c.get('name', '') for c in work.get('composers', [])]
                    composer_str = ', '.join(composer_names) if composer_names else 'Unknown'
                    
                    # Use earliest release year if available
                    publication_year = work.get('earliest_release_year')
                    
                    formatted_work = {
                        'title': work.get('title', ''),
                        'author': composer_str,
                        'publication_year': publication_year,
                        'url': work.get('url', ''),
                        'format': 'music',
                        'source': 'musicbrainz',
                        'api_source': 'musicbrainz',
                        'source_priority': 2  # Medium priority for MusicBrainz
                    }
                    works.append(formatted_work)
            
            return works[:limit]
            
        except Exception as e:
            logger.warning(f"MusicBrainz search failed: {e}")
            raise ExternalServiceError("MusicBrainz", str(e), e)
    
    # HathiTrust search method removed
    
    def group_similar_works(self, works: List[Dict[str, Any]]) -> Dict[Tuple[str, str], List[Dict[str, Any]]]:
        """
        Group similar works by normalized title and author
        """
        import re
        work_groups = {}
        
        for work in works:
            # Create normalized key for grouping
            title_norm = work.get("title", "").lower().strip()
            author_norm = work.get("author", "").lower().strip()
            
            # Clean title and author for better grouping
            title_clean = re.sub(r'[^\w\s]', '', title_norm)
            title_clean = re.sub(r'\s+', ' ', title_clean).strip()
            author_clean = re.sub(r'[^\w\s]', '', author_norm)
            author_clean = re.sub(r'\s+', ' ', author_clean).strip()
            
            group_key = (title_clean, author_clean)
            
            if group_key not in work_groups:
                work_groups[group_key] = []
            work_groups[group_key].append(work)
        
        return work_groups
    
    def merge_work_sources(self, work_group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple works from different sources into a single result
        """
        if not work_group:
            return {}
        
        # Sort by source priority (lower number = higher priority)
        work_group.sort(key=lambda w: w.get('source_priority', 999))
        
        # Use highest priority work as base
        base_work = work_group[0]
        
        # Collect all source URLs
        source_urls = []
        for work in work_group:
            url = work.get("url", "")
            if url and url not in source_urls:
                source_urls.append(url)
        
        # Create merged result
        merged_work = {
            **base_work,
            'source_urls': source_urls,
            'source_count': len(work_group),
            'all_sources': [w.get('api_source') for w in work_group]
        }
        
        return merged_work

# Global service instance
external_api_service = ExternalAPIService()