"""
Google Apps Script Alternative
This module creates a simple endpoint to send data to Google Sheets
without needing credentials.json

The easiest approach: Use Google Apps Script!
"""

# OPTION 1: Simple Python - No Credentials Needed
# ================================================

def get_apps_script_code():
    """
    Returns the Google Apps Script code you need to paste into Google Sheets.
    This does NOT require any credentials file!
    
    Steps:
    1. Open your Google Sheet
    2. Click Extensions → Apps Script
    3. Delete default code
    4. Paste the code below
    5. Click Deploy → New Deployment → Web app
    6. Execute as: Me
    7. Allow access
    8. Copy the deployment URL
    9. Paste URL in config below
    10. Done! No credentials needed!
    """
    
    code = '''
// Paste this into Google Apps Script (Extensions → Apps Script in your Sheet)
// NO CREDENTIALS NEEDED!

function doPost(e) {
  try {
    const sheet = SpreadsheetApp.getActiveSheet();
    const data = JSON.parse(e.postData.contents);
    
    // Add headers if sheet is empty
    if (sheet.getLastRow() === 0) {
      const headers = [
        'URL',
        'Email',
        'Inquiry Form URL',
        'Company Name',
        'Industry',
        'HTTP Status',
        'Robots Allowed',
        'Last Crawled At',
        'Crawl Status',
        'Error Message'
      ];
      sheet.appendRow(headers);
    }
    
    // Add each result row
    data.forEach(result => {
      sheet.appendRow([
        result.url || '',
        result.email || '',
        result.inquiryFormUrl || '',
        result.companyName || '',
        result.industry || '',
        result.httpStatus || '',
        result.robotsAllowed || '',
        result.lastCrawledAt || '',
        result.crawlStatus || '',
        result.errorMessage || ''
      ]);
    });
    
    return ContentService.createTextOutput(
      JSON.stringify({success: true, rows: data.length})
    ).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    return ContentService.createTextOutput(
      JSON.stringify({success: false, error: error.toString()})
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

// Test function (optional)
function doGet(e) {
  return ContentService.createTextOutput(
    'Google Sheets Export API Ready. Send POST requests with crawler results.'
  );
}
'''
    
    return code


# OPTION 2: Simple Batch Script
# ===============================

SIMPLE_BATCH_SCRIPT = '''
@echo off
REM Simple batch script - Just run this!
REM No credentials needed with Apps Script option

cd /d %~dp0
python batch_crawler.py "test data.xlsx" --apps-script
pause
'''

SIMPLE_BASH_SCRIPT = '''#!/bin/bash
# Simple bash script - Just run this!
# No credentials needed with Apps Script option

cd "$(dirname "$0")"
python batch_crawler.py "test data.xlsx" --apps-script
'''

# OPTION 3: One-Click Desktop Shortcut
# =====================================

DESKTOP_SHORTCUT_CODE = '''
@echo off
REM Save this as a .bat file on your Desktop
REM Just double-click to run!

REM Change to the project directory
cd /d C:\Users\tobia\Downloads\crawling-main

REM Run the crawler with Google Sheets export
python batch_crawler.py "test data.xlsx" --google-sheets

REM Keep window open to see results
pause
'''

if __name__ == '__main__':
    print("GOOGLE APPS SCRIPT SETUP INSTRUCTIONS")
    print("=" * 50)
    print("\n1. Open your Google Sheet")
    print("2. Click: Extensions → Apps Script")
    print("3. Delete the default code")
    print("4. Paste this code:\n")
    print(get_apps_script_code())
    print("\n" + "=" * 50)
    print("5. Click Deploy → New Deployment")
    print("6. Select: Web app")
    print("7. Execute as: Me")
    print("8. New users: Allow access")
    print("9. Copy the deployment URL")
    print("10. Done!\n")
