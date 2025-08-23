from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..models.work_record import WorkRecord

class BaseCountryAnalyzer(ABC):
    """
    Abstract base class for country-specific copyright analyzers
    """
    
    def __init__(self, country_code: str):
        self.country_code = country_code
        self.api_clients = {}
        self.copyright_calculator = None
        self.config = {}
    
    @abstractmethod
    async def analyze_work(
        self, 
        title: str, 
        author: str, 
        work_type: str = "auto",
        verbose: bool = False
    ) -> WorkRecord:
        """
        Analyze a work for copyright status
        
        Args:
            title: Title of the work
            author: Author/composer name
            work_type: Type of work ("literary", "musical", "auto")
            verbose: Whether to print detailed progress
            
        Returns:
            WorkRecord with copyright analysis
        """
        pass
    
    @abstractmethod
    async def analyze_batch(self, works: List[tuple], verbose: bool = False) -> List[WorkRecord]:
        """
        Analyze multiple works in batch
        
        Args:
            works: List of (title, author) tuples
            verbose: Whether to print progress
            
        Returns:
            List of WorkRecord objects
        """
        pass
    
    @abstractmethod
    def get_supported_apis(self) -> List[str]:
        """
        Get list of supported API sources for this country
        
        Returns:
            List of API source names
        """
        pass
    
    @abstractmethod
    def get_copyright_info(self) -> Dict[str, Any]:
        """
        Get information about this country's copyright system
        
        Returns:
            Dictionary with copyright system information
        """
        pass
    
    def get_country_code(self) -> str:
        """Get the country code for this analyzer"""
        return self.country_code
    
    def _log_verbose(self, message: str, verbose: bool = False):
        """Helper method for verbose logging"""
        if verbose:
            print(message)