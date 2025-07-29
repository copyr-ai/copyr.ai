from pydantic import BaseModel
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
    work_type: str  # book, music, etc.
    copyright_status: Optional[str] = None
    public_domain_date: Optional[str] = None
    source_api: str  # hathitrust, loc, musicbrainz
    source_id: str  # unique identifier from source
    raw_data: Dict[str, Any]  # original API response
    processed_data: Dict[str, Any]  # normalized data
    cache_status: CacheStatus = CacheStatus.FRESH
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

class CacheSearchQuery(BaseModel):
    query_hash: str
    query_text: str
    work_type: str
    results: list[str]  # list of work_cache IDs
    total_results: int
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None