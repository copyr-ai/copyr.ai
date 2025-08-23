from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class CacheStatus(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    EXPIRED = "expired"

class WorkCache(BaseModel):
    id: Optional[str] = None
    title: str
    author: Optional[str] = None
    publication_year: Optional[int] = None
    
    # New normalized fields for better search and deduplication
    title_normalized: Optional[str] = None
    author_normalized: Optional[str] = None
    content_hash: Optional[str] = None
    
    work_type: str  # literary, musical, etc.
    work_subtype: Optional[str] = None  # novel, poem, song, symphony, etc.
    copyright_status: Optional[str] = None
    
    # Fixed: Changed from public_domain_date (TEXT) to public_domain_year (INTEGER)
    public_domain_date: Optional[str] = None  # Keep for backward compatibility
    public_domain_year: Optional[int] = None  # New proper field
    
    source_api: str  # hathitrust, loc, musicbrainz
    source_id: str  # unique identifier from source
    raw_data: Dict[str, Any]  # original API response
    processed_data: Dict[str, Any]  # normalized data
    
    # New confidence scoring
    confidence_score: float = Field(default=0.80, ge=0.0, le=1.0)
    
    cache_status: CacheStatus = CacheStatus.FRESH
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    class Config:
        # Allow population by field name for backward compatibility (Pydantic v2)
        populate_by_name = True
    
    @property
    def effective_public_domain_year(self) -> Optional[int]:
        """Get public domain year, preferring the new field over legacy field"""
        if self.public_domain_year is not None:
            return self.public_domain_year
        
        # Try to parse legacy field
        if self.public_domain_date and self.public_domain_date.isdigit():
            return int(self.public_domain_date)
        
        return None

class CacheSearchQuery(BaseModel):
    query_hash: str
    query_text: str
    work_type: str
    results: list[str]  # list of work_cache IDs
    total_results: int
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None