from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from ...auth.middleware import require_auth
from ...core.exceptions import NotFoundError, ValidationError, AuthorizationError
from ...core.security import InputSanitizer
from ...repositories.work_repository import UserRepository, SearchHistoryRepository
from ...core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["users"])

# Initialize repositories
user_repo = UserRepository()
history_repo = SearchHistoryRepository()

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

@router.get("/user/{user_id}/profile")
async def get_user_profile(
    user_id: str,
    current_user: dict = Depends(require_auth)
):
    """
    Get user profile information
    """
    try:
        # Validate user ID format
        user_id = InputSanitizer.validate_user_id(user_id)
        
        # Check if user can access this profile (allow admin access)
        if current_user["user_id"] != user_id and current_user.get("role") != "admin":
            raise AuthorizationError("Access denied: insufficient permissions")
        
        profile = await user_repo.get_user_profile(user_id)
        
        if not profile:
            # Try to create profile from auth system
            try:
                from ...database.config import supabase_admin
                auth_user = supabase_admin.auth.admin.get_user_by_id(user_id)
                
                if auth_user.user:
                    profile_data = {
                        'id': user_id,
                        'email': auth_user.user.email,
                        'full_name': auth_user.user.user_metadata.get('full_name') or auth_user.user.user_metadata.get('name'),
                        'avatar_url': auth_user.user.user_metadata.get('avatar_url') or auth_user.user.user_metadata.get('picture')
                    }
                    
                    profile = await user_repo.create_user_profile(profile_data)
                else:
                    raise NotFoundError("user_profile", user_id)
                    
            except Exception as create_error:
                logger.error(f"Failed to create user profile: {create_error}")
                raise NotFoundError("user_profile", user_id)
        
        return profile
        
    except ValidationError:
        raise
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to get user profile {user_id}: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user profile: {str(e)}")

@router.post("/user/{user_id}/search-history")
async def save_search_history(
    user_id: str,
    search_data: SearchHistoryItem,
    current_user: dict = Depends(require_auth)
):
    """
    Save a search to user's history
    """
    try:
        # Validate user ID
        user_id = InputSanitizer.validate_user_id(user_id)
        
        # Check if user can access this resource (allow admin access)
        if current_user["user_id"] != user_id and current_user.get("role") != "admin":
            raise AuthorizationError("Access denied: insufficient permissions")
        
        # Validate and sanitize search data
        query_text = InputSanitizer.sanitize_string(search_data.query_text, max_length=500)
        
        if not query_text:
            raise ValidationError("Query text cannot be empty")
        
        search_id = await history_repo.create_search_history(
            user_id=user_id,
            query_text=query_text,
            filters=search_data.filters,
            results=search_data.results
        )
        
        return {
            "message": "Search saved to history successfully",
            "search_id": search_id.get('id') if isinstance(search_id, dict) else None
        }
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Failed to save search history for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save search to history")

@router.get("/user/{user_id}/search-history", response_model=List[SearchHistoryResponse])
async def get_user_search_history(
    user_id: str,
    limit: int = 20,
    current_user: dict = Depends(require_auth)
):
    """
    Get user's search history
    """
    try:
        # Validate inputs
        user_id = InputSanitizer.validate_user_id(user_id)
        limit = InputSanitizer.validate_limit(limit, max_limit=100)
        
        # Check if user can access this resource (allow admin access)
        if current_user["user_id"] != user_id and current_user.get("role") != "admin":
            raise AuthorizationError("Access denied: insufficient permissions")
        
        history_items = await history_repo.get_user_search_history(user_id, limit)
        
        # Convert to response format
        formatted_items = []
        for item in history_items:
            formatted_items.append({
                'id': item['id'],
                'query_text': item['query_text'],
                'filters': item['filters'] or {},
                'results': item['results'] or [],
                'result_count': item['result_count'],
                'searched_at': item['searched_at']
            })
        
        return formatted_items
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Failed to get search history for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve search history")

@router.delete("/user/{user_id}/search-history/{search_id}")
async def delete_search_history_item(
    user_id: str,
    search_id: str,
    current_user: dict = Depends(require_auth)
):
    """
    Delete a specific search from user's history
    """
    try:
        # Validate inputs
        user_id = InputSanitizer.validate_user_id(user_id)
        search_id = InputSanitizer.validate_user_id(search_id)  # Search IDs are also UUIDs
        
        # Check if user can access this resource (allow admin access)
        if current_user["user_id"] != user_id and current_user.get("role") != "admin":
            raise AuthorizationError("Access denied: insufficient permissions")
        
        success = await history_repo.delete_search_history_item(user_id, search_id)
        
        if not success:
            raise NotFoundError("search_history_item", search_id)
        
        return {"message": "Search history item deleted successfully"}
        
    except ValidationError:
        raise
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to delete search history item {search_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete search history item")

@router.delete("/user/{user_id}/search-history")
async def clear_user_search_history(
    user_id: str,
    current_user: dict = Depends(require_auth)
):
    """
    Clear all search history for a user
    """
    try:
        # Validate user ID
        user_id = InputSanitizer.validate_user_id(user_id)
        
        # Check if user can access this resource (allow admin access)
        if current_user["user_id"] != user_id and current_user.get("role") != "admin":
            raise AuthorizationError("Access denied: insufficient permissions")
        
        items_deleted = await history_repo.clear_user_search_history(user_id)
        
        return {
            "message": "Search history cleared successfully",
            "items_deleted": items_deleted
        }
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Failed to clear search history for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear search history")