"""
Batch Crawler - Processes multiple URLs from Excel/CSV
Reads from input file and crawls all URLs, saving results
"""

import argparse
import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

try:
    import pandas as pd
except ImportError:
    print("Error: pandas not installed. Run: pip install pandas openpyxl")
    sys.exit(1)

from crawler.engine import CrawlerEngine
from utils.logger import setup_logger

# Optional Google Sheets export
try:
    from google_sheets_export import GoogleSheetsExporter
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False

# Google Apps Script integration
try:
    from google_apps_script_integration import GoogleAppsScriptIntegration
    GOOGLE_APPS_SCRIPT_AVAILABLE = True
except ImportError:
    GOOGLE_APPS_SCRIPT_AVAILABLE = False

# Setup logging
logger = setup_logger(name="batch_crawler", level=logging.INFO)


class BatchCrawler:
    """Handles batch crawling of multiple websites."""
    
    def __init__(
        self,
        timeout: int = 30,
        robots_policy: str = "respect",
        user_agent: str = "CrawlerBot/1.0"
    ):
        """
        Initialize batch crawler.
        
        Args:
            timeout: Request timeout in seconds
            robots_policy: "respect" or "ignore"
            user_agent: User agent string
        """
        self.timeout = timeout
        self.robots_policy = robots_policy
        self.user_agent = user_agent
        self.results = []
        self.start_time = datetime.now()
    
    def crawl_urls(self, urls: List[str], company_names: List[str] = None) -> List[Dict]:
        """
        Crawl multiple URLs.
        
        Args:
            urls: List of URLs to crawl
            company_names: Optional list of company names (same order as urls)
            
        Returns:
            List of result dictionaries
        """
        total = len(urls)
        if company_names is None:
            company_names = [None] * total
        
        for i, (url, company_name) in enumerate(zip(urls, company_names), 1):
            try:
                logger.info(f"[{i}/{total}] Crawling: {url}")
                
                crawler = CrawlerEngine(
                    root_url=url,
                    crawl_settings={'timeout': self.timeout},
                    user_agent_policy=self.user_agent,
                    robots_policy=self.robots_policy
                )
                
                result = crawler.crawl()
                self.results.append(result)
                
                # Log summary
                status = result.get('crawlStatus')
                email = result.get('email')
                form = result.get('inquiryFormUrl')
                
                if status == 'success':
                    logger.info(f"  ✓ Success - Email: {email or 'N/A'}, Form: {form or 'N/A'}")
                else:
                    logger.warning(f"  ✗ Failed - {result.get('errorMessage')}")
                
                crawler.close()
                
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
                from datetime import datetime
                self.results.append({
                    'url': url,
                    'email': None,
                    'inquiryFormUrl': None,
                    'companyName': company_name,
                    'industry': None,
                    'httpStatus': 0,
                    'robotsAllowed': True,
                    'lastCrawledAt': datetime.utcnow().isoformat(),
                    'crawlStatus': 'error',
                    'errorMessage': str(e)
                })
        
        return self.results
    
    def save_results(self, output_file: str = None):
        """
        Save crawl results to file.
        
        Args:
            output_file: Output file path (default: timestamped crawl_results.jsonl)
        """
        if output_file is None:
            output_file = f"crawl_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for result in self.results:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
            
            logger.info(f"\n✓ Results saved to: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return None
    
    def generate_summary(self):
        """Generate and print summary statistics."""
        total = len(self.results)
        successful = sum(1 for r in self.results if r.get('crawlStatus') == 'success')
        failed = sum(1 for r in self.results if r.get('crawlStatus') == 'error')
        
        emails_found = sum(1 for r in self.results if r.get('email'))
        forms_found = sum(1 for r in self.results if r.get('inquiryFormUrl'))
        company_names_found = sum(1 for r in self.results if r.get('companyName'))
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        print("\n" + "=" * 70)
        print("CRAWL RESULTS SUMMARY")
        print("=" * 70)
        print(f"Total URLs: {total}")
        print(f"Successful: {successful} ({successful/total*100 if total > 0 else 0:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100 if total > 0 else 0:.1f}%)")
        print("-" * 70)
        print(f"Emails Found: {emails_found}/{total} ({emails_found/total*100 if total > 0 else 0:.1f}%)")
        print(f"Forms Found: {forms_found}/{total} ({forms_found/total*100 if total > 0 else 0:.1f}%)")
        print(f"Company Names: {company_names_found}/{total} ({company_names_found/total*100 if total > 0 else 0:.1f}%)")
        print("-" * 70)
        print(f"Total Time: {elapsed:.1f}s")
        if total > 0:
            print(f"Avg Time/URL: {elapsed/total:.1f}s")
        print("=" * 70 + "\n")


def load_urls_from_excel(file_path: str, url_column: str = None, limit: int = None) -> tuple:
    """
    Load URLs from Excel file.
    
    Args:
        file_path: Path to Excel file
        url_column: Column name containing URLs (auto-detect if None)
        limit: Limit number of URLs to load
        
    Returns:
        Tuple of (urls: List[str], company_names: List[str])
    """
    try:
        df = pd.read_excel(file_path)
        
        # Auto-detect URL column
        if url_column is None:
            possible_cols = ['トップページURL', 'URL', 'Url', 'url', 'Homepage', 'homepage']
            url_column = None
            for col in possible_cols:
                if col in df.columns:
                    url_column = col
                    break
            
            if url_column is None:
                for col in df.columns:
                    if 'url' in col.lower() or 'homepage' in col.lower():
                        url_column = col
                        break
        
        if url_column is None:
            logger.error(f"Could not find URL column. Available columns: {list(df.columns)}")
            return [], []
        
        logger.info(f"Using URL column: {url_column}")
        
        urls = df[url_column].dropna().astype(str).tolist()
        
        # Try to get company names
        company_names = []
        company_col = None
        for col in ['法人名', 'Company', 'companyName', 'company_name']:
            if col in df.columns:
                company_col = col
                break
        
        if company_col:
            company_names = df[company_col].astype(str).tolist()
            company_names = [name if name != 'nan' else None for name in company_names]
        else:
            company_names = [None] * len(urls)
        
        # Filter out empty strings and fix URLs
        filtered_urls = []
        filtered_names = []
        for url, name in zip(urls, company_names):
            url_clean = url.strip()
            if url_clean and url_clean != 'nan':
                if not url_clean.startswith(('http://', 'https://')):
                    url_clean = 'https://' + url_clean
                filtered_urls.append(url_clean)
                filtered_names.append(name if name != 'nan' else None)
        
        if limit:
            filtered_urls = filtered_urls[:limit]
            filtered_names = filtered_names[:limit]
        
        logger.info(f"Loaded {len(filtered_urls)} URLs from {file_path}")
        return filtered_urls, filtered_names
        
    except Exception as e:
        logger.error(f"Failed to load URLs from {file_path}: {e}")
        return [], []


def main():
    """Main batch crawler."""
    parser = argparse.ArgumentParser(
        description='Batch crawl multiple websites from Excel file'
    )
    parser.add_argument('input_file', help='Input Excel or CSV file')
    parser.add_argument('--url-column', type=str, help='Column name with URLs')
    parser.add_argument('--limit', type=int, help='Limit number of URLs to crawl')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout (default: 30s)')
    parser.add_argument('--robots-policy', choices=['respect', 'ignore'], default='respect',
                        help='Robots.txt policy (default: respect)')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--google-sheets', action='store_true', 
                        help='Export results to Google Sheets')
    parser.add_argument('--sheet-name', type=str, default='Sheet1',
                        help='Google Sheets sheet name (default: Sheet1)')
    parser.add_argument('--credentials', type=str, default='credentials.json',
                        help='Path to Google service account credentials')
    parser.add_argument('--google-apps-script', type=str, 
                        help='Google Apps Script deployment URL')
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.input_file).exists():
        logger.error(f"Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Load URLs
    urls, company_names = load_urls_from_excel(args.input_file, args.url_column, args.limit)
    if not urls:
        logger.error("No URLs to crawl")
        sys.exit(1)
    
    logger.info(f"\nStarting batch crawl with {len(urls)} URLs...")
    logger.info(f"Timeout: {args.timeout}s, Robots Policy: {args.robots_policy}")
    
    # Run crawler
    crawler = BatchCrawler(
        timeout=args.timeout,
        robots_policy=args.robots_policy
    )
    
    results = crawler.crawl_urls(urls, company_names)
    
    # Save results to JSON
    output_file = crawler.save_results(args.output)
    
    # Export to Google Sheets if requested
    if args.google_sheets:
        if GOOGLE_SHEETS_AVAILABLE:
            logger.info("\nExporting results to Google Sheets...")
            exporter = GoogleSheetsExporter(args.credentials)
            if exporter.service:
                exporter.export_results(results, args.sheet_name, append=False)
                sheet_info = exporter.get_sheet_info()
                if sheet_info:
                    print(f"\n✓ Results exported to: {sheet_info['url']}")
                    print(f"  Sheet: {args.sheet_name}")
        else:
            logger.warning("Google Sheets export requested but google-auth-oauthlib not installed")
            logger.info("Install it with: pip install google-auth-oauthlib google-auth-httplib2")
    
    # Send to Google Apps Script if requested
    if args.google_apps_script:
        if GOOGLE_APPS_SCRIPT_AVAILABLE:
            logger.info("\nSending results to Google Apps Script...")
            integrator = GoogleAppsScriptIntegration(args.google_apps_script)
            summary = integrator.send_batch(results)
            if summary:
                print(f"\n✓ Google Apps Script Integration Complete")
                print(f"  Total: {summary['total']}")
                print(f"  Successful: {summary['successful']}")
                print(f"  Failed: {summary['failed']}")
        else:
            logger.warning("Google Apps Script integration not available")
    
    # Print summary
    crawler.generate_summary()
    
    # Print sample results
    print("\nSample Results (first 3):")
    for result in results[:3]:
        print(f"\n  URL: {result['url']}")
        print(f"    Status: {result['crawlStatus']}")
        print(f"    Email: {result.get('email') or 'N/A'}")
        print(f"    Form: {result.get('inquiryFormUrl') or 'N/A'}")
        print(f"    Company: {result.get('companyName') or 'N/A'}")


if __name__ == "__main__":
    main()

