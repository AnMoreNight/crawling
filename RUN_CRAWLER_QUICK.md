# RUN_CRAWLER - Quick Reference

This file explains the single, simple runner `RUN_CRAWLER.bat` and how it automatically exports crawl results to Google Sheets.

## How It Works (Simple)

1. **Double-click `RUN_CRAWLER.bat`** to see a menu.
2. **Choose a crawl option**:
   - Option 1: Test crawl (10 URLs) — fast, good for testing
   - Option 2: Crawl with limit (50 URLs)
   - Option 3: Crawl all URLs
3. **Wait for crawl to finish** — a `crawl_results.jsonl` file will be created.
4. **Choose to export** — the script asks: "Export results to Google Sheets now? (Y/n)"
5. **Pick export method**:
   - If you have `credentials.json` (service account), you can use it
   - Otherwise, use the Google Apps Script URL (press Enter to use the embedded default)
6. **Done!** Check your Google Sheet for the new rows.

## Two Export Options

### Option A: Service Account (credentials.json)
- Requires: `credentials.json` file in the project folder
- How: Share your Google Sheet with the service account email
- Pro: No URL needed, works offline after setup
- Con: Need to set up service account first

### Option B: Google Apps Script (URL-based)
- Requires: Nothing! Uses an embedded default URL
- How: Script POSTs results directly to your deployed Apps Script
- Pro: Zero local credential management
- Con: Needs working deployment of the Apps Script
- Default URL (embedded): `https://script.google.com/macros/s/AKfycbz39IOKmJgBdt4ZL2wW2eljPtdxeSrd52q0DJrXfgGnlaLQb5izqupTqSRwx1XvgqdM/exec`

**Recommended**: Apps Script mode (no local files needed, just double-click and go!)

## What Gets Exported

Each crawled URL becomes one row in your Google Sheet with:
- **URL**: The crawled page
- **Email**: Extracted business email (if found)
- **Inquiry Form URL**: Contact form URL (if found)
- **Company Name**: Business name (if found)
- **Industry**: Extracted industry (if detected)
- **HTTP Status**: Response code (200, 404, etc.)
- **Robots Allowed**: Whether robots.txt allowed crawling
- **Last Crawled At**: Timestamp
- **Crawl Status**: success/error
- **Error Message**: Any errors that occurred

---

That's it! One simple runner that handles everything.
