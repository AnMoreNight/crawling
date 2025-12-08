# Architecture Overview

## File Structure

```
crawling/
├── crawler/                    # Main crawler module
│   ├── __init__.py            # Module exports (CrawlerEngine)
│   ├── engine.py              # Main CrawlerEngine class
│   ├── fetcher.py             # PageFetcher - HTTP requests with retry
│   ├── parser.py              # HTMLParser - parsing utilities
│   ├── robots.py              # RobotsChecker - robots.txt handling
│   └── storage.py             # CrawlResult - result formatting
├── utils/                      # Utility modules
│   ├── __init__.py
│   └── logger.py              # Logging configuration
├── example.py                  # Usage examples
├── requirements.txt           # Python dependencies
├── README.md                  # User documentation
└── ARCHITECTURE.md            # This file
```

## Component Responsibilities

### CrawlerEngine (`crawler/engine.py`)
**Main orchestrator** that coordinates all components:
- Manages crawl queue with depth tracking
- Controls concurrency using ThreadPoolExecutor
- Coordinates robots.txt checking, fetching, and parsing
- Aggregates results and provides summary statistics

**Key Methods:**
- `__init__()`: Initialize with configuration
- `crawl()`: Start crawling process
- `_crawl_page()`: Crawl single page
- `_should_crawl()`: Decision logic for URL crawling
- `get_summary()`: Get crawl statistics

### PageFetcher (`crawler/fetcher.py`)
**HTTP request handler** with robust error handling:
- Implements retry logic with exponential backoff
- Follows redirects automatically
- Handles timeouts and connection errors
- Uses requests.Session for connection pooling

**Key Methods:**
- `fetch_page()`: Fetch URL with retry logic
- Returns: (content, status_code, final_url, error_message)

### HTMLParser (`crawler/parser.py`)
**HTML parsing utilities** for data extraction:
- Extracts links from HTML
- Detects inquiry/contact forms (multi-language)
- Extracts email addresses with normalization
- Extracts metadata (company name, industry)

**Key Methods:**
- `parse_links()`: Extract all links from page
- `detect_forms()`: Find inquiry/contact forms
- `extract_emails()`: Extract and normalize emails
- `extract_metadata()`: Extract company metadata

### RobotsChecker (`crawler/robots.py`)
**Robots.txt compliance** handler:
- Parses robots.txt files
- Caches parsed files per domain
- Checks URL permissions
- Respects user agent policies

**Key Methods:**
- `is_allowed()`: Check if URL is allowed
- `_get_parser()`: Get/cache RobotFileParser

### CrawlResult (`crawler/storage.py`)
**Result data structure** and serialization:
- Structured result format matching specification
- JSON serialization for database insertion
- File output handling (JSONL format)

**Key Methods:**
- `to_dict()`: Convert to dictionary
- `to_json()`: Convert to JSON string
- `store_crawl_result()`: Write to file

## Data Flow

```
1. User creates CrawlerEngine with configuration
   ↓
2. Engine.crawl() starts
   ↓
3. For each URL in queue:
   a. RobotsChecker.is_allowed() → Check robots.txt
   b. PageFetcher.fetch_page() → Fetch HTML
   c. HTMLParser.parse_links() → Extract links
   d. HTMLParser.detect_forms() → Find forms
   e. HTMLParser.extract_emails() → Extract emails
   f. HTMLParser.extract_metadata() → Extract metadata
   g. Create CrawlResult → Format result
   h. Add new links to queue (if depth < maxDepth)
   ↓
4. Store results → Write to file/output
   ↓
5. Return list of results
```

## Concurrency Model

- Uses `ThreadPoolExecutor` for concurrent requests
- Configurable concurrency limit (default: 5)
- Queue-based URL management
- Thread-safe visited URL tracking
- Results collected in main thread

## Error Handling Strategy

### Network Errors
- Automatic retry with exponential backoff
- Configurable max retries (default: 3)
- Retries on: 429, 500, 502, 503, 504
- Timeout handling with configurable timeout

### Parsing Errors
- Graceful degradation
- Logs errors but continues crawling
- Returns partial results when possible

### Robots.txt Errors
- Defaults to allowing crawl if inaccessible
- Caches per domain to reduce requests
- Logs warnings for debugging

## Configuration Options

### Crawl Settings
- `maxDepth`: Maximum crawl depth (integer)
- `concurrency`: Concurrent requests (integer)
- `timeout`: Request timeout in seconds (integer)

### Policies
- `robots_policy`: "respect" | "ignore"
- `user_agent_policy`: User agent string

### Filters
- `exclude_patterns`: List of URL patterns to skip

## Output Format

Each result follows the specification exactly:
```python
{
  "url": str,
  "email": str | None,
  "inquiryFormUrl": str | None,
  "companyName": str | None,
  "industry": str | None,
  "httpStatus": int,
  "robotsAllowed": bool,
  "lastCrawledAt": str (ISO format),
  "crawlStatus": "success" | "error" | "retry",
  "errorMessage": str | None
}
```

## Design Principles

1. **Modularity**: Each component has a single responsibility
2. **Extensibility**: Easy to add new parsers or fetchers
3. **Robustness**: Comprehensive error handling
4. **Performance**: Concurrency control and caching
5. **Compliance**: Respects robots.txt and rate limits
6. **Observability**: Detailed logging at all levels

## Testing Considerations

- Unit tests for each component
- Mock HTTP responses for fetcher tests
- Test robots.txt parsing edge cases
- Test form detection with various HTML structures
- Test email extraction with various formats
- Integration tests for full crawl flow

## Future Enhancements

- Rate limiting per domain
- Cookie/session handling
- JavaScript rendering support
- Database integration
- Distributed crawling
- More sophisticated industry detection
- Enhanced form detection with ML

