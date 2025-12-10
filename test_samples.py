"""
Test script for Phase 1 Crawler
Tests on sample websites from various categories
"""

import json
import logging
from datetime import datetime
from crawler.engine import CrawlerEngine
from crawler.fetcher import PageFetcher
from crawler.parser import HTMLParser

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Sample test websites organized by category
TEST_WEBSITES = {
    "Excel Sample": [
        "https://www.konanhanbai.jp/",
        "http://www.wedding-b.com/",
        "http://mcc-muguet.jp/",
    ],
}


def test_url(url: str) -> dict:
    """Test crawling a single URL."""
    logger.info(f"Crawling: {url}")
    
    result = {
        'url': url,
        'status': 0,
        'error': None,
        'email': None,
        'form': None,
        'company': None,
        'crawl_status': 'error'
    }
    
    try:
        fetcher = PageFetcher(timeout=30, max_retries=3, user_agent="CrawlerBot/1.0")
        html, status, final_url, error = fetcher.fetch_page(url)
        result['status'] = status
        result['error'] = error
        
        if html and not error:
            final_url_to_use = final_url or url
            parser = HTMLParser()
            emails = parser.extract_emails(html)
            forms = parser.detect_forms(html)
            metadata = parser.extract_metadata(html)
            
            result.update({
                'email': emails[0] if emails else None,
                'form': forms[0] if forms else None,
                'company': metadata.get('companyName'),
                'crawl_status': 'success'
            })
        
        fetcher.close()
        
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"Exception: {e}")
    
    return result


def test_category(category: str, urls: list):
    """Test crawling a category of websites."""
    print(f"\n{'='*70}")
    print(f"Testing: {category}")
    print(f"{'='*70}\n")
    
    results = []
    
    for i, url in enumerate(urls, 1):
        logger.info(f"[{i}/{len(urls)}] Crawling: {url}")
        result = test_url(url)
        results.append(result)
        
        # Print result
        if result['crawl_status'] == 'success':
            print(f"  ✓ Success (HTTP {result['status']})")
            email_str = result['email'] or "N/A"
            form_str = result['form'] or "N/A"
            company_str = result['company'] or "N/A"
            print(f"    Email: {email_str}")
            print(f"    Form: {form_str}")
            print(f"    Company: {company_str}")
        else:
            print(f"  ✗ Failed: {result['error']}")
    
    return results


def main():
    """Run tests on all categories."""
    print("\n" + "="*70)
    print("Phase 1 Crawler - Sample Website Tests")
    print("="*70)
    
    start_time = datetime.now()
    all_results = {}
    
    # Test categories
    for category, urls in TEST_WEBSITES.items():
        all_results[category] = test_category(category, urls)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}\n")
    
    total_crawls = 0
    total_success = 0
    emails_found = 0
    forms_found = 0
    
    for category, results in all_results.items():
        successful = sum(1 for r in results if r['crawl_status'] == 'success')
        emails = sum(1 for r in results if r.get('email'))
        forms = sum(1 for r in results if r.get('form'))
        
        print(f"{category}:")
        print(f"  Success: {successful}/{len(results)}")
        print(f"  Emails Found: {emails}")
        print(f"  Forms Found: {forms}\n")
        
        total_crawls += len(results)
        total_success += successful
        emails_found += emails
        forms_found += forms
    
    print(f"{'='*70}")
    print(f"OVERALL STATISTICS:")
    if total_crawls > 0:
        print(f"  Total Crawls: {total_crawls}")
        print(f"  Successful: {total_success}/{total_crawls} ({total_success/total_crawls*100:.1f}%)")
        print(f"  Emails Found: {emails_found}/{total_crawls} ({emails_found/total_crawls*100:.1f}%)")
        print(f"  Forms Found: {forms_found}/{total_crawls} ({forms_found/total_crawls*100:.1f}%)")
        print(f"  Total Time: {elapsed:.1f}s")
        print(f"  Avg Time/URL: {elapsed/total_crawls:.1f}s")
    else:
        print(f"  No crawls performed")
    print(f"{'='*70}\n")
    
    # Save results
    output_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to: {output_file}\n")


if __name__ == "__main__":
    main()

