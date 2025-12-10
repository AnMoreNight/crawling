# START HERE - Visual Guide

## For Non-Technical Users

### Option 1: One-Click Quick Test (Recommended First Time)
```
1. Double-click: QUICK_TEST.bat
2. Watch it run (takes 2-3 minutes)
3. Results auto-export to Google Sheets
4. Done! Check your Sheet for new rows
```

### Option 2: Full Menu (More Control)
```
1. Double-click: RUN_CRAWLER.bat
2. Choose option 1, 2, or 3
3. Wait for crawl to finish
4. Answer Y to export
5. Press Enter for default URL
6. Check Google Sheet
```

---

## What Each File Does

| File | Purpose | Use When |
|------|---------|----------|
| `QUICK_TEST.bat` | Auto crawl (10 URLs) + export | First time / quick test |
| `RUN_CRAWLER.bat` | Menu with 3 crawl options | Full control needed |
| `RUN_CRAWLER_QUICK.md` | How-to guide | Need instructions |
| `INTEGRATION_COMPLETE.md` | Feature summary | Want to know details |
| `IMPLEMENTATION_SUMMARY.md` | Technical summary | For developers |

---

## Your Google Sheet

All crawled data goes here:
```
https://docs.google.com/spreadsheets/d/1-CTG-z5o9XhLbGy-3SZr5bUF9X0rekKLV0Zw-7DX8xI
```

Columns added per URL:
- URL
- Email (if found)
- Contact Form URL
- Company Name
- Industry
- HTTP Status
- Robots Allowed
- Last Crawled At
- Crawl Status
- Error Message

---

## Troubleshooting

### "What if nothing happens?"
→ Open terminal and type: `python -c "import requests; print('OK')"`
→ Should print `OK` (means Python is working)

### "What if export fails?"
→ Check that your Google Sheet is shared with anyone who has the link
→ Or contact support with the error message

### "How do I know it worked?"
→ Check your Google Sheet
→ You should see new rows with the crawled URLs

### "How long does it take?"
→ 10 URLs = ~2-3 minutes
→ 50 URLs = ~5-10 minutes
→ 100+ URLs = longer (depends on page size/network)

---

## Getting Help

1. **Read**: `RUN_CRAWLER_QUICK.md` — most common questions answered there
2. **Check**: Google Sheet — verify rows were added
3. **Run**: `QUICK_TEST.bat` — test with 10 URLs first
4. **Review**: Error messages in terminal window

---

## Quick Facts

✓ **No credentials needed** — Apps Script URL is embedded  
✓ **Automatic export** — After crawl, you're asked to export  
✓ **Data goes to Google Sheets** — All results visible in one place  
✓ **Takes 2-3 minutes** — Small test crawl (10 URLs)  
✓ **Non-technical UI** — Just double-click and answer prompts  

---

## Ready?

**👉 Double-click `QUICK_TEST.bat` to start!**

(Or open `RUN_CRAWLER.bat` if you want to choose crawl size)

