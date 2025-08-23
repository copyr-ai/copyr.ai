#!/usr/bin/env python3
"""
Copyright Analyzer - Country-aware orchestrator for copyr.ai

Queries multiple APIs to gather metadata about literary and musical works,
then calculates public domain status based on country-specific copyright law.

Usage:
    python copyright_analyzer.py "The Great Gatsby" "F. Scott Fitzgerald"
    python copyright_analyzer.py "Symphony No. 9" "Ludwig van Beethoven" --work-type musical --country US
"""

import json
import sys
from typing import Optional, Dict, Any, List
import argparse
from datetime import datetime
import importlib

from .models.work_record import WorkRecord
from .countries import COUNTRY_REGISTRY, get_supported_countries, is_country_supported, get_country_info

class CopyrightAnalyzer:
    """
    Country-aware main orchestrator for copyright analysis
    """
    
    def __init__(self, country: str = "US"):
        self.country = country.upper()
        
        # Validate country support
        if not is_country_supported(self.country):
            supported = ", ".join(get_supported_countries())
            raise ValueError(f"Country '{self.country}' not supported. Supported countries: {supported}")
        
        # Load country-specific analyzer
        self.country_analyzer = self._load_country_analyzer()
    
    def _load_country_analyzer(self):
        """Dynamically load the country-specific analyzer"""
        country_info = get_country_info(self.country)
        if not country_info:
            raise ValueError(f"No configuration found for country: {self.country}")
        
        # Import the analyzer class
        analyzer_module_path, analyzer_class_name = country_info['analyzer_class'].rsplit('.', 1)
        analyzer_module = importlib.import_module(f".{analyzer_module_path}", package=__package__)
        analyzer_class = getattr(analyzer_module, analyzer_class_name)
        
        return analyzer_class()
    
    async def analyze_work(
        self, 
        title: str, 
        author: str, 
        work_type: str = "auto",
        verbose: bool = False,
        country: Optional[str] = None
    ) -> WorkRecord:
        """
        Analyze a work for copyright status
        
        Args:
            title: Title of the work
            author: Author/composer name
            work_type: "literary", "musical", or "auto" to detect
            verbose: Print detailed progress information
            country: Override the analyzer's default country
            
        Returns:
            WorkRecord with copyright analysis
        """
        # If country override is provided, create new analyzer
        if country and country.upper() != self.country:
            temp_analyzer = CopyrightAnalyzer(country)
            return await temp_analyzer.analyze_work(title, author, work_type, verbose)
        
        # Use the country-specific analyzer
        return await self.country_analyzer.analyze_work(title, author, work_type, verbose)
    
    def analyze_batch(
        self, 
        works: List[tuple], 
        verbose: bool = False,
        country: Optional[str] = None
    ) -> List[WorkRecord]:
        """
        Analyze multiple works in batch
        
        Args:
            works: List of (title, author) tuples
            verbose: Print progress information
            country: Override the analyzer's default country
            
        Returns:
            List of WorkRecord objects
        """
        # If country override is provided, create new analyzer
        if country and country.upper() != self.country:
            temp_analyzer = CopyrightAnalyzer(country)
            return temp_analyzer.analyze_batch(works, verbose)
        
        # Use the country-specific analyzer
        return self.country_analyzer.analyze_batch(works, verbose)
    
    def get_supported_apis(self) -> List[str]:
        """Get list of supported API sources for current country"""
        return self.country_analyzer.get_supported_apis()
    
    def get_copyright_info(self) -> Dict[str, Any]:
        """Get information about current country's copyright system"""
        return self.country_analyzer.get_copyright_info()
    
    def get_country(self) -> str:
        """Get the current country code"""
        return self.country
    
    @staticmethod
    def get_all_supported_countries() -> List[str]:
        """Get list of all supported countries"""
        return get_supported_countries()
    
    @staticmethod
    def get_country_information(country_code: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific country"""
        return get_country_info(country_code)

def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description="Analyze copyright status of literary and musical works",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  python copyright_analyzer.py "The Great Gatsby" "F. Scott Fitzgerald"
  python copyright_analyzer.py "Symphony No. 9" "Beethoven" --work-type musical
  python copyright_analyzer.py "Pride and Prejudice" "Jane Austen" --verbose --country US

Supported countries: {", ".join(get_supported_countries())}
        """
    )
    
    parser.add_argument("title", nargs='?', help="Title of the work")
    parser.add_argument("author", nargs='?', help="Author or composer name")
    parser.add_argument(
        "--work-type", 
        choices=["literary", "musical", "auto"], 
        default="auto",
        help="Type of work (default: auto-detect)"
    )
    parser.add_argument(
        "--country", "-c",
        choices=get_supported_countries(),
        default="US",
        help="Country for copyright analysis (default: US)"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true",
        help="Print detailed analysis progress"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for JSON results (default: stdout)"
    )
    parser.add_argument(
        "--batch",
        help="JSON file with list of works to analyze in batch"
    )
    parser.add_argument(
        "--list-countries",
        action="store_true",
        help="List all supported countries and exit"
    )
    
    args = parser.parse_args()
    
    # Handle list countries option
    if args.list_countries:
        print("Supported countries:")
        for country_code in get_supported_countries():
            country_info = get_country_info(country_code)
            print(f"  {country_code}: {country_info['name']}")
        sys.exit(0)
    
    # Validate required arguments
    if not args.list_countries and (not args.title or not args.author):
        parser.error("title and author are required unless using --list-countries")
    
    try:
        analyzer = CopyrightAnalyzer(args.country)
        
        if args.batch:
            # Batch processing
            with open(args.batch, 'r', encoding='utf-8') as f:
                works_data = json.load(f)
            
            works = [(work['title'], work['author']) for work in works_data]
            results = analyzer.analyze_batch(works, verbose=args.verbose)
            
            # Convert to JSON
            json_results = [result.to_dict() for result in results]
        else:
            # Single work analysis
            result = analyzer.analyze_work(
                title=args.title,
                author=args.author,
                work_type=args.work_type,
                verbose=args.verbose
            )
            
            json_results = result.to_dict()
        
        # Output results
        json_output = json.dumps(json_results, indent=2, ensure_ascii=False)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(json_output)
            if args.verbose:
                print(f"\nResults saved to: {args.output}")
        else:
            print("\n" + "="*50)
            print("ANALYSIS RESULTS:")
            print("="*50)
            print(json_output)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()