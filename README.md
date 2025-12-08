# Web Crawler Module

A scalable, production-ready web crawler module for extracting company information from websites. This module implements Phase 1 specifications for crawling company websites and extracting structured data including email addresses, inquiry forms, and metadata.

## Features

- **Robots.txt Compliance**: Respects robots.txt when configured
- **Concurrency Control**: Configurable concurrent request handling
- **Retry Logic**: Automatic retry for network failures
- **Form Detection**: Multi-language support for detecting inquiry/contact forms
- **Email Extraction**: Regex-based email extraction with normalization
- **Redirect Handling**: Follows redirects and resolves final URLs
- **Structured Output**: JSON-ready output format for database insertion
- **Modular Design**: Clean separation of concerns with reusable components

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from crawler import CrawlerEngine

# Configure crawler
crawler = CrawlerEngine(
    root_url="https://example.com",
    crawl_settings={
        'timeout': 30
    },
    user_agent_policy="CrawlerBot/1.0",
    robots_policy="respect",
    exclude_patterns=["/admin", "/login"]
)

# Start crawling - returns single result
result = crawler.crawl(output_file="results.jsonl")

# Print result
print(result)

# Cleanup
crawler.close()
```

## Architecture

### Module Structure

```
crawling/
├── crawler/
│   ├── __init__.py          # Module exports
│   ├── engine.py            # Main CrawlerEngine class
│   ├── fetcher.py           # Page fetching with retry logic
│   ├── parser.py            # HTML parsing utilities
│   ├── robots.py            # Robots.txt checker
│   └── storage.py           # Result storage and formatting
├── utils/
│   ├── __init__.py
│   └── logger.py            # Logging utilities
├── example.py               # Usage examples
├── requirements.txt         # Dependencies
└── README.md                # This file
```

### Core Components

1. **CrawlerEngine** (`crawler/engine.py`)
   - Main orchestrator
   - Manages crawl queue and concurrency
   - Coordinates all components

2. **PageFetcher** (`crawler/fetcher.py`)
   - HTTP requests with retry logic
   - Redirect following
   - Timeout handling

3. **HTMLParser** (`crawler/parser.py`)
   - Link extraction
   - Form detection (multi-language)
   - Email extraction
   - Metadata extraction

4. **RobotsChecker** (`crawler/robots.py`)
   - Robots.txt parsing
   - URL permission checking
   - Caching for performance

5. **CrawlResult** (`crawler/storage.py`)
   - Result data structure
   - JSON serialization
   - File output handling

## Configuration

### Crawl Settings

- `timeout`: Request timeout in seconds (default: 30)

**Note**: The crawler crawls only the root URL once per input. It does not follow links to other pages.

### Policies

- `robots_policy`: `"respect"` or `"ignore"` robots.txt
- `user_agent_policy`: User agent string for requests

### Exclude Patterns

List of URL patterns to skip during crawling (e.g., `["/admin", "/login", ".pdf"]`)

## Output Format

Each crawl result is a JSON object with the following structure:

```json
{
  "url": "https://example.com",
  "email": "contact@example.com",
  "inquiryFormUrl": "https://example.com/contact/form",
  "companyName": "Example Company",
  "industry": "technology",
  "httpStatus": 200,
  "robotsAllowed": true,
  "lastCrawledAt": "2024-01-01T12:00:00",
  "crawlStatus": "success",
  "errorMessage": null
}
```

## Form Detection

The crawler detects inquiry/contact forms using:

- Form tags with inquiry-related keywords
- Button labels (English and Japanese supported)
- Link text containing form-related keywords

Supported keywords include:
- English: "contact", "inquiry", "consultation", "form", etc.
- Japanese: "問い合わせ", "お問い合わせ", "相談", etc.

## Error Handling

The crawler implements comprehensive error handling:

- Network errors: Automatic retry with exponential backoff
- Timeout errors: Configurable timeout with retry
- Parsing errors: Graceful degradation with error logging
- Robots.txt errors: Defaults to allowing crawl if robots.txt is inaccessible

## Examples

See `example.py` for complete usage examples including:

- Basic crawl
- Custom settings
- Batch crawling multiple websites

## Logging

The module uses Python's standard logging. Configure logging level:

```python
from utils.logger import setup_logger
import logging

logger = setup_logger(level=logging.INFO)
```

## Behavior

- **Single URL Crawl**: Crawls only the root URL once per input (does not follow links)
- **One Result Per Input**: Returns a single result dictionary per root URL

## Performance Considerations

- Caches robots.txt per domain
- Efficient single-page crawling
- Standard Python logging available for debugging (not included in output)

## License

This module is provided as-is for Phase 1 implementation.

