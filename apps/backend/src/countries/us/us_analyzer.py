from typing import List, Dict, Any, Optional
from datetime import datetime

from ...core.base_analyzer import BaseCountryAnalyzer
from ...models.work_record import WorkRecord
from ...utils.metadata_normalizer import MetadataNormalizer
from .copyright_rules import USCopyrightCalculator
from .api_clients.library_of_congress import LibraryOfCongressClient
from .api_clients.hathitrust import HathiTrustClient
from .api_clients.musicbrainz import MusicBrainzClient
from . import config

class USAnalyzer(BaseCountryAnalyzer):
    """
    US-specific copyright analyzer
    """
    
    def __init__(self):
        super().__init__("US")
        
        # Initialize configuration
        self.config = config
        
        # Initialize copyright calculator
        self.copyright_calculator = USCopyrightCalculator()
        
        # Initialize API clients
        self.api_clients = {
            'library_of_congress': LibraryOfCongressClient(
                rate_limit_delay=config.get_api_config('library_of_congress').get('rate_limit_delay', 1.0)
            ),
            'hathitrust': HathiTrustClient(
                rate_limit_delay=config.get_api_config('hathitrust').get('rate_limit_delay', 1.0)
            ),
            'musicbrainz': MusicBrainzClient(
                rate_limit_delay=config.get_api_config('musicbrainz').get('rate_limit_delay', 1.1)
            )
        }
        
        # Initialize metadata normalizer
        self.normalizer = MetadataNormalizer()
    
    def analyze_work(
        self, 
        title: str, 
        author: str, 
        work_type: str = "auto",
        verbose: bool = False
    ) -> WorkRecord:
        """
        Analyze a work for copyright status using US-specific logic
        """
        self._log_verbose(f"Analyzing: '{title}' by {author}", verbose)
        self._log_verbose("=" * 50, verbose)
        
        # Step 1: Query Library of Congress
        self._log_verbose("1. Querying Library of Congress...", verbose)
        loc_response = self.api_clients['library_of_congress'].search_books(title, author)
        
        if verbose and loc_response.success:
            total_results = loc_response.data.get('total_results', 0) if loc_response.data else 0
            self._log_verbose(f"   Found {total_results} results", verbose)
        elif verbose:
            self._log_verbose(f"   Error: {loc_response.error}", verbose)
        
        # Step 2: Try HathiTrust with OCLC from LOC
        hathi_response = None
        if loc_response.success and loc_response.data:
            best_match = loc_response.data.get('best_match')
            if best_match:
                oclc_number = self.api_clients['hathitrust'].extract_identifier_from_metadata(best_match)
                if oclc_number:
                    self._log_verbose(f"2. Querying HathiTrust with OCLC: {oclc_number}...", verbose)
                    hathi_response = self.api_clients['hathitrust'].get_volume_brief_by_identifier('oclc', oclc_number)
                    if verbose and hathi_response.success:
                        rights = hathi_response.data.get('rights_summary', {}).get('most_common_rights', 'unknown') if hathi_response.data else 'unknown'
                        self._log_verbose(f"   Rights status: {rights}", verbose)
        
        if not hathi_response and verbose:
            self._log_verbose("2. Skipping HathiTrust (no OCLC found)", verbose)
        
        # Step 3: Query MusicBrainz for works (if musical/auto) and always for artist details
        musicbrainz_response = None
        musicbrainz_artist_response = None
        
        if work_type in ["musical", "auto"]:
            self._log_verbose("3. Querying MusicBrainz for musical works...", verbose)
            musicbrainz_response = self.api_clients['musicbrainz'].search_works(title, author)
            
            if verbose and musicbrainz_response.success:
                works_count = len(musicbrainz_response.data.get('works', []) if musicbrainz_response.data else [])
                self._log_verbose(f"   Found {works_count} musical works", verbose)
        elif verbose:
            self._log_verbose("3. Skipping MusicBrainz works (literary work)", verbose)
        
        # Always query MusicBrainz for artist details to get death dates (even for literary works)
        self._log_verbose("4. Querying MusicBrainz for artist details...", verbose)
        musicbrainz_artist_response = self.api_clients['musicbrainz'].search_artists(author)
        if verbose and musicbrainz_artist_response.success:
            best_artist = musicbrainz_artist_response.data.get('best_match') if musicbrainz_artist_response.data else None
            if best_artist and best_artist.get('death_year'):
                self._log_verbose(f"   Found death year: {best_artist['death_year']}", verbose)
        
        # Step 4: Merge and normalize metadata
        self._log_verbose("5. Merging metadata from sources...", verbose)
        merged_metadata = self.normalizer.merge_api_responses(
            loc_response=loc_response,
            hathi_response=hathi_response,
            musicbrainz_response=musicbrainz_response,
            musicbrainz_artist_response=musicbrainz_artist_response,
            search_title=title,
            search_author=author,
            search_work_type=work_type
        )
        
        if verbose:
            self._log_verbose(f"   Normalized title: {merged_metadata.get('title', 'Unknown')}", verbose)
            self._log_verbose(f"   Normalized author: {merged_metadata.get('author_name', 'Unknown')}", verbose)
            self._log_verbose(f"   Publication year: {merged_metadata.get('publication_year', 'Unknown')}", verbose)
            self._log_verbose(f"   Death year: {merged_metadata.get('author_death_year', 'Unknown')}", verbose)
        
        # Step 5: Calculate copyright status
        self._log_verbose("6. Calculating copyright status...", verbose)
        status, pd_year, explanation = self.copyright_calculator.calculate_copyright_status(
            publication_year=merged_metadata.get('publication_year'),
            author_death_year=merged_metadata.get('author_death_year'),
            work_type=merged_metadata.get('copyright_type', 'individual'),  # Use copyright_type for legal analysis
            country=merged_metadata.get('country', 'US')
        )
        
        copyright_analysis = {
            'status': status,
            'enters_public_domain': pd_year,
            'notes': explanation
        }
        
        if verbose:
            self._log_verbose(f"   Status: {status}", verbose)
            if pd_year:
                self._log_verbose(f"   Enters public domain: {pd_year}", verbose)
            self._log_verbose(f"   Explanation: {explanation}", verbose)
        
        # Step 6: Create final work record
        work_record = self.normalizer.create_work_record(
            title=title,
            author=author,
            merged_metadata=merged_metadata,
            copyright_analysis=copyright_analysis
        )
        
        return work_record
    
    def analyze_batch(self, works: List[tuple], verbose: bool = False) -> List[WorkRecord]:
        """
        Analyze multiple works in batch
        """
        results = []
        
        for i, (title, author) in enumerate(works, 1):
            if verbose:
                print(f"\n[{i}/{len(works)}] Processing: {title} by {author}")
            
            try:
                result = self.analyze_work(title, author, verbose=verbose)
                results.append(result)
            except Exception as e:
                if verbose:
                    print(f"Error analyzing {title}: {e}")
                # Create error record
                error_record = WorkRecord(
                    title=title,
                    author_name=author,
                    status="Unknown",
                    notes=f"Analysis failed: {str(e)}"
                )
                results.append(error_record)
        
        return results
    
    def get_supported_apis(self) -> List[str]:
        """Get list of supported API sources"""
        return list(self.api_clients.keys())
    
    def get_copyright_info(self) -> Dict[str, Any]:
        """Get information about US copyright system"""
        info = config.COPYRIGHT_INFO.copy()
        info.update(self.copyright_calculator.get_country_info())
        return info