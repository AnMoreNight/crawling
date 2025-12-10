#!/usr/bin/env python
"""
Simple test: send array directly
"""

import requests
from datetime import datetime
import json

SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbz39IOKmJgBdt4ZL2wW2eljPtdxeSrd52q0DJrXfgGnlaLQb5izqupTqSRwx1XvgqdM/exec'

test_row = {
    'url': 'https://test-payload.example.com',
    'email': 'test@example.com',
    'inquiryFormUrl': 'https://test-payload.example.com/contact',
    'companyName': 'Test Payload Company',
    'industry': 'Testing',
    'httpStatus': 200,
    'robotsAllowed': True,
    'crawlStatus': 'success',
    'errorMessage': '',
    'lastCrawledAt': datetime.now().isoformat()
}

# Send array directly
print("Sending array with 1 row directly...")
payload = [test_row]

try:
    r = requests.post(SCRIPT_URL, json=payload, timeout=20)
    print(f"Status: {r.status_code}")
    try:
        response_data = r.json()
        print(f"Response (JSON): {json.dumps(response_data, indent=2)}")
    except:
        print(f"Response (text): {r.text[:800]}")
except requests.Timeout:
    print("Request timed out after 20 seconds")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
