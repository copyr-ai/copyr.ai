from typing import Dict, Any, Optional, List
import re
from datetime import datetime

from ..models.work_record import WorkRecord, APIResponse

class MetadataNormalizer:
    """
    Normalizes and merges metadata from different API sources
    """
    
    @staticmethod
    def normalize_author_name(name: str) -> str:
        """Normalize author/composer names to standard format"""
        if not name:
            return ""
        
        name = re.sub(r'\s+', ' ', name.strip())
        
        # Handle "Last, First" format
        if ',' in name and len(name.split(',')) == 2:
            last, first = [part.strip() for part in name.split(',')]
            name = f"{first} {last}"
        
        # Remove dates and titles
        name = re.sub(r'\s*\([^)]*\)', '', name)
        name = re.sub(r'\b(Jr\.?|Sr\.?|III?|IV|PhD|Dr\.?|Prof\.?)\b', '', name, flags=re.IGNORECASE)
        
        return name.strip()
    
    @staticmethod
    def extract_publication_year(date_string: str) -> Optional[int]:
        """Extract publication year from date string"""
        if not date_string:
            return None
        
        year_match = re.search(r'\b(1[5-9]\d{2}|20[0-9]\d)\b', str(date_string))
        return int(year_match.group(1)) if year_match else None
    
    @staticmethod
    def extract_death_year(life_span_data: Dict[str, Any]) -> Optional[int]:
        """Extract death year from life span data"""
        if not life_span_data:
            return None
        
        # MusicBrainz format
        if 'end' in life_span_data:
            end_date = str(life_span_data['end'])
            if len(end_date) >= 4:
                try:
                    return int(end_date[:4])
                except ValueError:
                    pass
        
        # Other formats
        death_date = life_span_data.get('death') or life_span_data.get('died', '')
        if death_date:
            return MetadataNormalizer.extract_publication_year(str(death_date))
        
        return None
    
    @staticmethod
    def determine_work_type(metadata: Dict[str, Any]) -> str:
        """Determine work type based on metadata"""
        author_name = metadata.get('author_name', '').lower()
        
        # Corporate authorship
        corporate_indicators = ['company', 'corporation', 'inc.', 'ltd.', 'llc', 'university', 'press', 'government']
        if any(indicator in author_name for indicator in corporate_indicators):
            return 'work_for_hire'
        
        # Anonymous works
        anonymous_indicators = ['anonymous', 'unknown', 'various', 'anon.']
        if any(indicator in author_name for indicator in anonymous_indicators):
            return 'anonymous'
        
        return 'individual'
    
    @staticmethod
    def merge_api_responses(
        loc_response: Optional[APIResponse] = None,
        hathi_response: Optional[APIResponse] = None,
        musicbrainz_response: Optional[APIResponse] = None,
        musicbrainz_artist_response: Optional[APIResponse] = None,
        search_title: str = "",
        search_author: str = ""
    ) -> Dict[str, Any]:
        """
        Merge responses from different APIs into normalized metadata
        """
        merged = {
            'title': '',
            'author_name': '',
            'publication_year': None,
            'author_death_year': None,
            'country': 'US',
            'confidence_sources': {},
            'source_links': {},
            'work_type_indicators': [],
            'search_title': search_title,
            'search_author': search_author
        }
        
        # Process Library of Congress data
        if loc_response and loc_response.success and loc_response.data:
            loc_data = loc_response.data
            best_match = loc_data.get('best_match')
            
            if best_match:
                # Check if this is a high-quality match before using the data
                # Title - only use if it's a reasonably good match
                loc_title = best_match.get('title', '').lower()
                search_title_lower = merged['search_title'].lower()
                
                # Simple title relevance check
                title_similarity = 0
                if search_title_lower in loc_title or loc_title in search_title_lower:
                    min_len = min(len(loc_title), len(search_title_lower))
                    max_len = max(len(loc_title), len(search_title_lower))
                    title_similarity = min_len / max_len if max_len > 0 else 0
                
                # Only use LOC title if similarity is reasonable (not anthology/collection)
                if (best_match.get('title') and not merged['title'] and 
                    (title_similarity > 0.6 or loc_response.confidence > 0.7)):
                    merged['title'] = best_match['title']
                
                # Author - find the best matching author from the list
                authors = best_match.get('authors', [])
                if authors and not merged['author_name']:
                    # Try to find the target author in the list first
                    target_author_lower = merged['search_author'].lower()
                    selected_author = None
                    
                    # Look for exact or close matches to our target author
                    for author in authors:
                        normalized = MetadataNormalizer.normalize_author_name(author).lower()
                        if (target_author_lower in normalized or 
                            normalized in target_author_lower or
                            # Handle "last, first" format matching
                            (target_author_lower.replace(' ', ', ') in author.lower()) or
                            (target_author_lower.replace(', ', ' ') in normalized)):
                            selected_author = author
                            break
                    
                    # If no good match found, use the first author
                    if not selected_author:
                        selected_author = authors[0]
                    
                    merged['author_name'] = MetadataNormalizer.normalize_author_name(selected_author)
                
                # Publication year
                if best_match.get('publication_year') and not merged['publication_year']:
                    merged['publication_year'] = best_match['publication_year']
                
                # Source link
                if best_match.get('url'):
                    merged['source_links']['loc'] = best_match['url']
                
                merged['confidence_sources']['loc'] = loc_response.confidence
        
        # Process HathiTrust data
        if hathi_response and hathi_response.success and hathi_response.data:
            hathi_data = hathi_response.data
            best_volume = hathi_data.get('best_volume')
            
            if best_volume:
                # Title (if not already set or better match)
                if best_volume.get('title') and (not merged['title'] or 
                    hathi_response.confidence > merged['confidence_sources'].get('loc', 0)):
                    merged['title'] = best_volume['title']
                
                # Publication year
                pub_date = best_volume.get('publication_date', '')
                pub_year = MetadataNormalizer.extract_publication_year(pub_date)
                if pub_year and not merged['publication_year']:
                    merged['publication_year'] = pub_year
                
                # Source link
                if best_volume.get('url'):
                    merged['source_links']['hathitrust'] = best_volume['url']
                
                # Rights information
                rights_summary = hathi_data.get('rights_summary', {})
                if rights_summary:
                    merged['hathi_rights'] = rights_summary
                
                merged['confidence_sources']['hathitrust'] = hathi_response.confidence
        
        # Process MusicBrainz work data
        if musicbrainz_response and musicbrainz_response.success and musicbrainz_response.data:
            mb_data = musicbrainz_response.data
            best_match = mb_data.get('best_match')
            
            if best_match:
                # Title
                if best_match.get('title') and not merged['title']:
                    merged['title'] = best_match['title']
                
                # Composer
                composers = best_match.get('composers', [])
                if composers and not merged['author_name']:
                    merged['author_name'] = MetadataNormalizer.normalize_author_name(composers[0]['name'])
                
                # Source link
                if best_match.get('url'):
                    merged['source_links']['musicbrainz'] = best_match['url']
                
                merged['confidence_sources']['musicbrainz'] = musicbrainz_response.confidence
        
        # Process MusicBrainz artist data
        if musicbrainz_artist_response and musicbrainz_artist_response.success and musicbrainz_artist_response.data:
            artist_data = musicbrainz_artist_response.data
            best_artist = artist_data.get('best_match')
            
            if best_artist:
                # Death year
                if best_artist.get('death_year') and not merged['author_death_year']:
                    merged['author_death_year'] = best_artist['death_year']
                
                # Country
                if best_artist.get('country'):
                    merged['country'] = best_artist['country']
        
        # Determine work type
        merged['work_type'] = MetadataNormalizer.determine_work_type(merged)
        
        return merged
    
    @staticmethod
    def create_work_record(
        title: str,
        author: str,
        merged_metadata: Dict[str, Any],
        copyright_analysis: Optional[Dict[str, Any]] = None
    ) -> WorkRecord:
        """
        Create a WorkRecord from merged metadata and copyright analysis
        """
        record = WorkRecord(
            title=merged_metadata.get('title') or title,
            author_name=merged_metadata.get('author_name') or author,
            publication_year=merged_metadata.get('publication_year'),
            year_of_death=merged_metadata.get('author_death_year'),
            country=merged_metadata.get('country', 'US'),
            work_type=merged_metadata.get('work_type', 'individual'),
            source_links=merged_metadata.get('source_links', {}),
            queried_at=datetime.utcnow()
        )
        
        # Add copyright analysis if available
        if copyright_analysis:
            record.status = copyright_analysis.get('status', 'Unknown')
            record.enters_public_domain = copyright_analysis.get('enters_public_domain')
            record.notes = copyright_analysis.get('notes', '')
        
        # Calculate confidence score
        confidence_sources = merged_metadata.get('confidence_sources', {})
        if confidence_sources:
            # Average confidence weighted by source reliability
            weights = {'loc': 0.4, 'hathitrust': 0.3, 'musicbrainz': 0.3}
            total_weight = 0
            weighted_confidence = 0
            
            for source, confidence in confidence_sources.items():
                weight = weights.get(source, 0.2)
                weighted_confidence += confidence * weight
                total_weight += weight
            
            record.confidence_score = weighted_confidence / total_weight if total_weight > 0 else 0.0
        
        return record