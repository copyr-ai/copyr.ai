"""
US-specific configuration for copyright analysis
"""

from typing import Dict, Any, List

# US Copyright system information
COPYRIGHT_INFO = {
    "country": "United States",
    "country_code": "US",
    "laws_implemented": ["Title 17 USC §304", "Title 17 USC §305"],
    "rules": {
        "pre_1923": "Public Domain - all works published before 1923",
        "1923_1977": "95 years from publication (with renewal requirements)",
        "1978_plus_individual": "Life of author + 70 years",
        "1978_plus_work_for_hire": "95 years from publication or 120 years from creation (whichever is shorter)"
    },
    "note": "Calculations are specific to US copyright law and may not apply to other jurisdictions"
}

# API client configurations
API_CLIENTS_CONFIG = {
    "library_of_congress": {
        "name": "Library of Congress",
        "base_url": "https://www.loc.gov",
        "rate_limit_delay": 1.0,
        "confidence_weight": 0.4,
        "primary_use": "literary_works"
    },
    "hathitrust": {
        "name": "HathiTrust Digital Library",
        "base_url": "https://catalog.hathitrust.org/api",
        "rate_limit_delay": 1.0,
        "confidence_weight": 0.3,
        "primary_use": "rights_information"
    },
    "musicbrainz": {
        "name": "MusicBrainz",
        "base_url": "https://musicbrainz.org/ws/2",
        "rate_limit_delay": 1.1,  # MusicBrainz requires 1 req/sec minimum
        "confidence_weight": 0.3,
        "primary_use": "musical_works"
    }
}

# Metadata normalization settings
NORMALIZATION_CONFIG = {
    "confidence_weights": {
        "loc": 0.4,
        "hathitrust": 0.3,
        "musicbrainz": 0.3
    },
    "author_name_cleanup_patterns": [
        r'\s*\([^)]*\)',  # Remove dates in parentheses
        r'\b(Jr\.?|Sr\.?|III?|IV|PhD|Dr\.?|Prof\.?)\b'  # Remove titles
    ],
    "corporate_authorship_indicators": [
        'company', 'corporation', 'inc.', 'ltd.', 'llc', 'organization',
        'university', 'press', 'publishing', 'government', 'department'
    ],
    "anonymous_indicators": [
        'anonymous', 'unknown', 'various', 'anon.'
    ]
}

# Search and analysis settings
ANALYSIS_CONFIG = {
    "default_work_type": "auto",
    "max_api_timeout": 30,  # seconds
    "max_search_results": 50,
    "batch_processing_delay": 0.1,  # seconds between batch items
    "verbose_logging": True
}

# Work type mappings
WORK_TYPE_CONFIG = {
    "literary": {
        "primary_apis": ["library_of_congress", "hathitrust"],
        "secondary_apis": [],
        "file_formats": ["book", "text", "manuscript"]
    },
    "musical": {
        "primary_apis": ["musicbrainz"],
        "secondary_apis": ["library_of_congress"],
        "file_formats": ["sound recording", "musical composition", "score"]
    },
    "auto": {
        "detection_strategy": "query_all_then_rank",
        "fallback_type": "literary"
    }
}

def get_api_config(api_name: str) -> Dict[str, Any]:
    """Get configuration for a specific API client"""
    return API_CLIENTS_CONFIG.get(api_name, {})

def get_confidence_weight(source: str) -> float:
    """Get confidence weight for a data source"""
    return NORMALIZATION_CONFIG["confidence_weights"].get(source, 0.1)

def get_supported_work_types() -> List[str]:
    """Get list of supported work types"""
    return list(WORK_TYPE_CONFIG.keys())

def get_work_type_apis(work_type: str) -> Dict[str, List[str]]:
    """Get API configuration for a work type"""
    config = WORK_TYPE_CONFIG.get(work_type, {})
    return {
        "primary": config.get("primary_apis", []),
        "secondary": config.get("secondary_apis", [])
    }