#!/usr/bin/env python
"""
Export the latest crawl results to Google Sheets
"""

import sys
import json
import os
from glob import glob
from datetime import datetime

sys.path.insert(0, 'c:/Users/tobia/Downloads/crawling-main')
from google_apps_script_integration import send_crawl_results_to_apps_script

# Find the latest results file
results_files = sorted(glob('crawl_results_*.jsonl'))
if not results_files:
    print("✗ No crawl results files found!")
    sys.exit(1)

latest_file = results_files[-1]
print(f"Latest results file: {latest_file}")
print(f"File size: {os.path.getsize(latest_file)} bytes")

# Read and display sample rows
print("\nSample rows from file:")
with open(latest_file, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 3:
            break
        try:
            row = json.loads(line)
            print(f"  [{i+1}] {row.get('url', 'N/A')} → {row.get('inquiryFormUrl', 'N/A')}")
        except:
            pass

# Export to Apps Script
SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbz39IOKmJgBdt4ZL2wW2eljPtdxeSrd52q0DJrXfgGnlaLQb5izqupTqSRwx1XvgqdM/exec'

print(f"\nExporting to Google Sheets via Apps Script...")
print(f"Script URL: {SCRIPT_URL}")

summary = send_crawl_results_to_apps_script(latest_file, SCRIPT_URL)

if summary:
    print(f"\n✓ Export Complete!")
    print(f"  Total rows: {summary['total']}")
    print(f"  Successful: {summary['successful']}")
    print(f"  Failed: {summary['failed']}")
    if summary['failed'] == 0:
        print(f"\n✓✓✓ All {summary['total']} rows successfully exported to Google Sheets!")
    else:
        print(f"\n⚠ {summary['failed']} rows failed to export")
else:
    print("✗ Export failed!")
    sys.exit(1)
