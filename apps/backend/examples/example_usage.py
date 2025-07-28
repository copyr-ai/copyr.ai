#!/usr/bin/env python3
"""
Example usage of the copyright analyzer

This script demonstrates how to use the copyright analyzer
to analyze various types of works.
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.copyright_analyzer import CopyrightAnalyzer

def example_single_analysis():
    """Example of analyzing a single work"""
    print("="*60)
    print("EXAMPLE 1: Single Work Analysis")
    print("="*60)
    
    analyzer = CopyrightAnalyzer("US")
    
    # Analyze a classic work
    result = analyzer.analyze_work(
        title="The Great Gatsby",
        author="F. Scott Fitzgerald",
        verbose=True
    )
    
    print("\nRESULT:")
    print(json.dumps(result.to_dict(), indent=2))

def example_musical_work():
    """Example of analyzing a musical work"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Musical Work Analysis")
    print("="*60)
    
    analyzer = CopyrightAnalyzer("US")
    
    # Analyze a classical composition
    result = analyzer.analyze_work(
        title="Symphony No. 9",
        author="Ludwig van Beethoven",
        work_type="musical",
        verbose=True
    )
    
    print("\nRESULT:")
    print(json.dumps(result.to_dict(), indent=2))

def example_batch_analysis():
    """Example of batch analysis"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Batch Analysis")
    print("="*60)
    
    analyzer = CopyrightAnalyzer("US")
    
    # List of works to analyze
    works = [
        ("Pride and Prejudice", "Jane Austen"),
        ("The Adventures of Tom Sawyer", "Mark Twain"),
        ("Dracula", "Bram Stoker"),
        ("The Picture of Dorian Gray", "Oscar Wilde")
    ]
    
    results = analyzer.analyze_batch(works, verbose=True)
    
    print("\nBATCH RESULTS SUMMARY:")
    print("-" * 40)
    for result in results:
        print(f"'{result.title}' by {result.author_name}: {result.status}")
        if result.enters_public_domain:
            print(f"  - Enters PD: {result.enters_public_domain}")
        print(f"  - Confidence: {result.confidence_score:.2f}")
        print()

def example_output_formats():
    """Example of different output formats"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Output Formats")
    print("="*60)
    
    analyzer = CopyrightAnalyzer("US")
    
    result = analyzer.analyze_work("Frankenstein", "Mary Shelley")
    
    print("JSON Output:")
    print(json.dumps(result.to_dict(), indent=2))
    
    print("\nSummary Format:")
    print(f"Work: {result.title}")
    print(f"Author: {result.author_name}")
    print(f"Publication Year: {result.publication_year or 'Unknown'}")
    print(f"Author Death Year: {result.year_of_death or 'Unknown'}")
    print(f"Copyright Status: {result.status}")
    if result.enters_public_domain:
        print(f"Enters Public Domain: {result.enters_public_domain}")
    print(f"Confidence Score: {result.confidence_score:.2f}")
    print(f"Notes: {result.notes}")
    if result.source_links:
        print("Sources:")
        for source, url in result.source_links.items():
            print(f"  - {source}: {url}")

def main():
    """Run all examples"""
    print("COPYR.AI COPYRIGHT ANALYZER - EXAMPLES")
    print("This demonstrates the MVP functionality for US literary and musical works")
    
    try:
        example_single_analysis()
        example_musical_work()
        example_batch_analysis()
        example_output_formats()
        
        print(f"\n{'='*60}")
        print("EXAMPLES COMPLETED SUCCESSFULLY!")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()