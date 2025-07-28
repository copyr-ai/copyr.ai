import requests
import json
from typing import Optional, Dict, Any, List
from urllib.parse import quote
import time

from ....models.work_record import APIResponse
from ....core.base_api_client import BaseAPIClient

class LibraryOfCongressClient(BaseAPIClient):
    """
    Client for Library of Congress Search API
    Docs: https://www.loc.gov/apis/
    """
    
    BASE_URL = "https://www.loc.gov"
    SEARCH_ENDPOINT = "/search"
    
    def __init__(self, rate_limit_delay: float = 1.0):
        super().__init__(rate_limit_delay)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'copyr.ai/1.0 (copyright research tool)',
            'Accept': 'application/json'
        })
    
    def search_books(self, title: str, author: str) -> APIResponse:
        """
        Search for books in Library of Congress catalog
        
        Args:
            title: Book title
            author: Author name
            
        Returns:
            APIResponse with search results
        """
        self._rate_limit()
        
        # Construct search query
        query = f'"{title}" "{author}"'
        search_url = f"{self.BASE_URL}{self.SEARCH_ENDPOINT}"
        
        params = {
            'q': query,
            'fo': 'json',
            'c': 50,  # max results
            'at': 'results,pagination',
            'format': 'book'
        }
        
        try:
            response = self.session.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            source_url = response.url
            
            # Parse results
            parsed_results = self._parse_search_results(data, title, author)
            
            return APIResponse(
                success=True,
                data=parsed_results,
                source_url=source_url,
                confidence=self._calculate_confidence(parsed_results, title, author)
            )
            
        except requests.exceptions.RequestException as e:
            return APIResponse(
                success=False,
                error=f"LOC API request failed: {str(e)}",
                source_url=search_url
            )
        except json.JSONDecodeError as e:
            return APIResponse(
                success=False,
                error=f"LOC API response parsing failed: {str(e)}",
                source_url=search_url
            )
    
    def _parse_search_results(self, data: Dict[str, Any], title: str, author: str) -> Dict[str, Any]:
        """Parse LOC search results"""
        results = {
            'matches': [],
            'total_results': 0,
            'best_match': None
        }
        
        if 'results' not in data:
            return results
        
        results['total_results'] = len(data['results'])
        
        for item in data['results']:
            parsed_item = self._parse_item(item)
            if parsed_item:
                results['matches'].append(parsed_item)
        
        # Find best match
        if results['matches']:
            results['best_match'] = self._find_best_match(results['matches'], title, author)
        
        return results
    
    def _parse_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse individual LOC catalog item"""
        try:
            # Extract basic metadata
            title = item.get('title', [''])[0] if item.get('title') else ''
            contributors = item.get('contributor', [])
            dates = item.get('date', [])
            
            # Parse publication year
            pub_year = None
            for date_str in dates:
                if isinstance(date_str, str) and date_str.isdigit():
                    pub_year = int(date_str)
                    break
                elif isinstance(date_str, str):
                    # Try to extract year from date string
                    import re
                    year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
                    if year_match:
                        pub_year = int(year_match.group())
                        break
            
            # Parse authors
            authors = []
            for contrib in contributors:
                if isinstance(contrib, str):
                    authors.append(contrib)
            
            # Get URL
            url = item.get('id', '')
            if url and not url.startswith('http'):
                url = f"{self.BASE_URL}{url}"
            
            return {
                'title': title,
                'authors': authors,
                'publication_year': pub_year,
                'url': url,
                'format': item.get('original_format', []),
                'subjects': item.get('subject', []),
                'raw_data': item
            }
            
        except Exception as e:
            # Log error but continue processing other items
            print(f"Error parsing LOC item: {e}")
            return None
    
    def _find_best_match(self, matches: List[Dict[str, Any]], target_title: str, target_author: str) -> Dict[str, Any]:
        """Find the best matching item from search results"""
        if not matches:
            return None
        
        # Simple scoring based on title and author similarity
        def score_match(item):
            score = 0
            item_title = item.get('title', '').lower()
            item_authors = [a.lower() for a in item.get('authors', [])]
            
            # Title similarity (simple substring matching)
            if target_title.lower() in item_title or item_title in target_title.lower():
                score += 50
            
            # Author similarity
            target_author_lower = target_author.lower()
            for author in item_authors:
                if target_author_lower in author or author in target_author_lower:
                    score += 40
                    break
            
            # Prefer items with publication year
            if item.get('publication_year'):
                score += 10
            
            return score
        
        # Return item with highest score
        return max(matches, key=score_match)
    
    def _calculate_confidence(self, results: Dict[str, Any], title: str, author: str) -> float:
        """Calculate confidence score for the results"""
        if not results.get('matches'):
            return 0.0
        
        best_match = results.get('best_match')
        if not best_match:
            return 0.1
        
        confidence = 0.3  # Base confidence for having results
        
        # Boost confidence for exact matches
        if best_match.get('title', '').lower() == title.lower():
            confidence += 0.4
        elif title.lower() in best_match.get('title', '').lower():
            confidence += 0.2
        
        # Boost confidence for author matches
        target_author_lower = author.lower()
        for item_author in best_match.get('authors', []):
            if target_author_lower in item_author.lower():
                confidence += 0.3
                break
        
        return min(confidence, 1.0)
    
    def get_item_details(self, item_url: str) -> APIResponse:
        """Get detailed information about a specific LOC item"""
        self._rate_limit()
        
        try:
            # Add JSON format parameter
            detail_url = f"{item_url}?fo=json"
            
            response = self.session.get(detail_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            return APIResponse(
                success=True,
                data=data,
                source_url=detail_url,
                confidence=0.8
            )
            
        except requests.exceptions.RequestException as e:
            return APIResponse(
                success=False,
                error=f"LOC detail request failed: {str(e)}",
                source_url=item_url
            )