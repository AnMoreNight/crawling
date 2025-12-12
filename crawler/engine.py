"""
Main crawler engine
Orchestrates the crawling process - crawls only the root URL once per input.
"""

from typing import Dict, Optional, List
import logging

from .fetcher import PageFetcher
from .parser import HTMLParser
from .robots import RobotsChecker
from .storage import CrawlResult
from .enhanced_email_extractor import EnhancedEmailExtractor
from .enhanced_company_name_extractor import EnhancedCompanyNameExtractor
from .contact_form_detector import ContactFormDetector
from .industry_extractor import IndustryExtractor

logger = logging.getLogger(__name__)


class CrawlerEngine:
    """
    Main crawler engine that orchestrates the crawling process.
    Crawls only the root URL once per input (no link following).
    """
    
    def __init__(
        self,
        root_url: str,
        crawl_settings: Dict[str, int] = None,
        user_agent_policy: str = "CrawlerBot/1.0",
        robots_policy: str = "respect",
        exclude_patterns: List[str] = None
    ):
        """
        Initialize crawler engine.
        
        Args:
            root_url: Root company URL to crawl (crawled once per input)
            crawl_settings: Dictionary with timeout (default: 30s)
            user_agent_policy: User agent string
            robots_policy: "respect" or "ignore"
            exclude_patterns: List of URL patterns to exclude
        """
        self.root_url = root_url
        if crawl_settings is None:
            crawl_settings = {'timeout': 30}
        self.timeout = crawl_settings.get('timeout', 30)
        self.user_agent_policy = user_agent_policy
        self.robots_policy = robots_policy
        self.exclude_patterns = exclude_patterns or []
        
        # Initialize components
        self.fetcher = PageFetcher(
            timeout=self.timeout,
            max_retries=3,
            user_agent=self.user_agent_policy
        )
        self.robots_checker = RobotsChecker(user_agent=self.user_agent_policy)
        self.parser = HTMLParser()  # Will set base_url when parsing
        
        logger.info(f"Initialized crawler for {root_url}")
        logger.info(f"Settings: timeout={self.timeout}, robots_policy={self.robots_policy}")
    
    def crawl(self, output_file: Optional[str] = None) -> Dict:
        """
        Crawl the root URL once and return result.
        
        Args:
            output_file: Optional file path to store result
            
        Returns:
            Single crawl result dictionary
        """
        logger.info(f"Starting crawl for {self.root_url}")
        
        url = self.root_url
        
        # Check exclude patterns
        if any(pattern in url for pattern in self.exclude_patterns):
            logger.warning(f"URL matches exclude pattern: {url}")
            result = CrawlResult(
                url=url,
                http_status=0,
                crawl_status="error",
                error_message="URL matches exclude pattern"
            )
            return result.to_dict()
        
        # Check robots.txt permission
        robots_allowed = self.robots_checker.is_allowed(url, self.robots_policy)
        if not robots_allowed:
            logger.warning(f"Robots.txt disallows crawling: {url}")
            result = CrawlResult(
                url=url,
                http_status=0,
                robots_allowed=False,
                crawl_status="error",
                error_message="Robots.txt disallows crawling"
            )
            return result.to_dict()
        
        logger.info(f"Crawling: {url}")
        
        # Fetch page
        content, status_code, final_url, error_message = self.fetcher.fetch_page(url)
        
        # Initialize result with final URL (after redirects)
        final_url_to_use = final_url or url
        result = CrawlResult(
            url=final_url_to_use,
            http_status=status_code,
            robots_allowed=robots_allowed,
            crawl_status="success" if (content and status_code == 200) else "error",
            error_message=error_message
        )
        
        # If fetch failed, return error result
        if not content or status_code != 200:
            logger.warning(f"Failed to fetch {url}: HTTP {status_code}")
            if output_file:
                self._write_result(result, output_file)
            return result.to_dict()
        
        # Parse HTML and extract information
        try:
            parser = HTMLParser(final_url_to_use)
            
            # Capture candidate containers
            email_candidates = []
            company_name_candidates = []
            form_candidates = []
            industry_candidates = []

            # Extract emails using enhanced extractor (capture all candidates)
            emails = EnhancedEmailExtractor.extract_emails(content)
            if emails:
                email_candidates.extend(emails)
                best_email = EnhancedEmailExtractor.get_best_email(emails)
                if best_email:
                    result.email = best_email
                    logger.info(f"Found email: {result.email}")
            result.email_candidates = email_candidates
            
            # Detect forms using ContactFormDetector (scored & candidate-aware)
            contact_detector = ContactFormDetector(fetcher=self.fetcher, robots_checker=self.robots_checker)
            form_result = contact_detector.detect_contact_form_url(final_url_to_use, reference_url=None, log_candidates=form_candidates)
            if form_result and form_result.get('form_url'):
                result.inquiry_form_url = form_result.get('form_url')
                logger.info(f"Found inquiry form: {result.inquiry_form_url}")
            # Attach candidates (list of candidate dicts)
            result.inquiry_form_candidates = form_result.get('candidates', []) if isinstance(form_result, dict) else []
            # Also keep raw form candidate URLs list
            result.inquiry_form_raw_candidates = [c.get('url') for c in result.inquiry_form_candidates]
            # Add any logged form candidate URLs
            if form_candidates:
                # extend the stored candidates list with unique URLs
                for u in form_candidates:
                    if u not in result.inquiry_form_raw_candidates:
                        result.inquiry_form_raw_candidates.append(u)
            
            # Extract company name using enhanced extractor (capture candidates)
            company_name = EnhancedCompanyNameExtractor.extract_company_name(content, reference_name=None, log_candidates=company_name_candidates)
            if company_name:
                result.company_name = company_name
                logger.info(f"Found company name: {result.company_name}")
            result.company_name_candidates = company_name_candidates
            
            # Extract industry using IndustryExtractor (multi-source, candidate logging)
            industry_extractor = IndustryExtractor(final_url_to_use, fetcher=self.fetcher)
            industry_result = industry_extractor.extract(content, final_url=final_url_to_use, log_candidates=industry_candidates)
            if industry_result and industry_result.get('industry'):
                result.industry = industry_result.get('industry')
                logger.info(f"Found industry: {result.industry}")
            # attach industry candidate list
            result.industry_candidates = industry_result.get('industry_candidates', []) if isinstance(industry_result, dict) else []
            # also log simple candidate strings if extractor provided them
            if industry_candidates:
                # merge unique simple strings into industry_candidates field
                existing_vals = {c.get('value') for c in result.industry_candidates if isinstance(c, dict) and c.get('value')}
                for val in industry_candidates:
                    if val not in existing_vals:
                        result.industry_candidates.append({'value': val, 'source': 'logged', 'confidence': 0.0})
                
        except Exception as e:
            logger.error(f"Error parsing HTML for {url}: {e}")
            result.error_message = f"Parsing error: {str(e)}"
            result.crawl_status = "error"
        
        logger.info(f"Crawl completed for {url}")
        
        # Write to file if specified
        if output_file:
            self._write_result(result, output_file)
        
        return result.to_dict()
    
    def _write_result(self, result: CrawlResult, output_file: str):
        """Write result to output file."""
        import json
        try:
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(result.to_dict(), ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"Failed to write result to {output_file}: {e}")
    
    def close(self):
        """Clean up resources."""
        self.fetcher.close()

