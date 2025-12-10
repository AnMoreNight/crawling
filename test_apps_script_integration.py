#!/usr/bin/env python
"""
Test script for Google Apps Script Integration
Tests the doPost endpoint with sample crawl results
"""

import sys
import json
import logging
from datetime import datetime

# Add parent directory to path so we can import our modules
sys.path.insert(0, '/c/Users/tobia/Downloads/crawling-main')

from google_apps_script_integration import GoogleAppsScriptIntegration

# Setup logging to see all messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Your Apps Script URL
SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbz39IOKmJgBdt4ZL2wW2eljPtdxeSrd52q0DJrXfgGnlaLQb5izqupTqSRwx1XvgqdM/exec'

# Sample test data (simulating crawl results)
TEST_RESULTS = [
    {
        'url': 'https://example.com',
        'email': 'info@example.com',
        'inquiryFormUrl': 'https://example.com/contact',
        'companyName': 'Example Inc',
        'industry': 'Technology',
        'httpStatus': 200,
        'robotsAllowed': True,
        'crawlStatus': 'success',
        'errorMessage': '',
        'lastCrawledAt': datetime.now().isoformat()
    },
    {
        'url': 'https://test-company.jp',
        'email': 'contact@test-company.jp',
        'inquiryFormUrl': 'https://test-company.jp/contact.html',
        'companyName': 'テスト会社',
        'industry': 'Manufacturing',
        'httpStatus': 200,
        'robotsAllowed': True,
        'crawlStatus': 'success',
        'errorMessage': '',
        'lastCrawledAt': datetime.now().isoformat()
    }
]

def test_payload_format():
    """Test the exact payload format the Apps Script expects"""
    print("\n" + "="*60)
    print("TEST 0: Testing raw payload format")
    print("="*60)
    
    import requests
    
    # Test 1: Single result with action format
    print("\nSending single result with 'addResult' action...")
    payload1 = {
        'action': 'addResult',
        'data': {
            'url': 'https://example.com',
            'email': 'info@example.com',
            'inquiryFormUrl': 'https://example.com/contact',
            'companyName': 'Example Inc',
            'industry': 'Technology',
            'httpStatus': 200,
            'robotsAllowed': True,
            'crawlStatus': 'success',
            'errorMessage': '',
            'lastCrawledAt': datetime.now().isoformat()
        }
    }
    
    try:
        r = requests.post(SCRIPT_URL, json=payload1, timeout=30)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Array of results
    print("\n\nSending array of results directly...")
    payload2 = [TEST_RESULTS[0]]
    
    try:
        r = requests.post(SCRIPT_URL, json=payload2, timeout=30)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

def test_single_result():
    """Test sending a single result"""
    print("\n" + "="*60)
    print("TEST 1: Sending single result")
    print("="*60)
    
    integrator = GoogleAppsScriptIntegration(SCRIPT_URL)
    result = TEST_RESULTS[0]
    
    success = integrator.send_result(result)
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
    return success

def test_batch():
    """Test sending multiple results"""
    print("\n" + "="*60)
    print("TEST 2: Sending batch of results")
    print("="*60)
    
    integrator = GoogleAppsScriptIntegration(SCRIPT_URL)
    summary = integrator.send_batch(TEST_RESULTS)
    
    if summary:
        print(f"\nBatch Summary:")
        print(f"  Total: {summary['total']}")
        print(f"  Successful: {summary['successful']}")
        print(f"  Failed: {summary['failed']}")
        return summary['failed'] == 0
    return False

if __name__ == '__main__':
    print("\n" + "█"*60)
    print("Google Apps Script Integration Test")
    print("█"*60)
    
    try:
        # Test payload formats
        test_payload_format()
        
        # Test single result
        single_ok = test_single_result()
        
        # Test batch
        batch_ok = test_batch()
        
        # Summary
        print("\n" + "="*60)
        print("FINAL RESULTS")
        print("="*60)
        print(f"Single result test: {'✓ PASS' if single_ok else '✗ FAIL'}")
        print(f"Batch test: {'✓ PASS' if batch_ok else '✗ FAIL'}")
        
        if single_ok and batch_ok:
            print("\n✓ All tests passed! Integration is working correctly.")
            sys.exit(0)
        else:
            print("\n✗ Some tests failed. Check the errors above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
