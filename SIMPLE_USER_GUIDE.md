# How to Use Phase 1 Crawler - Simple Edition

## For Non-Developers

You don't need to use the command line at all! Just double-click the .bat files.

---

## Option 1: Quick Test (Recommended Start)

**File:** `QUICK_TEST.bat`

**What it does:**
- Crawls 10 websites from your Excel file
- Takes about 1 minute
- Saves results locally

**How to use:**
1. Find `QUICK_TEST.bat` in the folder
2. Double-click it
3. Wait for it to finish
4. Press Enter

**Result:** You'll see the crawl progress and results on screen

---

## Option 2: Run Full Crawler

**File:** `RUN_FULL.bat`

**What it does:**
- Crawls ALL websites in your Excel file
- Saves all results to `crawl_results.jsonl`

**How to use:**
1. Find `RUN_FULL.bat` in the folder
2. Double-click it
3. Wait (time depends on number of URLs)
4. Press Enter

**Result:** All data saved to local file

---

## Option 3: Export to Google Sheets

**File:** `EXPORT_TO_SHEETS.bat`

**Prerequisites:**
- You need `credentials.json` file (one-time setup)
- See: `GOOGLE_SHEETS_SETUP.md` for how to get it

**How to use:**
1. Download `credentials.json` from Google Cloud (see setup guide)
2. Save it in this folder
3. Double-click `EXPORT_TO_SHEETS.bat`
4. Results appear in your Google Sheet automatically

---

## Option 4: Interactive Menu

**File:** `RUN_CRAWLER.bat`

**What it does:**
- Shows you a menu with options
- Choose what you want to do

**How to use:**
1. Double-click `RUN_CRAWLER.bat`
2. Choose option (1, 2, 3, or 4)
3. Press Enter
4. Wait for results

---

## Credentials Question

### Do I need credentials.json?

**Only if you want to export to Google Sheets automatically.**

- **Local only** (save results to your computer): NO credentials needed
- **Google Sheets export** (automatic to your Sheet): YES, need credentials

### Do I have to use JSON?

We offer **2 alternatives**:

#### Alternative 1: Google Apps Script (NO CREDENTIALS NEEDED!)
This is the **easiest** - no JSON file at all!

**Setup (one-time):**
1. Open your Google Sheet
2. Click: `Extensions` → `Apps Script`
3. Delete default code
4. Paste the code from: `apps_script_alternative.py`
5. Click `Deploy` → `New Deployment`
6. Choose: `Web app`
7. Execute as: `Me`
8. Allow access
9. Copy the deployment URL
10. Done! (No credentials file needed!)

**Usage:**
Just use the regular batch files - it sends data to your Sheet automatically!

#### Alternative 2: JSON Service Account (Current)
What we have now - most secure for production.

---

## Recommended Path for Non-Developers

### Step 1: Test It Works
```
Double-click: QUICK_TEST.bat
```
(Takes 1 minute)

### Step 2: Run Full Crawler
```
Double-click: RUN_FULL.bat
```
(Time depends on URLs)

### Step 3a: Option - Export to Google Sheets
If you want automatic export:
```
1. Follow GOOGLE_SHEETS_SETUP.md
2. Download credentials.json
3. Double-click: EXPORT_TO_SHEETS.bat
```

### Step 3b: Option - Use Google Apps Script Instead
If you want NO credentials file:
```
1. Follow Google Apps Script instructions above
2. Results go to Google Sheets automatically
3. No credentials.json needed!
```

---

## File Guide

| File | Purpose | Click to |
|------|---------|----------|
| `QUICK_TEST.bat` | Test with 10 URLs | See if it works |
| `RUN_FULL.bat` | Crawl all URLs | Run full crawl |
| `EXPORT_TO_SHEETS.bat` | Send to Google Sheets | Export results |
| `RUN_CRAWLER.bat` | Interactive menu | Choose what to do |

---

## What Happens When You Double-Click

```
1. Command window opens
2. Crawler starts
3. Shows progress: [1/358] Crawling: https://...
4. Shows results: ✓ Success (HTTP 200)
5. Saves all data
6. Shows summary statistics
7. Done!
```

---

## Results Location

After running, you'll have:

**Local file:**
- `crawl_results.jsonl` - All results in JSON format

**Google Sheets (if exported):**
- Data appears in your Google Sheet automatically
- Same data, but in a spreadsheet

---

## Questions?

### "What's the difference between the .bat files?"

- **QUICK_TEST.bat** - Tests with 10 URLs (fast)
- **RUN_FULL.bat** - All URLs (slow but complete)
- **EXPORT_TO_SHEETS.bat** - Sends to Google Sheets
- **RUN_CRAWLER.bat** - Menu to choose

### "Can I change the Excel file?"

Yes! Just:
1. Create your own Excel file with URLs
2. Make sure column is named: "トップページURL", "URL", or "Homepage"
3. Use: `RUN_CRAWLER.bat` and choose to limit URLs
4. Or edit the .bat files to use your filename

### "How long does it take?"

- 10 URLs: ~1 minute
- 50 URLs: ~5 minutes
- 100 URLs: ~10 minutes
- 358 URLs: ~30 minutes

### "Can I stop it?"

Yes, press `Ctrl + C` in the command window

### "Where are the results?"

- Local: `crawl_results.jsonl` file in this folder
- Google Sheets: Appears in your Google Sheet if you used EXPORT_TO_SHEETS.bat

---

## Summary

For **non-developers**:
1. Just double-click the .bat files
2. No command line needed
3. No complex commands
4. Results appear automatically

That's it!

