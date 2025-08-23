import aiohttp
import json
from typing import Optional, Dict, Any, List
import asyncio
from urllib.parse import quote

from ....models.work_record import APIResponse
from ....core.base_api_client import BaseMusicAPIClient

class MusicBrainzClient(BaseMusicAPIClient):
    """
    Client for MusicBrainz API for musical works metadata
    Docs: https://musicbrainz.org/doc/MusicBrainz_API
    """
    
    BASE_URL = "https://musicbrainz.org/ws/2"
    
    def __init__(self, rate_limit_delay: float = 1.1):  # MusicBrainz requires 1 req/sec
        super().__init__(rate_limit_delay)
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.headers = {
            'User-Agent': 'copyr.ai/1.0 (copyright research tool; contact@copyr.ai)',
            'Accept': 'application/json'
        }
    
    async def _async_rate_limit(self):
        """Async rate limiting using asyncio.sleep"""
        import time
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    async def get_session(self, external_session: Optional[aiohttp.ClientSession] = None) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        # Use external session if provided (preferred)
        if external_session and not external_session.closed:
            return external_session
            
        # Otherwise use our own session
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers=self.headers
            )
        return self.session
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def search_works(self, title: str, composer: str, session: Optional[aiohttp.ClientSession] = None) -> APIResponse:
        """
        Search for musical works by title and composer
        
        Args:
            title: Work title
            composer: Composer name
            
        Returns:
            APIResponse with search results
        """
        await self._async_rate_limit()
        
        # Construct search query for works
        query = f'work:"{title}" AND artist:"{composer}"'
        url = f"{self.BASE_URL}/work"
        
        params = {
            'query': query,
            'fmt': 'json',
            'limit': 25,
            'inc': 'artist-rels+tags+aliases'
        }
        
        try:
            client_session = await self.get_session(session)
            async with client_session.get(url, params=params) as response:
                response.raise_for_status()
                
                data = await response.json()
                source_url = str(response.url)
            
            # Parse results
            parsed_results = await self._parse_work_results(data, title, composer, session)
            
            return APIResponse(
                success=True,
                data=parsed_results,
                source_url=source_url,
                confidence=self._calculate_confidence(parsed_results, title, composer)
            )
            
        except aiohttp.ClientError as e:
            return APIResponse(
                success=False,
                error=f"MusicBrainz API request failed: {str(e)}",
                source_url=url
            )
        except json.JSONDecodeError as e:
            return APIResponse(
                success=False,
                error=f"MusicBrainz API response parsing failed: {str(e)}",
                source_url=url
            )
    
    async def search_artists(self, artist_name: str, session: Optional[aiohttp.ClientSession] = None) -> APIResponse:
        """Search for artist information to get birth/death dates"""
        await self._async_rate_limit()
        
        query = f'artist:"{artist_name}"'
        url = f"{self.BASE_URL}/artist"
        
        params = {
            'query': query,
            'fmt': 'json',
            'limit': 10
        }
        
        try:
            client_session = await self.get_session(session)
            async with client_session.get(url, params=params) as response:
                response.raise_for_status()
                
                data = await response.json()
                parsed_results = self._parse_artist_results(data, artist_name)
            
            return APIResponse(
                success=True,
                data=parsed_results,
                source_url=response.url,
                confidence=0.8 if parsed_results.get('best_match') else 0.2
            )
            
        except aiohttp.ClientError as e:
            return APIResponse(
                success=False,
                error=f"MusicBrainz artist search failed: {str(e)}",
                source_url=url
            )
    
    async def _parse_work_results(self, data: Dict[str, Any], title: str, composer: str, session: Optional[aiohttp.ClientSession] = None) -> Dict[str, Any]:
        """Parse MusicBrainz work search results"""
        results = {
            'works': [],
            'total_results': 0,
            'best_match': None
        }
        
        if 'works' not in data:
            return results
        
        results['total_results'] = len(data['works'])
        
        for work in data['works']:
            parsed_work = await self._parse_work_item(work, session)
            if parsed_work:
                results['works'].append(parsed_work)
        
        # Find best match
        if results['works']:
            results['best_match'] = self._find_best_work_match(results['works'], title, composer)
        
        return results
    
    async def _parse_work_item(self, work: Dict[str, Any], session: Optional[aiohttp.ClientSession] = None) -> Optional[Dict[str, Any]]:
        """Parse individual MusicBrainz work item"""
        try:
            # Extract basic work info
            work_info = {
                'id': work.get('id'),
                'title': work.get('title', ''),
                'type': work.get('type'),
                'language': work.get('language'),
                'composers': [],
                'tags': [],
                'earliest_release_year': None,
                'url': f"https://musicbrainz.org/work/{work.get('id', '')}"
            }
            
            # Extract composers from relations
            if 'relations' in work:
                for relation in work['relations']:
                    if relation.get('type') == 'composer' and 'artist' in relation:
                        artist = relation['artist']
                        composer_info = {
                            'name': artist.get('name', ''),
                            'id': artist.get('id'),
                            'sort_name': artist.get('sort-name', ''),
                            'life_span': artist.get('life-span', {})
                        }
                        work_info['composers'].append(composer_info)
            
            # Extract tags
            if 'tags' in work:
                work_info['tags'] = [tag.get('name', '') for tag in work['tags']]
            
            # Try to get earliest release date from the work
            work_info['earliest_release_year'] = await self._get_earliest_release_year(work.get('id'), session)
            
            return work_info
            
        except Exception as e:
            print(f"Error parsing MusicBrainz work: {e}")
            return None
    
    async def _get_earliest_release_year(self, work_id: str, session: Optional[aiohttp.ClientSession] = None) -> Optional[int]:
        """Get the earliest release year for a MusicBrainz work"""
        if not work_id:
            return None
            
        try:
            await self._async_rate_limit()
            
            # Search for recordings of this work
            url = f"{self.BASE_URL}/recording"
            params = {
                'query': f'wid:{work_id}',
                'fmt': 'json',
                'limit': 50,
                'inc': 'releases'  # Include release information
            }
            
            client_session = await self.get_session(session)
            async with client_session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
            
            earliest_year = None
            
            if 'recordings' in data:
                for recording in data['recordings']:
                    if 'releases' in recording:
                        for release in recording['releases']:
                            release_date = release.get('date')
                            if release_date:
                                # Extract year from date (YYYY-MM-DD format)
                                try:
                                    year = int(release_date.split('-')[0])
                                    if earliest_year is None or year < earliest_year:
                                        earliest_year = year
                                except (ValueError, IndexError):
                                    continue
            
            return earliest_year
            
        except Exception as e:
            print(f"Error getting earliest release year for work {work_id}: {e}")
            return None
    
    def _parse_artist_results(self, data: Dict[str, Any], artist_name: str) -> Dict[str, Any]:
        """Parse MusicBrainz artist search results"""
        results = {
            'artists': [],
            'best_match': None
        }
        
        if 'artists' not in data:
            return results
        
        for artist in data['artists']:
            artist_info = {
                'id': artist.get('id'),
                'name': artist.get('name', ''),
                'sort_name': artist.get('sort-name', ''),
                'type': artist.get('type'),
                'country': artist.get('country'),
                'life_span': artist.get('life-span', {}),
                'birth_year': None,
                'death_year': None,
                'url': f"https://musicbrainz.org/artist/{artist.get('id', '')}"
            }
            
            # Parse life span dates
            life_span = artist.get('life-span', {})
            if life_span:
                begin = life_span.get('begin', '')
                end = life_span.get('end', '')
                
                if begin and len(begin) >= 4:
                    try:
                        artist_info['birth_year'] = int(begin[:4])
                    except ValueError:
                        pass
                
                if end and len(end) >= 4:
                    try:
                        artist_info['death_year'] = int(end[:4])
                    except ValueError:
                        pass
            
            results['artists'].append(artist_info)
        
        # Find best match
        if results['artists']:
            results['best_match'] = self._find_best_artist_match(results['artists'], artist_name)
        
        return results
    
    def _find_best_work_match(self, works: List[Dict[str, Any]], target_title: str, target_composer: str) -> Dict[str, Any]:
        """Find the best matching work"""
        if not works:
            return None
        
        def score_work(work):
            score = 0
            work_title = work.get('title', '').lower()
            
            # Title similarity
            if target_title.lower() in work_title or work_title in target_title.lower():
                score += 50
            
            # Composer similarity
            target_composer_lower = target_composer.lower()
            for composer in work.get('composers', []):
                composer_name = composer.get('name', '').lower()
                if target_composer_lower in composer_name or composer_name in target_composer_lower:
                    score += 40
                    break
            
            # Prefer works with more metadata
            if work.get('composers'):
                score += 10
            if work.get('tags'):
                score += 5
            
            return score
        
        return max(works, key=score_work)
    
    def _find_best_artist_match(self, artists: List[Dict[str, Any]], target_name: str) -> Dict[str, Any]:
        """Find the best matching artist"""
        if not artists:
            return None
        
        def score_artist(artist):
            score = 0
            artist_name = artist.get('name', '').lower()
            target_lower = target_name.lower()
            
            # Exact match gets highest score
            if artist_name == target_lower:
                score += 100
            elif target_lower in artist_name or artist_name in target_lower:
                score += 50
            
            # Prefer artists with life span data
            if artist.get('death_year'):
                score += 20
            if artist.get('birth_year'):
                score += 10
            
            # Prefer artists with country information
            if artist.get('country'):
                score += 5
            
            return score
        
        return max(artists, key=score_artist)
    
    def _calculate_confidence(self, results: Dict[str, Any], title: str, composer: str) -> float:
        """Calculate confidence score for the results"""
        if not results.get('works'):
            return 0.0
        
        best_match = results.get('best_match')
        if not best_match:
            return 0.1
        
        confidence = 0.3  # Base confidence
        
        # Title match confidence
        if best_match.get('title', '').lower() == title.lower():
            confidence += 0.4
        elif title.lower() in best_match.get('title', '').lower():
            confidence += 0.2
        
        # Composer match confidence
        target_composer_lower = composer.lower()
        for composer_info in best_match.get('composers', []):
            composer_name = composer_info.get('name', '').lower()
            if target_composer_lower in composer_name:
                confidence += 0.3
                break
        
        return min(confidence, 1.0)
    
    async def get_work_details(self, work_id: str) -> APIResponse:
        """Get detailed information about a specific work"""
        await self._async_rate_limit()
        
        url = f"{self.BASE_URL}/work/{work_id}"
        params = {
            'fmt': 'json',
            'inc': 'artist-rels+recording-rels+tags+aliases'
        }
        
        try:
            client_session = await self.get_session(session)
            async with client_session.get(url, params=params) as response:
                response.raise_for_status()
                
                data = await response.json()
            
            return APIResponse(
                success=True,
                data=data,
                source_url=response.url,
                confidence=0.9
            )
            
        except aiohttp.ClientError as e:
            return APIResponse(
                success=False,
                error=f"MusicBrainz work details request failed: {str(e)}",
                source_url=url
            )
    
    async def search_books(self, title: str, author: str) -> APIResponse:
        """Search for books (not applicable for MusicBrainz, returns empty)"""
        return APIResponse(
            success=True,
            data={"works": [], "total_results": 0},
            confidence=0.0
        )
    
    async def get_item_details(self, item_identifier: str) -> APIResponse:
        """Get detailed information about a specific work"""
        return await self.get_work_details(item_identifier)