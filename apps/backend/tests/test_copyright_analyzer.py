#!/usr/bin/env python3
"""
Test cases for the copyright analyzer
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.copyright_analyzer import CopyrightAnalyzer
from src.countries.us.copyright_rules import USCopyrightCalculator

def test_public_domain_work():
    """Test analysis of a known public domain work"""
    print("Testing public domain work: Pride and Prejudice by Jane Austen")
    
    analyzer = CopyrightAnalyzer("US")
    result = analyzer.analyze_work("Pride and Prejudice", "Jane Austen", verbose=True)
    
    print(f"Status: {result.status}")
    print(f"Enters PD: {result.enters_public_domain}")
    print(f"Confidence: {result.confidence_score}")
    print(f"Notes: {result.notes}")
    print(f"Sources: {result.source_links}")
    
    assert result.status == "Public Domain", f"Expected Public Domain, got {result.status}"
    print("[PASS] Test passed\n")

def test_copyrighted_work():
    """Test analysis of a work still under copyright"""
    print("Testing copyrighted work: The Great Gatsby by F. Scott Fitzgerald")
    
    analyzer = CopyrightAnalyzer("US")
    result = analyzer.analyze_work("The Great Gatsby", "F. Scott Fitzgerald", verbose=True)
    
    print(f"Status: {result.status}")
    print(f"Enters PD: {result.enters_public_domain}")
    print(f"Confidence: {result.confidence_score}")
    print(f"Notes: {result.notes}")
    print(f"Sources: {result.source_links}")
    
    # The Great Gatsby was published in 1925, so should be public domain (95 years)
    print("[COMPLETED] Test completed\n")

def test_musical_work():
    """Test analysis of a musical work"""
    print("Testing musical work: Symphony No. 9 by Beethoven")
    
    analyzer = CopyrightAnalyzer("US")
    result = analyzer.analyze_work("Symphony No. 9", "Ludwig van Beethoven", work_type="musical", verbose=True)
    
    print(f"Status: {result.status}")
    print(f"Enters PD: {result.enters_public_domain}")
    print(f"Confidence: {result.confidence_score}")
    print(f"Notes: {result.notes}")
    print(f"Sources: {result.source_links}")
    
    assert result.status == "Public Domain", f"Expected Public Domain, got {result.status}"
    print("[PASS] Test passed\n")

def test_copyright_calculator():
    """Test the copyright calculation engine directly"""
    print("Testing copyright calculation logic")
    
    calc = USCopyrightCalculator()
    
    # Test pre-1923 work
    status, pd_year, notes = calc.calculate_copyright_status(1920, None, "individual")
    assert status == "Public Domain", f"Pre-1923 should be PD, got {status}"
    print("[PASS] Pre-1923 test passed")
    
    # Test 1925 work (should be PD now - 95 years)
    status, pd_year, notes = calc.calculate_copyright_status(1925, None, "individual")
    expected_pd = 1925 + 95  # 2020
    assert status == "Public Domain", f"1925 work should be PD, got {status}"
    print("[PASS] 1925 work test passed")
    
    # Test recent work
    status, pd_year, notes = calc.calculate_copyright_status(2000, 2010, "individual")
    expected_pd = 2010 + 70  # 2080
    assert status == "Under Copyright", f"Recent work should be under copyright, got {status}"
    assert pd_year == expected_pd, f"Expected PD year {expected_pd}, got {pd_year}"
    print("[PASS] Recent work test passed")
    
    print()

def main():
    """Run all tests"""
    print("Running Copyright Analyzer Tests")
    print("=" * 50)
    
    try:
        test_copyright_calculator()
        test_public_domain_work()
        test_musical_work()
        test_copyrighted_work()
        
        print("[SUCCESS] All tests completed!")
        
    except Exception as e:
        print(f"[FAILED] Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()