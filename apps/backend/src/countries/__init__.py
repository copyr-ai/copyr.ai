"""
Country-specific implementations for copyright analysis
"""

# Country registry for dynamic loading
COUNTRY_REGISTRY = {
    'US': {
        'name': 'United States',
        'analyzer_class': 'countries.us.us_analyzer.USAnalyzer',
        'calculator_class': 'countries.us.copyright_rules.USCopyrightCalculator',
        'api_clients': {
            'library_of_congress': 'countries.us.api_clients.library_of_congress.LibraryOfCongressClient',
            'hathitrust': 'countries.us.api_clients.hathitrust.HathiTrustClient',
            'musicbrainz': 'countries.us.api_clients.musicbrainz.MusicBrainzClient'
        },
        'config_module': 'countries.us.config'
    }
    # Future countries will be added here:
    # 'UK': { ... },
    # 'CA': { ... },
    # etc.
}

def get_supported_countries():
    """Get list of supported country codes"""
    return list(COUNTRY_REGISTRY.keys())

def get_country_info(country_code: str):
    """Get information about a specific country"""
    return COUNTRY_REGISTRY.get(country_code.upper())

def is_country_supported(country_code: str) -> bool:
    """Check if a country is supported"""
    return country_code.upper() in COUNTRY_REGISTRY