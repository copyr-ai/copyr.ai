from typing import Optional, Tuple
from datetime import datetime
from ...core.base_copyright_calculator import BaseCopyrightCalculator

class USCopyrightCalculator(BaseCopyrightCalculator):
    """
    Calculates public domain status based on US Copyright Law (Title 17)
    Implements rules from §304 and §305
    """
    
    def __init__(self):
        super().__init__("US")
    
    def calculate_copyright_status(
        self,
        publication_year: Optional[int],
        author_death_year: Optional[int],
        work_type: str = "individual",
        country: str = "US"
    ) -> Tuple[str, Optional[int], str]:
        """
        Calculate copyright status and public domain entry year
        
        Returns:
            Tuple of (status, enters_public_domain_year, explanation)
        """
        
        if not publication_year:
            return "Unknown", None, "Publication year unknown"
        
        # Pre-1923 works are in public domain
        if publication_year < 1923:
            return "Public Domain", 1923, f"Published before 1923. In public domain since 1923."
        
        # Works published 1923-1977 (different rules based on renewal)
        if 1923 <= publication_year <= 1977:
            if work_type == "individual":
                # Individual works: 95 years from publication
                pd_year = publication_year + 95
                if self.current_year >= pd_year:
                    return "Public Domain", pd_year, f"Published {publication_year}. 95-year term expired."
                else:
                    return "Under Copyright", pd_year, f"Published {publication_year}. Term is 95 years under §304; PD Jan 1, {pd_year} per §305."
            else:
                # Work for hire, anonymous, pseudonymous: 95 years from publication
                pd_year = publication_year + 95
                if self.current_year >= pd_year:
                    return "Public Domain", pd_year, f"Published {publication_year}. 95-year term expired."
                else:
                    return "Under Copyright", pd_year, f"Published {publication_year} as {work_type}. Term is 95 years; PD Jan 1, {pd_year}."
        
        # Works published 1978 and later (current copyright law)
        if publication_year >= 1978:
            if work_type == "individual" and author_death_year:
                # Individual works: life + 70 years
                pd_year = author_death_year + 70
                if self.current_year >= pd_year:
                    return "Public Domain", pd_year, f"Author died {author_death_year}. Life + 70 years expired."
                else:
                    return "Under Copyright", pd_year, f"Published {publication_year} by individual author. Author died {author_death_year}. Term is life + 70 years; PD Jan 1, {pd_year}."
            
            elif work_type in ["work_for_hire", "anonymous", "pseudonymous"]:
                # Work for hire: 95 years from publication or 120 years from creation (whichever is shorter)
                # Using publication date as proxy
                pd_year = publication_year + 95
                if self.current_year >= pd_year:
                    return "Public Domain", pd_year, f"Published {publication_year}. 95-year term expired."
                else:
                    return "Under Copyright", pd_year, f"Published {publication_year} as {work_type}. Term is 95 years from publication; PD Jan 1, {pd_year}."
            
            elif work_type == "individual" and not author_death_year:
                # Individual work but death year unknown - assume still under copyright
                estimated_pd = publication_year + 95  # Conservative estimate
                return "Under Copyright", estimated_pd, f"Published {publication_year} by individual author. Death year unknown; estimated PD {estimated_pd} (conservative)."
        
        return "Unknown", None, "Cannot determine copyright status with available information"
    
    def is_likely_public_domain(self, publication_year: Optional[int], author_death_year: Optional[int]) -> bool:
        """Quick check if work is likely in public domain"""
        if not publication_year:
            return False
        
        # Pre-1923 definitely public domain
        if publication_year < 1923:
            return True
        
        # If author died more than 70 years ago and work published after 1978
        if author_death_year and publication_year >= 1978:
            return (self.current_year - author_death_year) > 70
        
        # If published before 1928 (95 years ago)
        if publication_year <= (self.current_year - 95):
            return True
        
        return False
    
    def get_copyright_term_explanation(self, work_type: str, publication_year: Optional[int]) -> str:
        """Get explanation of copyright term rules"""
        if not publication_year:
            return "Cannot determine copyright term without publication year"
        
        if publication_year < 1923:
            return "Works published before 1923 are in the public domain"
        elif 1923 <= publication_year <= 1977:
            return "Works published 1923-1977: 95 years from publication (with renewal)"
        elif publication_year >= 1978:
            if work_type == "individual":
                return "Works by individual authors (1978+): Life of author + 70 years"
            else:
                return "Works for hire, anonymous, or pseudonymous (1978+): 95 years from publication or 120 years from creation (whichever is shorter)"
        
        return "Copyright term depends on publication date and work type"