from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
# Database imports moved to avoid circular dependency issues
from ..database.models import WorkCache
from ..core.exceptions import DatabaseError, NotFoundError
from ..core.security import SQLInjectionProtector

logger = logging.getLogger(__name__)

class WorkRepository:
    """
    Repository pattern for work-related database operations
    """
    
    def __init__(self):
        self.table_name = "work_cache"
        self.default_cache_duration = timedelta(days=7)
    
    async def find_by_id(self, work_id: str) -> Optional[WorkCache]:
        """
        Find work by ID
        """
        try:
            from ..database.config import supabase
            response = supabase.table(self.table_name).select("*").eq("id", work_id).execute()
            
            if response.data:
                return WorkCache(**response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error finding work by ID {work_id}: {e}")
            raise DatabaseError("find_by_id", str(e), e)
    
    async def find_by_source_key(self, source_key: str) -> Optional[WorkCache]:
        """
        Find work by source key (source_api:source_id)
        """
        try:
            from ..database.config import supabase
            response = supabase.table(self.table_name).select("*").eq("source_key", source_key).execute()
            
            if response.data:
                work_data = response.data[0]
                # Check if cache is still valid
                expires_at = datetime.fromisoformat(work_data["expires_at"].replace("Z", "+00:00"))
                if expires_at > datetime.utcnow():
                    return WorkCache(**work_data)
                else:
                    # Cache expired, mark as stale
                    await self.update_cache_status(work_data["id"], "expired")
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding work by source key {source_key}: {e}")
            raise DatabaseError("find_by_source_key", str(e), e)
    
    async def search_by_content(
        self, 
        title: Optional[str] = None, 
        author: Optional[str] = None,
        work_type: Optional[str] = None,
        limit: int = 10
    ) -> List[WorkCache]:
        """
        Search works by content with fuzzy matching
        For autocomplete, search title OR author (not AND)
        """
        try:
            from ..database.config import supabase
            
            # If both title and author are provided (autocomplete case), 
            # we want to search for works that match EITHER title OR author
            if title and author and title.strip() == author.strip():
                # This is an autocomplete search - search for query in either title or author
                search_term = title.strip()
                safe_term = SQLInjectionProtector.sanitize_for_sql(search_term)
                
                # Use OR condition to search both title and author
                query = supabase.table(self.table_name).select("*").or_(
                    f"title.ilike.%{safe_term}%,author.ilike.%{safe_term}%"
                )
            else:
                # Regular search - apply filters as AND conditions
                query = supabase.table(self.table_name).select("*")
                
                if title:
                    safe_title = SQLInjectionProtector.sanitize_for_sql(title.strip())
                    query = query.ilike("title", f"%{safe_title}%")
                
                if author:
                    safe_author = SQLInjectionProtector.sanitize_for_sql(author.strip())
                    query = query.ilike("author", f"%{safe_author}%")
            
            if work_type and work_type in ['literary', 'musical']:
                query = query.eq("work_type", work_type)
            
            # Order by most recent and limit results
            response = query.order("created_at", desc=True).limit(limit).execute()
            
            works = []
            if response.data:
                for work_data in response.data:
                    works.append(WorkCache(**work_data))
            
            return works
            
        except Exception as e:
            logger.error(f"Error searching works by content: {e}")
            raise DatabaseError("search_by_content", str(e), e)
    
    async def get_popular_works(
        self, 
        limit: int = 10, 
        work_type: Optional[str] = None,
        copyright_status: Optional[str] = None
    ) -> List[WorkCache]:
        """
        Get popular/recently cached works with filtering
        """
        try:
            from ..database.config import supabase
            query = supabase.table(self.table_name).select("*")
            
            # Apply filters
            if work_type and work_type in ['literary', 'musical']:
                query = query.eq("work_type", work_type)
            
            if copyright_status:
                query = query.eq("copyright_status", copyright_status)
            
            # Get more works than needed to filter for unique titles
            response = query.order("created_at", desc=True).limit(limit * 3).execute()
            
            # Remove duplicates by title
            seen_titles = set()
            unique_works = []
            
            if response.data:
                for work_data in response.data:
                    title_normalized = work_data.get('title', '').lower().strip()
                    if title_normalized not in seen_titles and len(unique_works) < limit:
                        seen_titles.add(title_normalized)
                        unique_works.append(WorkCache(**work_data))
            
            return unique_works
            
        except Exception as e:
            logger.error(f"Error getting popular works: {e}")
            raise DatabaseError("get_popular_works", str(e), e)
    
    async def create_work(self, work: WorkCache) -> WorkCache:
        """
        Create new work cache entry
        """
        try:
            # Set timestamps
            now = datetime.utcnow()
            expires_at = now + self.default_cache_duration
            
            work_data = {
                "source_key": f"{work.source_api}:{work.source_id}",
                "title": work.title,
                "author": work.author,
                "publication_year": work.publication_year,
                "work_type": work.work_type,
                "copyright_status": work.copyright_status,
                "public_domain_date": work.public_domain_date,
                "source_api": work.source_api,
                "source_id": work.source_id,
                "raw_data": work.raw_data,
                "processed_data": work.processed_data,
                "cache_status": work.cache_status,
                "expires_at": expires_at.isoformat()
            }
            
            from ..database.config import supabase
            from ..database.config import supabase
            response = supabase.table(self.table_name).insert(work_data).execute()
            
            if response.data:
                return WorkCache(**response.data[0])
            else:
                raise DatabaseError("create_work", "No data returned from insert")
                
        except Exception as e:
            logger.error(f"Error creating work: {e}")
            raise DatabaseError("create_work", str(e), e)
    
    async def update_work(self, work_id: str, updates: Dict[str, Any]) -> WorkCache:
        """
        Update existing work cache entry
        """
        try:
            # Add updated_at timestamp
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            from ..database.config import supabase
            from ..database.config import supabase
            response = supabase.table(self.table_name).update(updates).eq("id", work_id).execute()
            
            if response.data:
                return WorkCache(**response.data[0])
            else:
                raise NotFoundError("work", work_id)
                
        except Exception as e:
            logger.error(f"Error updating work {work_id}: {e}")
            raise DatabaseError("update_work", str(e), e)
    
    async def update_cache_status(self, work_id: str, status: str) -> bool:
        """
        Update cache status for a work
        """
        try:
            from ..database.config import supabase
            from ..database.config import supabase
            response = supabase.table(self.table_name).update({
                "cache_status": status,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", work_id).execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Error updating cache status for work {work_id}: {e}")
            raise DatabaseError("update_cache_status", str(e), e)
    
    async def delete_expired_works(self, days_past_expiration: int = 30) -> int:
        """
        Delete works that have been expired for more than specified days
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_past_expiration)
            
            from ..database.config import supabase
            from ..database.config import supabase
            response = supabase.table(self.table_name).delete().lt(
                "expires_at", cutoff_date.isoformat()
            ).execute()
            
            return len(response.data) if response.data else 0
            
        except Exception as e:
            logger.error(f"Error deleting expired works: {e}")
            raise DatabaseError("delete_expired_works", str(e), e)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get repository statistics
        """
        try:
            from ..database.config import supabase
            
            # Total works
            total_response = supabase.table(self.table_name).select("id", count="exact").execute()
            total_works = total_response.count if total_response.count else 0
            
            # Works by type
            literary_response = supabase.table(self.table_name).select(
                "id", count="exact"
            ).eq("work_type", "literary").execute()
            literary_count = literary_response.count if literary_response.count else 0
            
            musical_response = supabase.table(self.table_name).select(
                "id", count="exact"
            ).eq("work_type", "musical").execute()
            musical_count = musical_response.count if musical_response.count else 0
            
            # Fresh vs expired cache
            fresh_response = supabase.table(self.table_name).select(
                "id", count="exact"
            ).eq("cache_status", "fresh").execute()
            fresh_count = fresh_response.count if fresh_response.count else 0
            
            return {
                "total_works": total_works,
                "literary_works": literary_count,
                "musical_works": musical_count,
                "fresh_cache": fresh_count,
                "cache_hit_ratio": (fresh_count / total_works * 100) if total_works > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting repository statistics: {e}")
            return {
                "total_works": 0,
                "literary_works": 0,
                "musical_works": 0,
                "fresh_cache": 0,
                "cache_hit_ratio": 0
            }

class SearchHistoryRepository:
    """
    Repository for user search history operations
    """
    
    def __init__(self):
        self.table_name = "user_search_history"
    
    async def create_search_history(
        self, 
        user_id: str, 
        query_text: str, 
        filters: Dict[str, Any],
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create new search history entry
        """
        try:
            search_data = {
                'user_id': user_id,
                'query_text': query_text,
                'filters': filters,
                'results': results,
                'result_count': len(results)
            }
            
            from ..database.config import supabase_admin
            response = supabase_admin.table(self.table_name).insert(search_data).execute()
            
            if response.data:
                return response.data[0]
            else:
                raise DatabaseError("create_search_history", "No data returned from insert")
                
        except Exception as e:
            logger.error(f"Error creating search history: {e}")
            raise DatabaseError("create_search_history", str(e), e)
    
    async def get_user_search_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get search history for a user
        """
        try:
            from ..database.config import supabase
            from ..database.config import supabase
            response = supabase.table(self.table_name).select('*').eq(
                'user_id', user_id
            ).order('searched_at', desc=True).limit(limit).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting search history for user {user_id}: {e}")
            raise DatabaseError("get_user_search_history", str(e), e)
    
    async def delete_search_history_item(self, user_id: str, search_id: str) -> bool:
        """
        Delete specific search history item
        """
        try:
            from ..database.config import supabase
            from ..database.config import supabase
            response = supabase.table(self.table_name).delete().eq(
                'id', search_id
            ).eq('user_id', user_id).execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Error deleting search history item {search_id}: {e}")
            raise DatabaseError("delete_search_history_item", str(e), e)
    
    async def clear_user_search_history(self, user_id: str) -> int:
        """
        Clear all search history for a user
        """
        try:
            from ..database.config import supabase
            from ..database.config import supabase
            response = supabase.table(self.table_name).delete().eq('user_id', user_id).execute()
            
            return len(response.data) if response.data else 0
            
        except Exception as e:
            logger.error(f"Error clearing search history for user {user_id}: {e}")
            raise DatabaseError("clear_user_search_history", str(e), e)

class UserRepository:
    """
    Repository for user profile operations
    """
    
    def __init__(self):
        self.table_name = "user_profiles"
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile by ID
        """
        try:
            from ..database.config import supabase_admin
            response = supabase_admin.table(self.table_name).select('*').eq('id', user_id).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting user profile {user_id}: {e}")
            raise DatabaseError("get_user_profile", str(e), e)
    
    async def create_user_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new user profile
        """
        try:
            from ..database.config import supabase_admin
            response = supabase_admin.table(self.table_name).insert(profile_data).execute()
            
            if response.data:
                return response.data[0]
            else:
                raise DatabaseError("create_user_profile", "No data returned from insert")
                
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            raise DatabaseError("create_user_profile", str(e), e)
    
    async def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user profile
        """
        try:
            from ..database.config import supabase_admin
            response = supabase_admin.table(self.table_name).update(updates).eq('id', user_id).execute()
            
            if response.data:
                return response.data[0]
            else:
                raise NotFoundError("user_profile", user_id)
                
        except Exception as e:
            logger.error(f"Error updating user profile {user_id}: {e}")
            raise DatabaseError("update_user_profile", str(e), e)