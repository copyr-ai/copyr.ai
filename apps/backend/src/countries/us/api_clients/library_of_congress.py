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
        
        # Construct search query with exact match for better results
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
            title_raw = item.get('title', '')
            title = title_raw[0] if isinstance(title_raw, list) and title_raw else str(title_raw) if title_raw else ''
            contributors = item.get('contributor', [])
            dates = item.get('date', [])
            
            # Parse publication year
            pub_year = None
            import re
            for date_str in dates:
                if isinstance(date_str, str):
                    if date_str.isdigit():
                        pub_year = int(date_str)
                        break
                    else:
                        year_match = re.search(r'\b(1[5-9]\d{2}|20[0-9]\d)\b', date_str)
                        if year_match:
                            pub_year = int(year_match.group())
                            break
            
            # Parse authors
            authors = [contrib for contrib in contributors if isinstance(contrib, str)]
            
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
            
        except Exception:
            # Skip malformed items silently
            return None
    
    def _find_best_match(self, matches: List[Dict[str, Any]], target_title: str, target_author: str) -> Dict[str, Any]:
        """Find the best matching item from search results"""
        if not matches:
            return None
        
        # Advanced scoring based on title and author similarity
        def score_match(item):
            score = 0
            item_title = item.get('title', '').lower().strip()
            item_authors = [a.lower().strip() for a in item.get('authors', [])]
            target_title_lower = target_title.lower().strip()
            target_author_lower = target_author.lower().strip()
            
            # Title similarity scoring
            title_score = 0
            
            # Clean titles for comparison (remove punctuation and extra spaces)
            import re
            clean_target = re.sub(r'[^\w\s]', '', target_title_lower).strip()
            clean_item = re.sub(r'[^\w\s]', '', item_title).strip()
            
            # Exact match gets highest score
            if clean_item == clean_target:
                title_score = 100
            # One contains the other with good length ratio
            elif clean_target in clean_item or clean_item in clean_target:
                # Award points based on how well they match
                min_len = min(len(clean_item), len(clean_target))
                max_len = max(len(clean_item), len(clean_target))
                length_ratio = min_len / max_len if max_len > 0 else 0
                
                if length_ratio > 0.2:  # At least 20% overlap
                    title_score = int(85 * length_ratio)
            # Word overlap scoring
            else:
                target_words = set(target_title_lower.split())
                item_words = set(item_title.split())
                
                # Remove very short words that don't matter
                target_words = {w for w in target_words if len(w) > 2}
                item_words = {w for w in item_words if len(w) > 2}
                
                if target_words and item_words:
                    overlap = len(target_words & item_words)
                    total_unique = len(target_words | item_words)
                    word_similarity = overlap / total_unique if total_unique > 0 else 0
                    title_score = int(60 * word_similarity)
            
            score += title_score
            
            # Author similarity scoring  
            author_score = 0
            best_author_match = 0
            
            for i, author in enumerate(item_authors):
                current_score = 0
                
                # Exact match
                if author == target_author_lower:
                    current_score = 100
                # Last name, first name format matching
                elif ',' in author:
                    # Parse "last, first" format
                    parts = [p.strip() for p in author.split(',')]
                    if len(parts) >= 2:
                        last_name = parts[0]
                        first_name = parts[1]
                        
                        # Check if target contains both names
                        if (last_name in target_author_lower and 
                            first_name in target_author_lower):
                            current_score = 90
                        elif last_name in target_author_lower:
                            current_score = 60
                        elif first_name in target_author_lower:
                            current_score = 40
                # Regular substring matching with length check
                elif target_author_lower in author or author in target_author_lower:
                    min_len = min(len(author), len(target_author_lower))
                    max_len = max(len(author), len(target_author_lower))
                    length_ratio = min_len / max_len if max_len > 0 else 0
                    
                    if length_ratio > 0.4:  # At least 40% overlap for authors
                        current_score = int(70 * length_ratio)
                
                # Bonus for being the primary author (first in list)
                if i == 0 and current_score > 0:
                    current_score = int(current_score * 1.2)  # 20% bonus
                
                best_author_match = max(best_author_match, current_score)
            
            # Heavy penalty if first author doesn't match at all but title does
            if (title_score > 50 and item_authors and 
                best_author_match == 0):
                # This might be a wrong match - reduce total score significantly
                score = int(score * 0.3)
            
            score += best_author_match
            
            # Bonus points for having publication year
            if item.get('publication_year'):
                score += 5
            
            
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