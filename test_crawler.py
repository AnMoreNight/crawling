"""
Phase 1 Crawler - Test Suite
Tests the crawler on sample websites and generates detailed reports.
"""

import json
import logging
from datetime import datetime
from typing import List, Dict
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler.engine import CrawlerEngine
from crawler.fetcher import PageFetcher
from crawler.robots import RobotsChecker
from utils.logger import setup_logger

# Setup logging
logger = setup_logger(name="test_crawler", level=logging.INFO)


# Sample test websites from your documents
TEST_WEBSITES = [
    # 探偵事務所 (Detective Agencies)
    {
        "url": "https://sc-t.co.jp",
        "category": "探偵事務所",
        "company_name": None
    },
    {
        "url": "https://www.avand-research.com",
        "category": "探偵事務所",
        "company_name": None
    },
    {
        "url": "https://machikado-tantei.com/item307/",
        "category": "探偵事務所",
        "company_name": None
    },
    # 興信所 (Credit Investigation)
    {
        "url": "https://www.galu-akita.com",
        "category": "興信所",
        "company_name": None
    },
    {
        "url": "https://www.tantei.or.jp/page/akitaken-c.html",
        "category": "興信所",
        "company_name": None
    },
    {
        "url": "https://www.himawaritantei.com/akita/",
        "category": "興信所",
        "company_name": None
    },
    # 結婚相談所 (Marriage Consultation)
    {
        "url": "https://www.club-sincerite.co.jp/",
        "category": "結婚相談所",
        "company_name": None
    },
    {
        "url": "https://www.p-a.jp/ad/reason/",
        "category": "結婚相談所",
        "company_name": None
    },
    {
        "url": "https://marrymeweb.com",
        "category": "結婚相談所",
        "company_name": None
    },
    # 離婚特化弁護士事務所 (Divorce Law Firms)
    {
        "url": "https://bengoshi-rikon.jp/",
        "category": "離婚特化弁護士事務所",
        "company_name": None
    },
    {
        "url": "https://www.rikon-soleil.jp",
        "category": "離婚特化弁護士事務所",
        "company_name": None
    },
    {
        "url": "https://www.mitakeyasaka-law.com",
        "category": "離婚特化弁護士事務所",
        "company_name": None
    },
    # DVシェルター (DV Shelters)
    {
        "url": "https://nwsnet.or.jp",
        "category": "DVシェルター",
        "company_name": None
    },
    {
        "url": "https://www.twp.metro.tokyo.lg.jp/consult/tabid/96/default.aspx",
        "category": "DVシェルター",
        "company_name": None
    },
    # カウンセラー (Counselors)
    {
        "url": "https://rikon.biz",
        "category": "カウンセラー",
        "company_name": None
    },
    {
        "url": "https://rikon-terrace.com/counseling/",
        "category": "カウンセラー",
        "company_name": None
    },
    {
        "url": "https://rikon.sakura-sogo.jp/02ketsui/",
        "category": "カウンセラー",
        "company_name": None
    },
    # From Excel sample
    {
        "url": "https://www.konanhanbai.jp/",
        "category": "ITコンサルティング",
        "company_name": "コナン販売株式会社"
    },
    {
        "url": "http://www.wedding-b.com/",
        "category": "ブライダル",
        "company_name": "株式会社ウエディング・ベル"
    },
    {
        "url": "http://mcc-muguet.jp/",
        "category": "その他スクール",
        "company_name": "株式会社エムシー・くりえーと"
    },
]


