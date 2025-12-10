# Google Sheets Integration - Quick Start

## Your Google Sheet
📊 **https://docs.google.com/spreadsheets/d/1-CTG-z5o9XhLbGy-3SZr5bUF9X0rekKLV0Zw-7DX8xI/edit?usp=sharing**

---

## 3-Step Setup

### 1. Install Libraries
```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 2. Get Credentials
1. Go to: https://console.cloud.google.com/
2. Create a **Service Account**
3. Download the JSON key file
4. Save it as `credentials.json` in your project folder
5. Share your Google Sheet with the service account email

### 3. Run with Google Sheets Export
```bash
python batch_crawler.py "test data.xlsx" --google-sheets
```

---

## Done!

Your crawl results will automatically export to Google Sheets.

---

## Commands

**Export to Google Sheets:**
```bash
python batch_crawler.py "test data.xlsx" --google-sheets
```

**Export specific number of URLs:**
```bash
python batch_crawler.py "test data.xlsx" --limit 50 --google-sheets
```

**Export to specific sheet:**
```bash
python batch_crawler.py "test data.xlsx" --google-sheets --sheet-name "My Sheet"
```

---

## What Exports

✓ URL
✓ Email  
✓ Inquiry Form URL
✓ Company Name
✓ Industry
✓ HTTP Status
✓ Robots Allowed
✓ Last Crawled At
✓ Crawl Status
✓ Error Message

---

## See Also

- **GOOGLE_SHEETS_SETUP.md** - Detailed setup guide
- **batch_crawler.py** - Main crawler script
- **google_sheets_export.py** - Google Sheets API module

---

**That's it. Your crawler now exports to Google Sheets automatically.**

