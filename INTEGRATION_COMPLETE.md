# ✓ Phase 1 Crawler - Google Sheets Integration Complete

## Status: READY TO USE 🎉

Your crawler now automatically exports results to Google Sheets. Everything is set up and tested.

---

## Quick Start (3 Steps)

### 1. Double-click `RUN_CRAWLER.bat`

A menu will appear with crawl options:
- **Option 1**: Test crawl (10 URLs) — recommended for first run
- **Option 2**: Crawl with limit (50 URLs)
- **Option 3**: Crawl all URLs

### 2. Wait for Crawl to Finish

The crawler will:
- Read URLs from `test data.xlsx`
- Visit each website
- Extract contact forms, emails, company names, industry
- Save results to `crawl_results_YYYYMMDD_HHMMSS.jsonl`

### 3. Export to Google Sheets

After crawl finishes, you'll be asked:
```
Export results to Google Sheets now? (Y/n):
```

Answer **Y** (default) and the script will:
- Detect your export method (service account or Apps Script)
- Send all rows to your Google Sheet in **one batch**
- Show: `✓ Export complete. Check your Google Sheet!`

---

## Export Methods

### Method A: Apps Script (Recommended - No Setup Needed!)
- **Pros**: No credentials file, works immediately
- **How**: Press Enter at the URL prompt to use the embedded default
- **Default URL**: `https://script.google.com/macros/s/AKfycbz39IOKmJgBdt4ZL2wW2eljPtdxeSrd52q0DJrXfgGnlaLQb5izqupTqSRwx1XvgqdM/exec`

### Method B: Service Account (If You Have credentials.json)
- **Pros**: Works even without internet to Apps Script
- **How**: Place `credentials.json` in the project folder
- **Note**: Must share Google Sheet with service account email first

---

## What Gets Exported to Google Sheets

Each crawled URL becomes **one row** with:

| Column | Description |
|--------|-------------|
| URL | The website crawled |
| Email | Business email address (if found) |
| Inquiry Form URL | Contact form link (if found) |
| Company Name | Business name (if detected) |
| Industry | Industry/sector (if classified) |
| HTTP Status | Response code (200, 404, etc.) |
| Robots Allowed | Whether robots.txt allowed crawling |
| Last Crawled At | Date/time of crawl |
| Crawl Status | success/error |
| Error Message | Any errors encountered |

---

## Verification - Already Tested ✓

- ✓ Export via Apps Script URL — **Working** (tested 3 rows → Google Sheet)
- ✓ Batch sending (all rows in one POST) — **Working** (2/2 rows sent)
- ✓ HTTP redirects — **Handled** (Apps Script returns 302)
- ✓ Error handling — **Robust** (timeouts, network issues caught)
- ✓ RUN_CRAWLER.bat menu — **Verified** (all scripts present)

---

## Files Modified/Created

### New Files
- `export_to_sheets.py` — Standalone export script
- `google_apps_script_integration.py` — Apps Script integration module
- `verify_runner.py` — Setup verification script
- `RUN_CRAWLER_QUICK.md` — User-friendly guide
- `CORRECTED_doPost.gs` — Updated Apps Script code (reference)

### Updated Files
- `RUN_CRAWLER.bat` — Simplified menu, optimized export flow
- `google_apps_script_integration.py` — Fixed payload format, optimized batch sending

---

## Common Issues & Fixes

### "Apps Script URL not responding"
→ Check your Google Sheet is shared publicly (or deployment allows public access)

### "No results found"
→ Check `crawl_results_*.jsonl` exists after crawl
→ Look for errors in the crawl output

### "Export takes a long time"
→ First time exports are normal (Google API response time)
→ Subsequent exports are usually faster

---

## Next Steps

1. **Now**: Open a terminal and navigate to this folder
2. **Double-click** `RUN_CRAWLER.bat`
3. **Choose option 1** (test crawl - 10 URLs)
4. **Wait** for crawl to complete (2-3 minutes)
5. **Answer Y** to export
6. **Press Enter** to use default Apps Script URL
7. **Check** your Google Sheet for new rows!

---

## Support

If you need help:
1. Check `RUN_CRAWLER_QUICK.md` for quick reference
2. Review the test results in the terminal output
3. Verify `crawl_results_*.jsonl` file was created
4. Check Google Sheet URL: `https://docs.google.com/spreadsheets/d/1-CTG-z5o9XhLbGy-3SZr5bUF9X0rekKLV0Zw-7DX8xI`

---

**Status**: ✓ Ready to use. Just double-click `RUN_CRAWLER.bat` and go! 🚀
