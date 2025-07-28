from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

class BaseCopyrightCalculator(ABC):
    """
    Abstract base class for copyright calculation engines
    Each country will implement its own copyright rules
    """
    
    def __init__(self, country_code: str):
        self.country_code = country_code
        self.current_year = datetime.now().year
    
    @abstractmethod
    def calculate_copyright_status(
        self,
        publication_year: Optional[int],
        author_death_year: Optional[int],
        work_type: str = "individual",
        **kwargs
    ) -> Tuple[str, Optional[int], str]:
        """
        Calculate copyright status and public domain entry year
        
        Args:
            publication_year: Year the work was published
            author_death_year: Year the author died
            work_type: Type of work (individual, work_for_hire, anonymous, etc.)
            **kwargs: Additional country-specific parameters
            
        Returns:
            Tuple of (status, enters_public_domain_year, explanation)
        """
        pass
    
    @abstractmethod
    def is_likely_public_domain(
        self, 
        publication_year: Optional[int], 
        author_death_year: Optional[int],
        **kwargs
    ) -> bool:
        """
        Quick check if work is likely in public domain
        
        Args:
            publication_year: Year the work was published
            author_death_year: Year the author died
            **kwargs: Additional country-specific parameters
            
        Returns:
            True if likely in public domain, False otherwise
        """
        pass
    
    @abstractmethod
    def get_copyright_term_explanation(
        self, 
        work_type: str, 
        publication_year: Optional[int],
        **kwargs
    ) -> str:
        """
        Get explanation of copyright term rules for this country
        
        Args:
            work_type: Type of work
            publication_year: Year of publication
            **kwargs: Additional parameters
            
        Returns:
            Human-readable explanation of copyright term rules
        """
        pass
    
    def get_country_info(self) -> Dict[str, Any]:
        """
        Get information about this country's copyright system
        
        Returns:
            Dictionary with country copyright information
        """
        return {
            "country_code": self.country_code,
            "current_year": self.current_year,
            "calculator_class": self.__class__.__name__
        }
    
    def _validate_years(self, publication_year: Optional[int], author_death_year: Optional[int]) -> bool:
        """
        Basic validation of year inputs
        
        Args:
            publication_year: Year of publication
            author_death_year: Year of death
            
        Returns:
            True if years are valid, False otherwise
        """
        if publication_year is not None:
            if publication_year < 1400 or publication_year > self.current_year + 5:
                return False
        
        if author_death_year is not None:
            if author_death_year < 1400 or author_death_year > self.current_year:
                return False
            
            # Death year should not be before publication year (with some tolerance)
            if publication_year and author_death_year < publication_year - 100:
                return False
        
        return True