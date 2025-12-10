#!/usr/bin/env python
"""
Quick test: both single and batch sending
"""

import sys
sys.path.insert(0, 'c:/Users/tobia/Downloads/crawling-main')

from google_apps_script_integration import GoogleAppsScriptIntegration
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbz39IOKmJgBdt4ZL2wW2eljPtdxeSrd52q0DJrXfgGnlaLQb5izqupTqSRwx1XvgqdM/exec'

results = [
    {
        'url': 'https://example1.com',
        'email': 'info@example1.com',
        'inquiryFormUrl': 'https://example1.com/contact',
        'companyName': 'Example One',
        'industry': 'Tech',
        'httpStatus': 200,
        'robotsAllowed': True,
        'crawlStatus': 'success',
        'errorMessage': '',
        'lastCrawledAt': datetime.now().isoformat()
    },
    {
        'url': 'https://example2.com',
        'email': 'info@example2.com',
        'inquiryFormUrl': 'https://example2.com/contact',
        'companyName': 'Example Two',
        'industry': 'Finance',
        'httpStatus': 200,
        'robotsAllowed': True,
        'crawlStatus': 'success',
        'errorMessage': '',
        'lastCrawledAt': datetime.now().isoformat()
    }
]

print("Testing batch send (2 rows)...")
integrator = GoogleAppsScriptIntegration(SCRIPT_URL)
summary = integrator.send_batch(results)
print(f"\nSummary: {summary}")
print(f"Success: {summary['successful']}/{summary['total']} rows sent ✓" if summary['failed'] == 0 else f"Failures: {summary['failed']}")
