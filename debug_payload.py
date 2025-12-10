#!/usr/bin/env python
"""
Direct test of Apps Script payload formats
"""

import requests
from datetime import datetime

SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbz39IOKmJgBdt4ZL2wW2eljPtdxeSrd52q0DJrXfgGnlaLQb5izqupTqSRwx1XvgqdM/exec'

test_row = {
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

print("="*70)
print("TEST: Sending array of rows directly (no action wrapper)")
print("="*70)
payload = [test_row]
print(f"\nPayload structure: Array with {len(payload)} item(s)")
print(f"Item 0: {list(test_row.keys())}")
r = requests.post(SCRIPT_URL, json=payload, timeout=30)
print(f"\nStatus: {r.status_code}")
print(f"Response: {r.text}")

print("\n" + "="*70)
print("TEST: Sending with action='addResult' wrapper")
print("="*70)
payload2 = {
    'action': 'addResult',
    'data': test_row
}
print(f"\nPayload structure: {list(payload2.keys())}")
print(f"data field type: dict with keys {list(payload2['data'].keys())}")
r2 = requests.post(SCRIPT_URL, json=payload2, timeout=30)
print(f"\nStatus: {r2.status_code}")
print(f"Response: {r2.text}")
