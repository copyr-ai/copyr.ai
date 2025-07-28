import requests
import json
from typing import Optional, Dict, Any, List
import time

from ....models.work_record import APIResponse
from ....core.base_api_client import BaseDigitalLibraryClient

class HathiTrustClient(BaseDigitalLibraryClient):
    """
    Client for HathiTrust Digital Library API
    Docs: https://www.hathitrust.org/data_api
    """
    
    BASE_URL = "https://catalog.hathitrust.org/api"
    VOLUMES_ENDPOINT = "/volumes"
    
    def __init__(self, rate_limit_delay: float = 1.0):
        super().__init__(rate_limit_delay)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'copyr.ai/1.0 (copyright research tool)',
            'Accept': 'application/json'
        })
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def search_books(self, title: str, author: str) -> APIResponse:
        """Search for books by title and author (maps to existing method)"""
        return self.search_by_title_author(title, author)
    
    def search_by_title_author(self, title: str, author: str) -> APIResponse:
        """
        Search HathiTrust by title and author
        Note: HathiTrust API primarily works with identifiers, so this is a best-effort search
        """
        self._rate_limit()
        
        # HathiTrust search is limited, so we'll try to construct a reasonable query
        search_url = f"https://catalog.hathitrust.org/Search/Home"
        
        try:
            # First try to search via the web interface to get identifiers
            params = {
                'lookfor': f'"{title}" "{author}"',
                'type': 'all',
                'filter[]': 'format:Book'
            }
            
            response = self.session.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            # For now, return a placeholder - in production, would need to parse HTML
            # or use a different approach since HathiTrust API is primarily ID-based
            return APIResponse(
                success=False,
                error="HathiTrust search by title/author requires additional implementation",
                source_url=response.url
            )
            
        except requests.exceptions.RequestException as e:
            return APIResponse(
                success=False,
                error=f"HathiTrust search failed: {str(e)}",
                source_url=search_url
            )
    
    def get_volume_brief_by_identifier(self, identifier_type: str, identifier: str) -> APIResponse:
        """Get brief volume information by identifier"""
        if identifier_type.lower() == 'oclc':
            return self.get_volume_brief_by_oclc(identifier)
        elif identifier_type.lower() == 'isbn':
            return self.get_volume_brief_by_isbn(identifier)
        else:
            return APIResponse(
                success=False,
                error=f"Unsupported identifier type: {identifier_type}"
            )
    
    def get_volume_brief_by_oclc(self, oclc_number: str) -> APIResponse:
        """
        Get brief volume information by OCLC number
        This is the primary way to get rights information from HathiTrust
        """
        self._rate_limit()
        
        url = f"{self.BASE_URL}{self.VOLUMES_ENDPOINT}/brief/json/oclc:{oclc_number}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse the response
            parsed_data = self._parse_volume_data(data)
            
            return APIResponse(
                success=True,
                data=parsed_data,
                source_url=url,
                confidence=0.9 if parsed_data else 0.1
            )
            
        except requests.exceptions.RequestException as e:
            return APIResponse(
                success=False,
                error=f"HathiTrust API request failed: {str(e)}",
                source_url=url
            )
        except json.JSONDecodeError as e:
            return APIResponse(
                success=False,
                error=f"HathiTrust API response parsing failed: {str(e)}",
                source_url=url
            )
    
    def get_volume_brief_by_isbn(self, isbn: str) -> APIResponse:
        """Get brief volume information by ISBN"""
        self._rate_limit()
        
        # Clean ISBN (remove hyphens)
        clean_isbn = isbn.replace('-', '').replace(' ', '')
        url = f"{self.BASE_URL}{self.VOLUMES_ENDPOINT}/brief/json/isbn:{clean_isbn}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            parsed_data = self._parse_volume_data(data)
            
            return APIResponse(
                success=True,
                data=parsed_data,
                source_url=url,
                confidence=0.9 if parsed_data else 0.1
            )
            
        except requests.exceptions.RequestException as e:
            return APIResponse(
                success=False,
                error=f"HathiTrust API request failed: {str(e)}",
                source_url=url
            )
    
    def _parse_volume_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse HathiTrust volume data"""
        if not data or 'items' not in data:
            return None
        
        results = {
            'volumes': [],
            'rights_summary': {},
            'best_volume': None
        }
        
        rights_counts = {}
        
        for item_id, item_data in data['items'].items():
            volume_info = {
                'item_id': item_id,
                'title': item_data.get('title', ''),
                'publisher': item_data.get('publisher', ''),
                'publication_date': item_data.get('publishDate', ''),
                'rights': item_data.get('rightsCode', ''),
                'access': item_data.get('accessLevel', ''),
                'url': f"https://catalog.hathitrust.org/Record/{item_id}",
                'raw_data': item_data
            }
            
            results['volumes'].append(volume_info)
            
            # Count rights codes
            rights_code = item_data.get('rightsCode', 'unknown')
            rights_counts[rights_code] = rights_counts.get(rights_code, 0) + 1
        
        # Create rights summary
        results['rights_summary'] = {
            'most_common_rights': max(rights_counts.items(), key=lambda x: x[1])[0] if rights_counts else 'unknown',
            'rights_distribution': rights_counts,
            'interpretation': self._interpret_rights_codes(rights_counts)
        }
        
        # Find best volume (prefer public domain, then most recent)
        if results['volumes']:
            results['best_volume'] = self._find_best_volume(results['volumes'])
        
        return results
    
    def _find_best_volume(self, volumes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find the best volume from the list"""
        if not volumes:
            return None
        
        # Scoring function
        def score_volume(vol):
            score = 0
            rights = vol.get('rights', '').lower()
            
            # Prefer public domain
            if 'pd' in rights or 'public' in rights:
                score += 100
            
            # Prefer full access
            if vol.get('access') == 'allow':
                score += 50
            
            # Prefer more recent publication (if date available)
            pub_date = vol.get('publication_date', '')
            if pub_date and pub_date.isdigit():
                # More recent gets higher score (but not too much weight)
                score += int(pub_date) // 100
            
            return score
        
        return max(volumes, key=score_volume)
    
    def _interpret_rights_codes(self, rights_counts: Dict[str, int]) -> Dict[str, str]:
        """Interpret HathiTrust rights codes"""
        interpretations = {}
        
        # Common HathiTrust rights codes
        rights_meanings = {
            'pd': 'Public Domain - free to use',
            'pdus': 'Public Domain in US - free to use in US',
            'ic': 'In Copyright - restricted access',
            'ic-world': 'In Copyright worldwide - restricted access',
            'und': 'Undetermined copyright status',
            'cc': 'Creative Commons license',
            'opb': 'Open access book'
        }
        
        for rights_code, count in rights_counts.items():
            meaning = rights_meanings.get(rights_code.lower(), f'Unknown rights code: {rights_code}')
            interpretations[rights_code] = f"{meaning} ({count} volumes)"
        
        return interpretations
    
    def extract_identifier_from_metadata(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Extract OCLC identifier from Library of Congress metadata"""
        return self.extract_oclc_from_loc_data(metadata)
    
    def extract_oclc_from_loc_data(self, loc_data: Dict[str, Any]) -> Optional[str]:
        """Extract OCLC number from Library of Congress data"""
        # Look for OCLC numbers in various fields
        if 'raw_data' in loc_data and isinstance(loc_data['raw_data'], dict):
            item = loc_data['raw_data']
            
            # Check control numbers
            control_numbers = item.get('control_number', [])
            for control_num in control_numbers:
                if isinstance(control_num, str) and 'oclc' in control_num.lower():
                    # Extract digits from OCLC number
                    import re
                    oclc_match = re.search(r'oclc[^\d]*(\d+)', control_num.lower())
                    if oclc_match:
                        return oclc_match.group(1)
            
            # Check other identifier fields
            identifiers = item.get('identifier', [])
            for identifier in identifiers:
                if isinstance(identifier, str) and 'oclc' in identifier.lower():
                    import re
                    oclc_match = re.search(r'oclc[^\d]*(\d+)', identifier.lower())
                    if oclc_match:
                        return oclc_match.group(1)
        
        return None
    
    def get_item_details(self, item_identifier: str) -> APIResponse:
        """Get detailed information about a specific item (maps to OCLC lookup)"""
        return self.get_volume_brief_by_oclc(item_identifier)