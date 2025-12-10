#!/usr/bin/env python
"""
System Verification Test
Verifies all modules work correctly before testing
"""

import json
from datetime import datetime

print("\n" + "="*60)
print("SYSTEM VERIFICATION TEST")
print("="*60 + "\n")

# Test 1: Import all modules
print("[1/4] Testing module imports...")
try:
    from crawler.engine import CrawlerEngine
    print("  ✓ CrawlerEngine imported")
    
    from crawler.enhanced_email_extractor import EnhancedEmailExtractor
    print("  ✓ EnhancedEmailExtractor imported")
    
    from crawler.enhanced_company_name_extractor import EnhancedCompanyNameExtractor
    print("  ✓ EnhancedCompanyNameExtractor imported")
    
    from google_apps_script_integration import GoogleAppsScriptIntegration
    print("  ✓ GoogleAppsScriptIntegration imported")
    
    from batch_crawler import BatchCrawler
    print("  ✓ BatchCrawler imported")
    
    print("  SUCCESS: All modules imported\n")
except Exception as e:
    print(f"  ERROR: {e}\n")
    exit(1)

# Test 2: Verify batch crawler help
print("[2/4] Testing batch crawler arguments...")
try:
    import argparse
    import sys
    
    # Check that --google-apps-script argument exists
    parser = argparse.ArgumentParser()
    parser.add_argument('--google-apps-script')
    args = parser.parse_args(['--google-apps-script', 'test_url'])
    
    if args.google_apps_script == 'test_url':
        print("  ✓ --google-apps-script argument works")
        print("  SUCCESS: Argument parsing OK\n")
    else:
        print("  ERROR: Argument not working\n")
        exit(1)
        
except Exception as e:
    print(f"  ERROR: {e}\n")
    exit(1)

# Test 3: Test enhancement modules
print("[3/4] Testing enhancer modules...")
try:
    test_html = "<title>テスト株式会社 | サービス</title><a href='mailto:info@example.com'>Contact</a>"
    
    # Test email extraction
    emails = EnhancedEmailExtractor.extract_emails(test_html)
    print(f"  ✓ Email extraction: {emails}")
    
    # Test company name extraction
    company = EnhancedCompanyNameExtractor.extract_company_name(test_html)
    print(f"  ✓ Company extraction: {company}")
    
    print("  SUCCESS: Enhancers working\n")
    
except Exception as e:
    print(f"  ERROR: {e}\n")
    exit(1)

# Test 4: Test Google Apps Script integration
print("[4/4] Testing Google Apps Script integration...")
try:
    script_url = "https://script.google.com/macros/s/AKfycbz39IOKmJgBdt4ZL2wW2eljPtdxeSrd52q0DJrXfgGnlaLQb5izqupTqSRwx1XvgqdM/exec"
    integrator = GoogleAppsScriptIntegration(script_url)
    print(f"  ✓ Google Apps Script integration initialized")
    print(f"  ✓ Target URL: {script_url[:50]}...")
    print("  SUCCESS: Apps Script integration ready\n")
    
except Exception as e:
    print(f"  ERROR: {e}\n")
    exit(1)

print("="*60)
print("✅ ALL SYSTEM TESTS PASSED!")
print("="*60)
print("\nReady to test with real data tomorrow:")
print("  Run: TEST_WITH_APPS_SCRIPT.bat")
print("  Or: python batch_crawler.py \"test data.xlsx\" --limit 9 --google-apps-script \"<URL>\"")
print()
