# Phase 1: Crawler Infrastructure - Implementation Guide

## Overview

Phase 1 implements a robust web crawler infrastructure for extracting company contact information. The crawler crawls a single root URL per input and extracts:

- **Email addresses** - Contact email addresses (normalized & deduplicated)
- **Inquiry forms** - Contact/inquiry form URLs
- **Company names** - Extracted from HTML titles and metadata
- **Industry classification** - Detected from meta descriptions
- **HTTP status & robots.txt compliance** - Infrastructure monitoring
- **Crawl logs & error tracking** - Full audit trail

## Architecture

### Core Components

```
crawler/
├── engine.py          # Main orchestrator (CrawlerEngine)
├── fetcher.py         # HTTP requests with retry logic (PageFetcher)
├── parser.py          # HTML parsing & data extraction (HTMLParser)
├── robots.py          # robots.txt compliance checking (RobotsChecker)
├── storage.py         # Result data structure (CrawlResult)
└── __init__.py        # Package exports

utils/
├── logger.py          # Logging configuration
└── sheets.py          # Google Sheets integration (optional)
```

### Data Flow

```
Input URL
    ↓
[CrawlerEngine] - Main orchestrator
    ↓
[RobotsChecker] - Check robots.txt permission
    ↓
[PageFetcher] - Fetch page (with retry logic)
    ↓
[HTMLParser] - Extract data from HTML
    ├─ extract_emails()       → List of emails
    ├─ detect_forms()         → Form URLs
    └─ extract_metadata()     → Company name, industry
    ↓
[CrawlResult] - Result object
    ↓
Output: JSON with all extracted data
```

## Usage Examples

### 1. Single Website Crawl

```python
from crawler.engine import CrawlerEngine
import json

# Create crawler engine
crawler = CrawlerEngine(
    root_url="https://www.konanhanbai.jp/",
    crawl_settings={'timeout': 30},
    user_agent_policy="CrawlerBot/1.0",
    robots_policy="respect"
)

# Crawl and get result
result = crawler.crawl()
print(json.dumps(result, indent=2, ensure_ascii=False))

# Clean up
crawler.close()
```

### 2. Batch Crawl from Excel

```bash
# Crawl URLs from Excel file
python batch_crawler.py input_data.xlsx --limit 10 --timeout 30

# With custom settings
python batch_crawler.py input_data.xlsx \
    --url-column "トップページURL" \
    --limit 100 \
    --robots-policy respect \
    --output results_2025.jsonl
```

### 3. Programmatic Batch Processing

```python
from crawler.engine import CrawlerEngine
from batch_crawler import BatchCrawler

# Create batch crawler
batch = BatchCrawler(timeout=30, robots_policy="respect")

# Load URLs from Excel
urls, company_names = BatchCrawler.load_urls_from_excel(
    'input.xlsx',
    url_column='トップページURL',
    limit=50
)

# Crawl all URLs
results = batch.crawl_urls(urls, company_names)

# Save results
output_file = batch.save_results('crawl_results.jsonl')

# Print summary
batch.generate_summary()
```

## Configuration

### CrawlerEngine Parameters

```python
CrawlerEngine(
    root_url: str,                    # Company website URL (required)
    crawl_settings: Dict = None,      # {'timeout': 30}
    user_agent_policy: str = None,    # "CrawlerBot/1.0"
    robots_policy: str = "respect",   # "respect" or "ignore" robots.txt
    exclude_patterns: List = None     # Patterns to skip (e.g., ["/admin"])
)
```

### Robots.txt Policy

- **"respect"** - Check robots.txt and honor disallow rules
- **"ignore"** - Crawl regardless of robots.txt restrictions

## Output Format

Each crawl produces a JSON result:

```json
{
  "url": "https://www.konanhanbai.jp/",
  "email": null,
  "inquiryFormUrl": "/koform/",
  "companyName": "コナン販売株式会社",
  "industry": null,
  "httpStatus": 200,
  "robotsAllowed": true,
  "lastCrawledAt": "2025-12-08T17:46:31.534307",
  "crawlStatus": "success",
  "errorMessage": null
}
```

## Testing

### Run Sample Tests

```bash
python test_samples.py
```

Tests 3 sample URLs and generates:
- Summary statistics
- Sample results display
- JSON results file with timestamp

### Expected Results

```
Phase 1 Crawler - Sample Website Tests

Testing: Excel Sample

[1/3] https://www.konanhanbai.jp/
  ✓ Success (HTTP 200)
    Email: N/A
    Form: /koform/
    Company: コナン販売株式会社

[2/3] http://www.wedding-b.com/
  ✓ Success (HTTP 200)
    Email: N/A
    Form: https://www.wedding-b.com/contactus.html
    Company: 結婚相談のウエディング・ベル

OVERALL STATISTICS:
  Total Crawls: 3
  Successful: 3/3 (100.0%)
  Emails Found: 0/3 (0.0%)
  Forms Found: 3/3 (100.0%)
  Total Time: 11.2s
  Avg Time/URL: 3.7s
```

## Error Handling

The crawler handles common errors gracefully:

