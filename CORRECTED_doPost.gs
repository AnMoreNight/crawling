// CORRECTED doPost function for your Google Apps Script

function doPost(e) {
  try {
    // Replace with your actual Google Sheet ID
    const SHEET_ID = '1-CTG-z5o9XhLbGy-3SZr5bUF9X0rekKLV0Zw-7DX8xI';
    const ss = SpreadsheetApp.openById(SHEET_ID);
    const sheet = ss.getSheetByName('Sheet1') || ss.getActiveSheet();
    const payload = JSON.parse(e.postData.contents);
    
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
    
    // Handle single result (from crawler with action=addResult)
    if (payload.action === 'addResult' && payload.data) {
      const result = payload.data;
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
      
      return ContentService.createTextOutput(
        JSON.stringify({success: true, message: 'Result added', url: result.url})
      ).setMimeType(ContentService.MimeType.JSON);
    }
    
    // Handle batch array (array of rows directly)
    if (Array.isArray(payload)) {
      let count = 0;
      payload.forEach(result => {
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
        count++;
      });
      
      return ContentService.createTextOutput(
        JSON.stringify({success: true, rows_added: count, message: `Added ${count} rows`})
      ).setMimeType(ContentService.MimeType.JSON);
    }
    
    // Invalid payload
    return ContentService.createTextOutput(
      JSON.stringify({success: false, error: 'Invalid payload format. Expected array or {action: "addResult", data: {...}}'})
    ).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    const errorMsg = error.toString();
    Logger.log('ERROR: ' + errorMsg);
    Logger.log('Stack: ' + error.stack);
    return ContentService.createTextOutput(
      JSON.stringify({success: false, error: errorMsg, stack: error.stack})
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

// Test function
function doGet(e) {
  return ContentService.createTextOutput(
    'Google Sheets Export API Ready. Send POST requests with crawler results.'
  );
}
