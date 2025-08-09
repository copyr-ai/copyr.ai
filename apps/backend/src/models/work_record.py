from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Literal
from datetime import datetime

@dataclass
class WorkRecord:
    """Normalized record for a literary or musical work with copyright analysis"""
    
    # Basic metadata
    title: str
    author_name: str
    publication_year: Optional[int] = None
    published: bool = True
    country: str = "US"
    year_of_death: Optional[int] = None
    work_type: Optional[str] = None  # Can be "literary", "musical", or None if uncertain
    
    # Copyright analysis
    status: Literal["Public Domain", "Under Copyright", "Unknown"] = "Unknown"
    enters_public_domain: Optional[int] = None
    
    # Source tracking
    source_links: Dict[str, str] = field(default_factory=dict)
    notes: str = ""
    
    # Metadata
    queried_at: datetime = field(default_factory=datetime.utcnow)
    confidence_score: float = 0.0  # 0-1 score for data reliability
    work_type_confidence: Optional[float] = None  # Confidence in work_type classification
    classification_source: Optional[str] = None   # Source of classification
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "title": self.title,
            "author_name": self.author_name,
            "publication_year": self.publication_year,
            "published": self.published,
            "country": self.country,
            "year_of_death": self.year_of_death,
            "work_type": self.work_type,
            "status": self.status,
            "enters_public_domain": self.enters_public_domain,
            "source_links": self.source_links,
            "notes": self.notes,
            "queried_at": self.queried_at.isoformat(),
            "confidence_score": self.confidence_score,
            "work_type_confidence": self.work_type_confidence,
            "classification_source": self.classification_source
        }

@dataclass 
class APIResponse:
    """Standardized response from API clients"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    source_url: Optional[str] = None
    confidence: float = 0.0