| Error | Handling |
|-------|----------|
| Network timeout | Retry logic with exponential backoff (3 attempts max) |
| Connection error | Logged and returns error result |
| Invalid HTTP status | Returns error result with status code |
| robots.txt blocked | Returns blocked error result |
| Parsing error | Logs error, returns partial results |
| Missing data | Returns null for unextracted fields |

## Performance Characteristics

- **Timeout**: 30 seconds per URL (configurable)
- **Retry attempts**: 3 (configurable)
- **Avg processing time**: 3-5 seconds per URL
- **Concurrent requests**: Single-threaded in Phase 1
- **robots.txt caching**: Per-domain for performance

## Data Extraction

### Email Extraction

- Regex pattern: `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`
- Normalization: Lowercase, whitespace trim
- Filters:
  - Removes common bot emails (noreply, no-reply, etc.)
  - Validates basic format
  - Deduplicates

### Form Detection

Detects forms using:
- Form tags with inquiry-related keywords
- Button labels (English and Japanese)
- Link text matching inquiry patterns

Keywords supported:
- **English**: contact, inquiry, consultation, form, message
- **Japanese**: 問い合わせ, お問い合わせ, 相談, フォーム

### Company Name Extraction

- Primary: HTML `<title>` tag
- Secondary: Open Graph `og:title` meta tag
- Fallback: URL hostname

### Industry Classification

Detects from meta description keywords:
- Technology: tech, software, it
- Finance: finance, banking, investment
- Retail: retail, shop, store
- (Extensible via keyword updates)

## Batch Processing

### Input File Format

Excel (.xlsx) or CSV with columns:
- **トップページURL** (or "URL", "Homepage") - Company website URL
- **法人名** (or "Company", "companyName") - Optional company name

### Output File Format

JSONL (JSON Lines) format:
```
{"url": "...", "email": "...", ...}
{"url": "...", "email": "...", ...}
...
```

One complete JSON object per line for streaming processing.

## Deployment

### Prerequisites

```bash
# Python 3.8+
python --version

# Install dependencies
pip install -r requirements.txt
```

### Required Packages

```
requests            # HTTP requests
beautifulsoup4      # HTML parsing
lxml               # XML/HTML parsing
pandas             # Excel file handling
openpyxl           # Excel support
tqdm               # Progress tracking
```

### Optional Packages

```
google-auth        # Google Sheets API
google-api-python-client  # Sheets integration
dnspython          # Email MX validation
```

## Google Sheets Integration

### Setup (Optional)

1. Go to https://console.cloud.google.com/
2. Create a new project
3. Enable "Google Sheets API"
4. Create a Service Account
5. Generate and download JSON key
6. Save as `credentials.json` in project root
7. Share Google Sheet with service account email

### Export Results

```python
from utils.sheets import SheetsExporter

exporter = SheetsExporter(
    sheet_id="1BrpuSrHXmp0-qFcXQfW44k7LNp1i2UcB0o8xjx2w4go",
    credentials_file="credentials.json"
)

exporter.append_results("Sheet1", results)
```

## Logging

Logs are sent to console with format:
```
2025-12-08 17:46:31 - root - INFO - Initialized crawler for https://www.konanhanbai.jp/
```

### Log Levels

- **INFO** - Crawler operations, extraction results
- **WARNING** - robots.txt blocks, retry attempts
- **ERROR** - Network errors, parsing failures

## Future Enhancements (Phase 2+)

1. **Concurrent crawling** - Multi-threaded/async processing
2. **JavaScript rendering** - Playwright support for JS-heavy sites
3. **Pattern detection** - Auto-detect CMS/form platform
4. **MX validation** - DNS MX record checking
5. **Link following** - Optional recursive crawling
6. **Advanced NLP** - Better company name/industry detection
7. **Machine learning** - Form confidence scoring

## Troubleshooting

### Q: Getting timeout errors

A: Increase timeout in crawl_settings:
```python
CrawlerEngine(root_url=url, crawl_settings={'timeout': 60})
```

### Q: Not finding emails/forms

A: Some sites load content dynamically (JavaScript). Phase 2 will add Playwright support.

### Q: robots.txt is blocking crawl

A: Use `robots_policy="ignore"` to bypass, but respect legal/ethical guidelines.

### Q: Import errors

A: Ensure crawler package is properly installed:
```bash
python -c "from crawler import CrawlerEngine; print('OK')"
```

## Production Checklist

- [ ] Test on 100+ URLs for pattern validation
- [ ] Set up monitoring/logging
- [ ] Configure error notifications
- [ ] Validate output quality (spot-check results)
- [ ] Establish crawl schedule (if batch processing)
- [ ] Set up Google Sheets export (optional)
- [ ] Document custom URL column names
- [ ] Create backup of Excel input
- [ ] Plan for rate limiting if needed
- [ ] Review and approve robots.txt policy

## Support

For issues or questions:

1. Check test results in `test_results_*.json`
2. Review error messages in logs
3. Run individual URLs to debug
4. Check robots.txt compliance manually
5. Validate URLs are accessible in browser

## Compliance

- **robots.txt** - Respects by default, configurable
- **User-Agent** - Identified as "CrawlerBot/1.0"
- **Timing** - 3-5 seconds per URL average
- **Rate limiting** - Single-threaded design is respectful

---

**Version**: Phase 1.0  
**Last Updated**: December 8, 2025  
**Status**: ✅ Ready for Production Testing
