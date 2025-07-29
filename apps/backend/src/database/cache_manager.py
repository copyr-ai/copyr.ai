import hashlib
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from .config import supabase
from .models import WorkCache, CacheSearchQuery, CacheStatus

class CacheManager:
    def __init__(self):
        self.default_cache_duration = timedelta(days=7)  # Cache for 1 week
        self.search_cache_duration = timedelta(hours=24)  # Search results cache for 24 hours
    
    def _generate_query_hash(self, query: str, work_type: str) -> str:
        """Generate a hash for search queries to use as cache key"""
        combined = f"{query.lower().strip()}:{work_type.lower()}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _normalize_work_identifier(self, title: str, author: str) -> str:
        """Create normalized identifier for works to prevent duplicates"""
        # Normalize title and author to lowercase, remove extra spaces and punctuation
        import re
        normalized_title = re.sub(r'[^\w\s]', '', title.lower().strip())
        normalized_title = re.sub(r'\s+', ' ', normalized_title).strip()
        
        normalized_author = re.sub(r'[^\w\s]', '', author.lower().strip())
        normalized_author = re.sub(r'\s+', ' ', normalized_author).strip()
        
        return f"{normalized_title}:{normalized_author}"
    
    def _generate_work_key(self, source_api: str, source_id: str) -> str:
        """Generate unique key for individual works"""
        return f"{source_api}:{source_id}"
    
    async def get_cached_work(self, source_api: str, source_id: str) -> Optional[WorkCache]:
        """Retrieve a cached work by source API and ID"""
        try:
            work_key = self._generate_work_key(source_api, source_id)
            response = supabase.table("work_cache").select("*").eq("source_key", work_key).execute()
            
            if response.data:
                work_data = response.data[0]
                # Check if cache is still valid
                expires_at = datetime.fromisoformat(work_data["expires_at"].replace("Z", "+00:00"))
                if expires_at > datetime.utcnow():
                    return WorkCache(**work_data)
                else:
                    # Mark as expired but don't delete (for background refresh)
                    await self._update_cache_status(work_data["id"], CacheStatus.EXPIRED)
            
            return None
        except Exception as e:
            print(f"Error retrieving cached work: {e}")
            return None
    
    async def cache_work(self, work: WorkCache, source_api: str, source_id: str) -> bool:
        """Cache a work result"""
        try:
            work_key = self._generate_work_key(source_api, source_id)
            expires_at = datetime.utcnow() + self.default_cache_duration
            
            work_data = {
                "source_key": work_key,
                "title": work.title,
                "author": work.author,
                "publication_year": work.publication_year,
                "work_type": work.work_type,
                "copyright_status": work.copyright_status,
                "public_domain_date": work.public_domain_date,
                "source_api": source_api,
                "source_id": source_id,
                "raw_data": work.raw_data,
                "processed_data": work.processed_data,
                "cache_status": CacheStatus.FRESH.value,
                "expires_at": expires_at.isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Upsert the work
            response = supabase.table("work_cache").upsert(work_data, on_conflict="source_key").execute()
            return len(response.data) > 0
            
        except Exception as e:
            print(f"Error caching work: {e}")
            return False
    
    async def get_cached_search(self, query: str, work_type: str) -> Optional[List[WorkCache]]:
        """Retrieve cached search results"""
        try:
            query_hash = self._generate_query_hash(query, work_type)
            
            # Get search query cache
            search_response = supabase.table("cache_search_queries").select("*").eq("query_hash", query_hash).execute()
            
            if not search_response.data:
                return None
            
            search_data = search_response.data[0]
            expires_at = datetime.fromisoformat(search_data["expires_at"].replace("Z", "+00:00"))
            
            if expires_at <= datetime.utcnow():
                return None  # Search cache expired
            
            # Get the actual works
            work_ids = search_data["results"]
            if not work_ids:
                return []
            
            works_response = supabase.table("work_cache").select("*").in_("id", work_ids).execute()
            
            works = []
            for work_data in works_response.data:
                works.append(WorkCache(**work_data))
            
            return works
            
        except Exception as e:
            print(f"Error retrieving cached search: {e}")
            return None
    
    async def cache_search_results(self, query: str, work_type: str, works: List[WorkCache]) -> bool:
        """Cache search results"""
        try:
            query_hash = self._generate_query_hash(query, work_type)
            expires_at = datetime.utcnow() + self.search_cache_duration
            
            # First, ensure all works are cached and get their IDs
            work_ids = []
            for work in works:
                cached = await self.cache_work(work, work.source_api, work.source_id)
                if cached:
                    # Get the work ID
                    work_key = self._generate_work_key(work.source_api, work.source_id)
                    response = supabase.table("work_cache").select("id").eq("source_key", work_key).execute()
                    if response.data:
                        work_ids.append(response.data[0]["id"])
            
            # Cache the search query
            search_data = {
                "query_hash": query_hash,
                "query_text": query,
                "work_type": work_type,
                "results": work_ids,
                "total_results": len(work_ids),
                "expires_at": expires_at.isoformat(),
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = supabase.table("cache_search_queries").upsert(search_data, on_conflict="query_hash").execute()
            return len(response.data) > 0
            
        except Exception as e:
            print(f"Error caching search results: {e}")
            return False
    
    async def _update_cache_status(self, work_id: str, status: CacheStatus) -> bool:
        """Update the cache status of a work"""
        try:
            response = supabase.table("work_cache").update({
                "cache_status": status.value,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", work_id).execute()
            
            return len(response.data) > 0
        except Exception as e:
            print(f"Error updating cache status: {e}")
            return False
    
    async def get_expired_works(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get works that need to be refreshed"""
        try:
            response = supabase.table("work_cache").select("*").eq("cache_status", CacheStatus.EXPIRED.value).limit(limit).execute()
            return response.data
        except Exception as e:
            print(f"Error getting expired works: {e}")
            return []
    
    async def cleanup_expired_cache(self, days_old: int = 30) -> int:
        """Remove very old expired cache entries"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            response = supabase.table("work_cache").delete().lt("expires_at", cutoff_date.isoformat()).execute()
            return len(response.data) if response.data else 0
            
        except Exception as e:
            print(f"Error cleaning up expired cache: {e}")
            return 0