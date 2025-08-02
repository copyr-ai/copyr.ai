import requests
import json
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List
from urllib.parse import quote
import time

from ....models.work_record import APIResponse
from ....core.base_api_client import BaseAPIClient

class LibraryOfCongressClient(BaseAPIClient):
    """
    Client for Library of Congress SRU (Search/Retrieval via URL) API
    Uses proper bibliographic search with CQL (Contextual Query Language)
    Docs: https://www.loc.gov/standards/sru/
    """
    
    SRU_BASE_URL = "http://lx2.loc.gov:210/LCDB"
    NAMESPACES = {
        'srw': 'http://www.loc.gov/zing/srw/',
        'mods': 'http://www.loc.gov/mods/v3',
        'marc': 'http://www.loc.gov/MARC21/slim'
    }
    
    def __init__(self, rate_limit_delay: float = 1.0):
        super().__init__(rate_limit_delay)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'copyr.ai/1.0 (copyright research tool)',
            'Accept': 'application/json'
        })
    
    def search_books(self, title: str, author: str) -> APIResponse:
        """
        Search for books using Library of Congress SRU API with CQL
        
        Args:
            title: Book title
            author: Author name
            
        Returns:
            APIResponse with search results
        """
        self._rate_limit()
        
        # Construct CQL query using proper bibliographic indexes
        cql_parts = []
        
        if title and title.strip():
            # Use dc.title for title search
            escaped_title = title.replace('"', '\\"')
            cql_parts.append(f'dc.title="{escaped_title}"')
        
        if author and author.strip() and author.lower() not in ['unknown', 'string', 'author']:
            # Use dc.creator for author search (Dublin Core creator)
            escaped_author = author.replace('"', '\\"')
            cql_parts.append(f'dc.creator="{escaped_author}"')
        
        if not cql_parts:
            return APIResponse(
                success=False,
                error="No valid search terms provided",
                source_url=""
            )
        
        # Join with AND for precise matching
        cql_query = " AND ".join(cql_parts)
        
        params = {
            'version': '1.1',
            'operation': 'searchRetrieve', 
            'query': cql_query,
            'maximumRecords': '20',
            'recordSchema': 'mods'  # MODS format for rich metadata
        }
        
        try:
            response = self.session.get(self.SRU_BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            source_url = response.url
            
            # Parse XML response
            parsed_results = self._parse_sru_response(response.text, title, author)
            
            return APIResponse(
                success=True,
                data=parsed_results,
                source_url=source_url,
                confidence=self._calculate_sru_confidence(parsed_results, title, author)
            )
            
        except requests.exceptions.RequestException as e:
            return APIResponse(
                success=False,
                error=f"LOC SRU API request failed: {str(e)}",
                source_url=self.SRU_BASE_URL
            )
        except ET.ParseError as e:
            return APIResponse(
                success=False,
                error=f"LOC SRU XML parsing failed: {str(e)}",
                source_url=self.SRU_BASE_URL
            )
    
    def _parse_sru_response(self, xml_text: str, title: str, author: str) -> Dict[str, Any]:
        """Parse SRU XML response with MODS records"""
        results = {
            'matches': [],
            'total_results': 0,
            'best_match': None
        }
        
        try:
            root = ET.fromstring(xml_text)
            
            # Get number of records
            num_records_elem = root.find('.//srw:numberOfRecords', self.NAMESPACES)
            if num_records_elem is not None:
                results['total_results'] = int(num_records_elem.text or 0)
            
            # Parse each record
            records = root.findall('.//srw:record', self.NAMESPACES)
            for record in records:
                parsed_item = self._parse_mods_record(record)
                if parsed_item:
                    results['matches'].append(parsed_item)
            
            # Return multiple relevant results instead of just one "best match"
            # Filter for most relevant matches and return up to 5
            if results['matches']:
                relevant_matches = self._filter_relevant_matches(results['matches'], title, author)
                results['best_match'] = relevant_matches[0] if relevant_matches else None
                results['relevant_matches'] = relevant_matches[:5]  # Up to 5 relevant matches
            
            return results
            
        except ET.ParseError as e:
            # Return empty results if XML parsing fails
            return results
    
    def _parse_mods_record(self, record) -> Optional[Dict[str, Any]]:
        """Parse individual MODS record from SRU response"""
        try:
            # Find the MODS element
            mods_elem = record.find('.//mods:mods', self.NAMESPACES)
            if mods_elem is None:
                return None
            
            # Extract title
            title_elem = mods_elem.find('.//mods:titleInfo/mods:title', self.NAMESPACES)
            title = title_elem.text if title_elem is not None else ''
            
            # Extract authors (personal names with author role)
            authors = []
            name_elems = mods_elem.findall('.//mods:name[@type="personal"]', self.NAMESPACES)
            for name_elem in name_elems:
                # Check if this is an author
                role_elem = name_elem.find('.//mods:roleTerm', self.NAMESPACES)
                if role_elem is not None and role_elem.text in ['author', 'creator', 'aut']:
                    name_part_elems = name_elem.findall('.//mods:namePart', self.NAMESPACES)
                    if name_part_elems:
                        # Combine name parts
                        name_parts = [elem.text for elem in name_part_elems if elem.text]
                        full_name = ' '.join(name_parts)
                        authors.append(full_name)
                else:
                    # If no role specified, assume it might be an author
                    name_part_elems = name_elem.findall('.//mods:namePart', self.NAMESPACES)
                    if name_part_elems:
                        name_parts = [elem.text for elem in name_part_elems if elem.text]
                        full_name = ' '.join(name_parts)
                        authors.append(full_name)
            
            # Extract publication year
            pub_year = None
            date_issued_elem = mods_elem.find('.//mods:dateIssued', self.NAMESPACES)
            if date_issued_elem is not None and date_issued_elem.text:
                import re
                year_match = re.search(r'\b(1[5-9]\d{2}|20[0-9]\d)\b', date_issued_elem.text)
                if year_match:
                    pub_year = int(year_match.group())
            
            # Extract identifiers for URL construction
            record_id = None
            lccn_id = None
            
            # Look for LCCN identifier in MODS
            identifier_elems = mods_elem.findall('.//mods:identifier', self.NAMESPACES)
            for identifier_elem in identifier_elems:
                id_type = identifier_elem.get('type', '')
                if id_type == 'lccn' and identifier_elem.text:
                    lccn_id = identifier_elem.text.strip()
                    record_id = lccn_id
                    break
            
            # If no LCCN, look for record identifier in MODS recordInfo
            if not record_id:
                record_info = mods_elem.find('.//mods:recordInfo/mods:recordIdentifier', self.NAMESPACES)
                if record_info is not None and record_info.text:
                    record_id = record_info.text.strip()
            
            # Construct URL
            url = ''
            if lccn_id:
                # Use proper LCCN permalink format
                url = f'https://lccn.loc.gov/{lccn_id}'
            elif record_id:
                # Fallback to generic record URL
                url = f'https://catalog.loc.gov/vwebv/holdingsInfo?bibId={record_id}'
            
            return {
                'title': title,
                'authors': authors,
                'publication_year': pub_year,
                'url': url,
                'record_id': record_id,
                'raw_mods': mods_elem
            }
            
        except Exception:
            # Skip malformed records silently
            return None
    
    def _calculate_sru_confidence(self, results: Dict[str, Any], title: str, author: str) -> float:
        """Calculate confidence score for SRU results"""
        if not results.get('matches'):
            return 0.0
        
        best_match = results.get('best_match')
        if not best_match:
            return 0.1
        
        # SRU with CQL should return much more accurate results
        # Start with higher base confidence
        confidence = 0.6
        
        # Check title match quality
        best_title = best_match.get('title', '').lower()
        target_title = title.lower()
        if target_title in best_title or best_title in target_title:
            confidence += 0.2
        
        # Check author match quality (if author was provided)
        if author and author.lower() not in ['unknown', 'string', 'author']:
            target_author = author.lower()
            found_author_match = False
            for item_author in best_match.get('authors', []):
                if target_author in item_author.lower() or item_author.lower() in target_author:
                    found_author_match = True
                    break
            
            if found_author_match:
                confidence += 0.2
            else:
                # Author mismatch reduces confidence
                confidence -= 0.3
        
        return min(max(confidence, 0.0), 1.0)
    
    def _filter_relevant_matches(self, matches: List[Dict[str, Any]], target_title: str, target_author: str) -> List[Dict[str, Any]]:
        """Filter and score matches to return only relevant ones"""
        if not matches:
            return []
        
        scored_matches = []
        target_title_lower = target_title.lower().strip()
        target_author_lower = target_author.lower().strip()
        
        for match in matches:
            score = self._calculate_relevance_score(match, target_title_lower, target_author_lower)
            if score > 0:  # Only include matches with positive relevance
                scored_matches.append((match, score))
        
        # Sort by relevance score (highest first)
        scored_matches.sort(key=lambda x: x[1], reverse=True)
        
        # Return just the matches (without scores)
        return [match for match, score in scored_matches]
    
    def _calculate_relevance_score(self, match: Dict[str, Any], target_title: str, target_author: str) -> float:
        """Calculate relevance score for a match"""
        score = 0.0
        
        match_title = match.get('title', '').lower().strip()
        match_authors = [author.lower().strip() for author in match.get('authors', [])]
        
        # Title relevance (0-100 points)
        title_score = self._score_title_relevance(target_title, match_title)
        score += title_score
        
        # Author relevance (0-100 points)
        author_score = self._score_author_relevance(target_author, match_authors)
        score += author_score
        
        # Bonus for having publication year (5 points)
        if match.get('publication_year'):
            score += 5
        
        # Minimum relevance threshold - require at least some title OR author relevance
        min_title_score = 20
        min_author_score = 15
        
        # If we have a specific author (not generic), require some author relevance
        if (target_author and target_author not in ['unknown', 'string', 'author'] and 
            len(target_author) > 2):
            if title_score < min_title_score and author_score < min_author_score:
                return 0  # Not relevant enough
        else:
            # If no specific author, just require title relevance
            if title_score < min_title_score:
                return 0
        
        return score
    
    def _score_title_relevance(self, target: str, match: str) -> float:
        """Score title relevance (0-100)"""
        if not target or not match:
            return 0
        
        import re
        
        # Clean titles for comparison
        clean_target = re.sub(r'[^\w\s]', '', target).strip()
        clean_match = re.sub(r'[^\w\s]', '', match).strip()
        
        # Exact match
        if clean_target == clean_match:
            return 100
        
        # Substring match with length ratio
        if clean_target in clean_match or clean_match in clean_target:
            min_len = min(len(clean_target), len(clean_match))
            max_len = max(len(clean_target), len(clean_match))
            ratio = min_len / max_len if max_len > 0 else 0
            return 80 * ratio if ratio > 0.3 else 0
        
        # Word overlap
        target_words = set(word for word in target.split() if len(word) > 2)
        match_words = set(word for word in match.split() if len(word) > 2)
        
        if target_words and match_words:
            overlap = len(target_words & match_words)
            total = len(target_words | match_words)
            overlap_ratio = overlap / total if total > 0 else 0
            return 60 * overlap_ratio if overlap_ratio > 0.3 else 0
        
        return 0
    
    def _score_author_relevance(self, target: str, match_authors: List[str]) -> float:
        """Score author relevance (0-100)"""
        if not target or not match_authors:
            return 0
        
        # Skip scoring for generic authors
        if target in ['unknown', 'string', 'author']:
            return 50  # Neutral score for generic authors
        
        best_score = 0
        
        for i, author in enumerate(match_authors):
            current_score = 0
            
            # Exact match
            if target == author:
                current_score = 100
            # Substring match
            elif target in author or author in target:
                min_len = min(len(target), len(author))
                max_len = max(len(target), len(author))
                ratio = min_len / max_len if max_len > 0 else 0
                if ratio > 0.4:
                    current_score = 70 * ratio
            # Handle "Last, First" format
            elif ',' in author:
                parts = [p.strip() for p in author.split(',')]
                if len(parts) >= 2:
                    last_name, first_name = parts[0], parts[1]
                    if (last_name in target and first_name in target):
                        current_score = 85
                    elif last_name in target:
                        current_score = 60
            
            # Bonus for primary author (first in list)
            if i == 0 and current_score > 0:
                current_score *= 1.1
            
            best_score = max(best_score, current_score)
        
        return best_score
    
    def search_by_author(self, author: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for works by author only"""
        if not author or not author.strip():
            return []
        response = self.search_books("", author)
        if response.success and response.data:
            matches = response.data.get('relevant_matches', response.data.get('matches', []))
            return [self._format_work_result(match) for match in matches[:limit]]
        return []
    
    def search_by_title(self, title: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for works by title only"""
        if not title or not title.strip():
            return []
        response = self.search_books(title, "")
        if response.success and response.data:
            matches = response.data.get('relevant_matches', response.data.get('matches', []))
            return [self._format_work_result(match) for match in matches[:limit]]
        return []
    
    def search_by_title_and_author(self, title: str, author: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for works by both title and author"""
        if not title or not author or not title.strip() or not author.strip():
            return []
        response = self.search_books(title, author)
        if response.success and response.data:
            matches = response.data.get('relevant_matches', response.data.get('matches', []))
            return [self._format_work_result(match) for match in matches[:limit]]
        return []
    
    def _format_work_result(self, match: Dict[str, Any]) -> Dict[str, Any]:
        """Format a match result for the search endpoint"""
        return {
            'title': match.get('title', ''),
            'author': ', '.join(match.get('authors', [])) if match.get('authors') else '',
            'publication_year': match.get('publication_year'),
            'url': match.get('url', ''),
            'format': 'book',  # LOC results are typically books
            'source': 'library_of_congress'
        }

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