#!/usr/bin/env python
"""
Final end-to-end test: crawl 3 URLs and export to Google Sheets
"""

import subprocess
import json
import os
from glob import glob
from datetime import datetime
import sys

sys.path.insert(0, 'c:/Users/tobia/Downloads/crawling-main')

SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbz39IOKmJgBdt4ZL2wW2eljPtdxeSrd52q0DJrXfgGnlaLQb5izqupTqSRwx1XvgqdM/exec'

print("="*70)
print("END-TO-END TEST: Crawl + Google Sheets Export")
print("="*70)

# Step 1: Crawl
print("\nStep 1: Running crawl for 3 URLs...")
result = subprocess.run([
    'python',
    'batch_crawler.py',
    'test data.xlsx',
    '--limit', '3',
    '--timeout', '15',
    '--robots-policy', 'ignore'
], capture_output=True, text=True)

print(result.stdout)
if result.returncode != 0:
    print(f"Crawl failed: {result.stderr}")
    sys.exit(1)

# Step 2: Find latest results file
print("\nStep 2: Finding latest results...")
results_files = sorted(glob('crawl_results_*.jsonl'))
if not results_files:
    print("✗ No results file found!")
    sys.exit(1)

latest_file = results_files[-1]
with open(latest_file, 'r', encoding='utf-8') as f:
    rows = [json.loads(line) for line in f if line.strip()]

print(f"✓ Found {len(rows)} results in {latest_file}")

# Step 3: Export to Google Sheets
print(f"\nStep 3: Exporting {len(rows)} rows to Google Sheets...")
from google_apps_script_integration import GoogleAppsScriptIntegration

integrator = GoogleAppsScriptIntegration(SCRIPT_URL)
summary = integrator.send_batch(rows)

# Step 4: Report
print("\n" + "="*70)
print("FINAL RESULTS")
print("="*70)
print(f"✓ Crawled {summary['total']} URLs")
print(f"✓ Exported {summary['successful']} rows to Google Sheets")
if summary['failed'] > 0:
    print(f"⚠ {summary['failed']} rows failed to export")
else:
    print(f"\n✓✓✓ SUCCESS: All {summary['total']} rows in your Google Sheet!")
    print(f"\nYou can now check your Google Sheet to see the crawled data:")
    print(f"Sheet ID: 1-CTG-z5o9XhLbGy-3SZr5bUF9X0rekKLV0Zw-7DX8xI")