class TestReport:
    """Generates test reports."""
    
    def __init__(self):
        self.results: List[Dict] = []
        self.start_time = datetime.now()
    
    def add_result(self, result: Dict):
        """Add a test result."""
        self.results.append(result)
    
    def generate_summary(self) -> Dict:
        """Generate summary statistics."""
        total = len(self.results)
        successful = sum(1 for r in self.results if r['crawl_status'] == 'success')
        failed = sum(1 for r in self.results if r['crawl_status'] == 'error')
        
        # Email extraction stats
        emails_found = sum(1 for r in self.results if r.get('email'))
        email_accuracy = (emails_found / total * 100) if total > 0 else 0
        
        # Form detection stats
        forms_found = sum(1 for r in self.results if r.get('inquiry_form_url'))
        form_accuracy = (forms_found / total * 100) if total > 0 else 0
        
        # Company name extraction stats
        names_found = sum(1 for r in self.results if r.get('company_name'))
        name_accuracy = (names_found / total * 100) if total > 0 else 0
        
        # Industry extraction stats
        industries_found = sum(1 for r in self.results if r.get('industry'))
        industry_accuracy = (industries_found / total * 100) if total > 0 else 0
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'total_websites': total,
            'successful_crawls': successful,
            'failed_crawls': failed,
            'success_rate': f"{(successful/total*100):.1f}%" if total > 0 else "0%",
            'email_extraction': {
                'found': emails_found,
                'accuracy': f"{email_accuracy:.1f}%"
            },
            'form_detection': {
                'found': forms_found,
                'accuracy': f"{form_accuracy:.1f}%"
            },
            'company_name_extraction': {
                'found': names_found,
                'accuracy': f"{name_accuracy:.1f}%"
            },
            'industry_extraction': {
                'found': industries_found,
                'accuracy': f"{industry_accuracy:.1f}%"
            },
            'elapsed_time': f"{elapsed:.2f}s",
            'avg_time_per_site': f"{(elapsed/total):.2f}s" if total > 0 else "0s"
        }
    
    def print_summary(self):
        """Print summary to console."""
        summary = self.generate_summary()
        
        print("\n" + "="*80)
        print("PHASE 1 CRAWLER - TEST RESULTS SUMMARY")
        print("="*80)
        print(f"Total Websites Tested: {summary['total_websites']}")
        print(f"Successful Crawls: {summary['successful_crawls']}")
        print(f"Failed Crawls: {summary['failed_crawls']}")
        print(f"Success Rate: {summary['success_rate']}")
        print("-"*80)
        print(f"Email Extraction: {summary['email_extraction']['found']}/{summary['total_websites']} ({summary['email_extraction']['accuracy']})")
        print(f"Form Detection: {summary['form_detection']['found']}/{summary['total_websites']} ({summary['form_detection']['accuracy']})")
        print(f"Company Name: {summary['company_name_extraction']['found']}/{summary['total_websites']} ({summary['company_name_extraction']['accuracy']})")
        print(f"Industry: {summary['industry_extraction']['found']}/{summary['total_websites']} ({summary['industry_extraction']['accuracy']})")
        print("-"*80)
        print(f"Total Time: {summary['elapsed_time']}")
        print(f"Avg Time/Site: {summary['avg_time_per_site']}")
        print("="*80 + "\n")
    
    def print_detailed_results(self):
        """Print detailed results for each website."""
        print("\n" + "="*80)
        print("DETAILED RESULTS BY WEBSITE")
        print("="*80 + "\n")
        
        for i, result in enumerate(self.results, 1):
            status_symbol = "✓" if result['crawl_status'] == 'success' else "✗"
            print(f"{i}. {status_symbol} {result['url']}")
            print(f"   Category: {result.get('expected_category', 'N/A')}")
            print(f"   Status: {result['crawl_status']} (HTTP {result.get('http_status', 'N/A')})")
            
            if result.get('email'):
                print(f"   ✓ Email: {result['email']}")
            else:
                print(f"   ✗ Email: Not found")
            
            if result.get('inquiry_form_url'):
                print(f"   ✓ Form: {result['inquiry_form_url']}")
            else:
                print(f"   ✗ Form: Not found")
            
            if result.get('company_name'):
                print(f"   ✓ Company: {result['company_name']}")
            else:
                print(f"   ✗ Company: Not found")
            
            if result.get('industry'):
                print(f"   ✓ Industry: {result['industry']}")
            else:
                print(f"   ✗ Industry: Not found")
            
            if result.get('error_message'):
                print(f"   Error: {result['error_message']}")
            
            print()
    
    def save_to_file(self, filename: str):
        """Save results to JSON file."""
        output = {
            'test_date': self.start_time.isoformat(),
            'summary': self.generate_summary(),
            'results': self.results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Test results saved to {filename}")


def test_single_website(website: Dict) -> Dict:
    """
    Test crawler on a single website.
    
    Args:
        website: Dictionary with url, category, company_name
        
    Returns:
        Test result dictionary
    """
    logger.info(f"Testing: {website['url']}")
    
    try:
        # Initialize crawler
        crawler = CrawlerEngine(
            root_url=website['url'],
            crawl_settings={'timeout': 30},
            user_agent_policy="CrawlerBot/1.0 (Phase1 Test)",
            robots_policy="respect",
            exclude_patterns=[]
        )
        
        # Crawl the website
        result = crawler.crawl()
        
        # Add expected values for comparison
        result['expected_category'] = website['category']
        result['expected_company_name'] = website['company_name']
        
        # Clean up
        crawler.close()
        
        logger.info(f"✓ Successfully crawled: {website['url']}")
        return result
        
    except Exception as e:
        logger.error(f"✗ Failed to crawl {website['url']}: {e}")
        return {
            'url': website['url'],
            'crawl_status': 'error',
            'error_message': str(e),
            'expected_category': website['category'],
            'expected_company_name': website['company_name']
        }


def run_tests(limit: int = None) -> TestReport:
    """
    Run tests on all sample websites.
    
    Args:
        limit: Optional limit on number of websites to test
        
    Returns:
        TestReport instance with all results
    """
    report = TestReport()
    
    test_sites = TEST_WEBSITES[:limit] if limit else TEST_WEBSITES
    
    print(f"\nStarting Phase 1 Crawler Tests on {len(test_sites)} websites...\n")
    
    for i, website in enumerate(test_sites, 1):
        print(f"[{i}/{len(test_sites)}] Testing {website['url']}...")
        result = test_single_website(website)
        report.add_result(result)
    
    return report


def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 1 Crawler Test Suite')
    parser.add_argument('--limit', type=int, help='Limit number of websites to test')
    parser.add_argument('--output', type=str, default='test_results.json', 
                        help='Output file for results (default: test_results.json)')
    parser.add_argument('--verbose', action='store_true', 
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run tests
    report = run_tests(limit=args.limit)
    
    # Print results
    report.print_summary()
    report.print_detailed_results()
    
    # Save to file
    report.save_to_file(args.output)
    
    print(f"\n✓ Test complete! Results saved to {args.output}")


if __name__ == "__main__":
    main()