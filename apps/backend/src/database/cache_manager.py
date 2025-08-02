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
    
    async def find_existing_work(self, work_title: str, work_author: str, publication_year: Optional[int] = None) -> Optional[Dict]:
        """
        Find existing work in cache by content similarity (not just source_key)
        Returns the existing work record if found
        """
        try:
            # Normalize search terms
            normalized_title = self._normalize_text(work_title)
            normalized_author = self._normalize_text(work_author) if work_author else ""
            
            # Search for existing works with similar title and author
            query = supabase.table("work_cache").select("*")
            
            # Add title search
            if normalized_title:
                query = query.ilike("title", f"%{normalized_title}%")
            
            # Add author search if provided
            if normalized_author:
                query = query.ilike("author", f"%{normalized_author}%")
            
            response = query.execute()
            
            if not response.data:
                return None
                
            # Find best match by similarity scoring
            best_match = None
            best_score = 0
            
            for existing_work in response.data:
                score = self._calculate_work_similarity(
                    work_title, work_author, publication_year,
                    existing_work.get("title", ""), 
                    existing_work.get("author", ""), 
                    existing_work.get("publication_year")
                )
                
                if score > best_score and score > 0.7:  # Minimum similarity threshold
                    best_score = score
                    best_match = existing_work
            
            return best_match
            
        except Exception as e:
            print(f"Error finding existing work: {e}")
            return None
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        import re
        # Remove punctuation, extra spaces, convert to lowercase
        normalized = re.sub(r'[^\w\s]', '', text.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized
    
    def _calculate_work_similarity(self, title1: str, author1: str, year1: Optional[int],
                                 title2: str, author2: str, year2: Optional[int]) -> float:
        """Calculate similarity score between two works (0.0 to 1.0)"""
        score = 0.0
        
        # Title similarity (60% weight)
        title1_norm = self._normalize_text(title1)
        title2_norm = self._normalize_text(title2)
        
        if title1_norm and title2_norm:
            if title1_norm == title2_norm:
                score += 0.6
            elif title1_norm in title2_norm or title2_norm in title1_norm:
                score += 0.4
            else:
                # Word overlap
                words1 = set(title1_norm.split())
                words2 = set(title2_norm.split())
                if words1 and words2:
                    overlap = len(words1 & words2) / len(words1 | words2)
                    score += 0.6 * overlap
        
        # Author similarity (30% weight)
        author1_norm = self._normalize_text(author1) if author1 else ""
        author2_norm = self._normalize_text(author2) if author2 else ""
        
        if author1_norm and author2_norm:
            if author1_norm == author2_norm:
                score += 0.3
            elif author1_norm in author2_norm or author2_norm in author1_norm:
                score += 0.2
        elif not author1_norm and not author2_norm:
            score += 0.15  # Both have no author info
        
        # Publication year similarity (10% weight)
        if year1 and year2:
            if year1 == year2:
                score += 0.1
            elif abs(year1 - year2) <= 2:  # Within 2 years
                score += 0.05
        elif not year1 and not year2:
            score += 0.05  # Both have no year info
        
        return min(score, 1.0)

    async def cache_work(self, work: WorkCache, source_api: str, source_id: str) -> bool:
        """
        Cache a work result with improved deduplication
        Checks for existing similar works before creating new entries
        """
        try:
            # First, check if this exact source already exists
            work_key = self._generate_work_key(source_api, source_id)
            existing_response = supabase.table("work_cache").select("*").eq("source_key", work_key).execute()
            
            if existing_response.data:
                # Update existing record
                existing_work = existing_response.data[0]
                expires_at = datetime.utcnow() + self.default_cache_duration
                
                updated_data = {
                    "title": work.title,
                    "author": work.author,
                    "publication_year": work.publication_year,
                    "work_type": work.work_type,
                    "copyright_status": work.copyright_status,
                    "public_domain_date": work.public_domain_date,
                    "raw_data": work.raw_data,
                    "processed_data": work.processed_data,
                    "cache_status": CacheStatus.FRESH.value,
                    "expires_at": expires_at.isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                response = supabase.table("work_cache").update(updated_data).eq("id", existing_work["id"]).execute()
                return len(response.data) > 0
            
            # Check for content-similar existing works
            similar_work = await self.find_existing_work(work.title, work.author, work.publication_year)
            
            if similar_work:
                # Merge information into existing work instead of creating duplicate
                expires_at = datetime.utcnow() + self.default_cache_duration
                
                # Merge source information
                existing_sources = similar_work.get("processed_data", {}).get("source_links", {})
                new_sources = work.processed_data.get("source_links", {})
                merged_sources = {**existing_sources, **new_sources}
                
                # Update with merged information
                merged_processed_data = {
                    **similar_work.get("processed_data", {}),
                    **work.processed_data,
                    "source_links": merged_sources,
                    "additional_sources": similar_work.get("processed_data", {}).get("additional_sources", []) + 
                                        [{"source_api": source_api, "source_id": source_id, "source_key": work_key}]
                }
                
                updated_data = {
                    "work_type": work.work_type,  # Update with most recent classification
                    "copyright_status": work.copyright_status,  # Update with most recent analysis
                    "public_domain_date": work.public_domain_date,
                    "processed_data": merged_processed_data,
                    "cache_status": CacheStatus.FRESH.value,
                    "expires_at": expires_at.isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                response = supabase.table("work_cache").update(updated_data).eq("id", similar_work["id"]).execute()
                return len(response.data) > 0
            
            # No similar work found, create new entry
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
            
            response = supabase.table("work_cache").insert(work_data).execute()
            return len(response.data) > 0
            
        except Exception as e:
            print(f"Error caching work: {e}")
            return False
    
    async def search_works_directly(self, title: Optional[str] = None, author: Optional[str] = None, 
                                   work_type: Optional[str] = None, limit: int = 5) -> List[WorkCache]:
        """
        Search work_cache table directly by content (not just cached query hashes)
        This ensures we find existing works even if the exact query was never cached
        """
        try:
            query = supabase.table("work_cache").select("*")
            
            # Add title search if provided
            if title:
                normalized_title = self._normalize_text(title)
                if normalized_title:
                    # Use PostgreSQL full-text search or ilike for partial matches
                    query = query.or_(f"title.ilike.%{title}%,title.ilike.%{normalized_title}%")
            
            # Add author search if provided  
            if author:
                normalized_author = self._normalize_text(author)
                if normalized_author:
                    query = query.or_(f"author.ilike.%{author}%,author.ilike.%{normalized_author}%")
            
            # Filter by work type if provided
            if work_type and work_type != "auto":
                query = query.eq("work_type", work_type)
            
            # Only get non-expired entries
            query = query.gte("expires_at", datetime.utcnow().isoformat())
            
            # Order by relevance (newer entries first) and limit
            query = query.order("updated_at", desc=True).limit(limit * 2)  # Get more for filtering
            
            response = query.execute()
            
            if not response.data:
                return []
            
            # Convert to WorkCache objects and apply intelligent filtering
            works = []
            for work_data in response.data:
                work = WorkCache(**work_data)
                
                # Apply similarity filtering for better relevance
                if title and author:
                    # Both provided - check similarity
                    similarity = self._calculate_work_similarity(
                        title, author, None,
                        work.title, work.author, work.publication_year
                    )
                    if similarity < 0.3:  # Lower threshold for direct search
                        continue
                elif title:
                    # Title only - check title relevance
                    if not self._is_title_relevant(title, work.title):
                        continue
                elif author:
                    # Author only - check author relevance  
                    if not self._is_author_relevant(author, work.author):
                        continue
                
                works.append(work)
                
                if len(works) >= limit:
                    break
            
            return works
            
        except Exception as e:
            print(f"Error in direct work search: {e}")
            return []
    
    def _is_title_relevant(self, search_title: str, work_title: str) -> bool:
        """Check if work title is relevant to search title"""
        if not search_title or not work_title:
            return False
            
        search_norm = self._normalize_text(search_title)
        work_norm = self._normalize_text(work_title)
        
        # Exact match
        if search_norm == work_norm:
            return True
            
        # Substring match
        if search_norm in work_norm or work_norm in search_norm:
            return True
            
        # Word overlap
        search_words = set(search_norm.split())
        work_words = set(work_norm.split())
        
        if search_words and work_words:
            overlap = len(search_words & work_words)
            return overlap >= min(2, len(search_words))  # At least 2 words or all search words
        
        return False
    
    def _is_author_relevant(self, search_author: str, work_author: str) -> bool:
        """Check if work author is relevant to search author"""
        if not search_author or not work_author:
            return False
            
        search_norm = self._normalize_text(search_author)
        work_norm = self._normalize_text(work_author)
        
        # Exact match
        if search_norm == work_norm:
            return True
            
        # Substring match (common for author names)
        if search_norm in work_norm or work_norm in search_norm:
            return True
            
        # Last name match (for cases like "Austen" matching "Austen, Jane")
        search_parts = search_norm.split()
        work_parts = work_norm.split()
        
        for search_part in search_parts:
            if len(search_part) > 2:  # Skip short words
                for work_part in work_parts:
                    if search_part in work_part or work_part in search_part:
                        return True
        
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
    
    def get_popular_works(self, limit: int = 6) -> List[WorkCache]:
        """
        Get any random 6 works from the database for homepage display
        """
        try:
            # Simply get any recent works from the database
            response = supabase.table("work_cache").select("*").order("created_at", desc=True).limit(limit).execute()
            print(f"Database query returned {len(response.data) if response.data else 0} records")
            
            # Convert to WorkCache objects
            works = []
            if response.data:
                for i, work_data in enumerate(response.data):
                    try:
                        work = self._dict_to_work_cache(work_data)
                        works.append(work)
                        print(f"Successfully converted work {i+1}: {work.title}")
                    except Exception as e:
                        print(f"Error converting work {i+1}: {e}")
                        print(f"Work data: {work_data}")
            
            print(f"Returning {len(works)} works")
            return works
            
        except Exception as e:
            print(f"Error getting popular works: {e}")
            import traceback
            traceback.print_exc()
            return []