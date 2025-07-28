from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from ..models.work_record import APIResponse

class BaseAPIClient(ABC):
    """
    Abstract base class for all API clients across different countries
    """
    
    def __init__(self, rate_limit_delay: float = 1.0):
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
    
    @abstractmethod
    def search_books(self, title: str, author: str) -> APIResponse:
        """
        Search for books/literary works
        
        Args:
            title: Work title
            author: Author name
            
        Returns:
            APIResponse with search results
        """
        pass
    
    @abstractmethod
    def get_item_details(self, item_identifier: str) -> APIResponse:
        """
        Get detailed information about a specific item
        
        Args:
            item_identifier: Unique identifier for the item
            
        Returns:
            APIResponse with detailed item information
        """
        pass
    
    def _rate_limit(self):
        """Enforce rate limiting - to be implemented by subclasses"""
        import time
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

class BaseMusicAPIClient(BaseAPIClient):
    """
    Abstract base class for music-specific API clients
    """
    
    @abstractmethod
    def search_works(self, title: str, composer: str) -> APIResponse:
        """
        Search for musical works
        
        Args:
            title: Work title
            composer: Composer name
            
        Returns:
            APIResponse with search results
        """
        pass
    
    @abstractmethod
    def search_artists(self, artist_name: str) -> APIResponse:
        """
        Search for artist information (birth/death dates, etc.)
        
        Args:
            artist_name: Name of the artist/composer
            
        Returns:
            APIResponse with artist information
        """
        pass

class BaseDigitalLibraryClient(BaseAPIClient):
    """
    Abstract base class for digital library clients (like HathiTrust)
    """
    
    @abstractmethod
    def get_volume_brief_by_identifier(self, identifier_type: str, identifier: str) -> APIResponse:
        """
        Get brief volume information by identifier
        
        Args:
            identifier_type: Type of identifier (oclc, isbn, etc.)
            identifier: The identifier value
            
        Returns:
            APIResponse with volume information
        """
        pass
    
    @abstractmethod
    def extract_identifier_from_metadata(self, metadata: Dict[str, Any]) -> Optional[str]:
        """
        Extract relevant identifier from external metadata
        
        Args:
            metadata: Metadata from another source
            
        Returns:
            Identifier string if found, None otherwise
        """
        pass