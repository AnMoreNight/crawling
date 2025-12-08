"""
Example usage of the web crawler module.

This demonstrates how to use the CrawlerEngine to crawl a company website
and extract structured information.
"""

import json
import logging
from crawler import CrawlerEngine
from utils.logger import setup_logger

# Setup logging
logger = setup_logger(level=logging.INFO)


def example_basic_crawl():
    """Basic example of crawling a company website."""
    
    # Configuration
    root_url = "https://www.tantei.or.jp/"  # Replace with actual company URL
    
    crawl_settings = {
        'timeout': 30         # Request timeout in seconds
    }
    
    user_agent_policy = "CrawlerBot/1.0"
    robots_policy = "respect"  # "respect" or "ignore"
    exclude_patterns = [
        "/admin",
        "/login",
        "/logout",
        ".pdf",
        ".jpg",
        ".png"
    ]
    
    # Initialize crawler
    crawler = CrawlerEngine(
        root_url=root_url,
        crawl_settings=crawl_settings,
        user_agent_policy=user_agent_policy,
        robots_policy=robots_policy,
        exclude_patterns=exclude_patterns
    )
    
    try:
        # Start crawling - returns single result with logs
        result = crawler.crawl(output_file="crawl_results.jsonl")
        
        # Print result
        print("\n" + "="*60)
        print("CRAWL RESULT")
        print("="*60)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("="*60)
        
        # Save result to JSON file
        with open("crawl_results.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\nResult saved to crawl_results.json")
        
    except Exception as e:
        logger.error(f"Crawl failed: {e}", exc_info=True)
    finally:
        crawler.close()


def example_custom_settings():
    """Example with custom settings."""
    
    root_url = "https://example.com"
    
    crawl_settings = {
        'timeout': 60
    }
    
    crawler = CrawlerEngine(
        root_url=root_url,
        crawl_settings=crawl_settings,
        user_agent_policy="MyCustomBot/2.0",
        robots_policy="ignore",  # Ignore robots.txt
        exclude_patterns=[]
    )
    
    try:
        result = crawler.crawl()
        
        # Check if email found
        if result.get('email'):
            print(f"Found email: {result['email']}")
        
        # Check if form found
        if result.get('inquiryFormUrl'):
            print(f"Found inquiry form: {result['inquiryFormUrl']}")
        
    finally:
        crawler.close()


def example_batch_crawl():
    """Example of crawling multiple company websites - one crawl per URL."""
    
    companies = [
        "https://example1.com",
        "https://example2.com",
        "https://example3.com"
    ]
    
    crawl_settings = {
        'timeout': 30
    }
    
    all_results = []
    
    for company_url in companies:
        logger.info(f"Crawling {company_url}")
        
        crawler = CrawlerEngine(
            root_url=company_url,
            crawl_settings=crawl_settings,
            robots_policy="respect"
        )
        
        try:
            # Each crawl returns a single result
            result = crawler.crawl()
            all_results.append(result)
            
            logger.info(f"Completed {company_url}: Status={result.get('crawlStatus')}")
            
        except Exception as e:
            logger.error(f"Failed to crawl {company_url}: {e}")
            # Create error result
            error_result = {
                'url': company_url,
                'crawlStatus': 'error',
                'errorMessage': str(e),
                'logs': []
            }
            all_results.append(error_result)
        finally:
            crawler.close()
    
    # Save all results
    with open("batch_crawl_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nBatch crawl completed. Total URLs crawled: {len(all_results)}")


if __name__ == "__main__":
    # Run basic example
    print("Running basic crawl example...")
    example_basic_crawl()
    
    # Uncomment to run other examples:
    # example_custom_settings()
    # example_batch_crawl()

