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
from .email_extractor import EmailExtractor
from .company_name_extractor import CompanyNameExtractor
from .industry_extractor import IndustryExtractor
from .contact_form_detector import ContactFormDetector

logger = logging.getLogger(__name__)


class CrawlerEngine:
    """
    Main crawler engine that orchestrates the crawling process.
    """
    
    def __init__(
        self,
        root_url: str,
        crawl_settings: Dict[str, int],
        user_agent_policy: str = "CrawlerBot/1.0",
        robots_policy: str = "respect",
        exclude_patterns: List[str] = None
    ):
        """
        Initialize crawler engine.
        
        Args:
            root_url: Root company URL to crawl (crawled once per input)
            crawl_settings: Dictionary with timeout
            user_agent_policy: User agent string
            robots_policy: "respect" or "ignore"
            exclude_patterns: List of URL patterns to exclude
        """
        self.root_url = root_url
        self.timeout = crawl_settings.get('timeout', 30)
        self.user_agent_policy = user_agent_policy
        self.robots_policy = robots_policy
        self.exclude_patterns = exclude_patterns or []
        
        # Initialize components
        self.fetcher = PageFetcher(
            timeout=self.timeout,
            user_agent=self.user_agent_policy
        )
        self.robots_checker = RobotsChecker(user_agent=self.user_agent_policy)
        
        logger.info(f"Initialized crawler for {root_url}")
        logger.info(f"Settings: timeout={self.timeout}, robots_policy={self.robots_policy}")
    
    def crawl(self, output_file: Optional[str] = None) -> Dict[str, any]:
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
        
        # Initialize result
        result = CrawlResult(
            url=final_url or url,
            http_status=status_code,
            robots_allowed=robots_allowed,
            crawl_status="error" if error_message else "success",
            error_message=error_message
        )
        
        # If fetch failed, return error result
        if not content or status_code != 200:
            if output_file:
                self._write_result(result, output_file)
            return result.to_dict()
        
        # Parse HTML
        parser = HTMLParser(final_url or url)
        
        # Extract features
        self._extract_email(result, parser, content)
        self._extract_inquiry_form(result, parser, content)
        self._extract_company_name(result, parser, content)
        self._extract_industry(result, parser, content)
        
        logger.info(f"Crawl completed for {url}")
        
        # Write to file if specified
        if output_file:
            self._write_result(result, output_file)
        
        return result.to_dict()
    
    def _extract_email(self, result: CrawlResult, parser: HTMLParser, content: str):
        """
        Extract email address from HTML content using advanced extraction.
        
        Args:
            result: CrawlResult object to update
            parser: HTMLParser instance
            content: HTML content to parse
        """
        try:
            extractor = EmailExtractor(
                base_url=result.url,
                use_playwright=True,
                validate_mx=False  # Set to True if MX validation needed
            )
            
            extraction_result = extractor.extract(content, result.url)
            
            if extraction_result.get('email'):
                result.email = extraction_result['email']
                confidence = extraction_result.get('confidence', 0.0)
                logger.info(f"Found email: {result.email} (confidence: {confidence:.2f})")
                
                # Log all candidates for audit
                candidates = extraction_result.get('candidates', [])
                if candidates:
                    logger.debug(f"Total email candidates found: {len(candidates)}")
                    for i, candidate in enumerate(candidates[:5], 1):  # Log top 5
                        logger.debug(
                            f"Candidate {i}: {candidate.get('email')} "
                            f"(method: {candidate.get('detection_method')}, "
                            f"score: {candidate.get('confidence', 0):.2f})"
                        )
            
            extractor.close()
        except Exception as e:
            logger.error(f"Error in advanced email extraction: {e}")
            # Fallback to basic extraction
            emails = parser.extract_emails(content)
            if emails:
                result.email = list(emails)[0]
                logger.info(f"Found email (fallback): {result.email}")
    
    def _extract_inquiry_form(self, result: CrawlResult, parser: HTMLParser, content: str):
        """
        Extract inquiry/contact form URL from HTML content using advanced detection.
        
        Args:
            result: CrawlResult object to update
            parser: HTMLParser instance
            content: HTML content to parse
        """
        try:
            # Use advanced contact form detector
            detector = ContactFormDetector(
                fetcher=self.fetcher,
                robots_checker=self.robots_checker
            )
            
            detection_result = detector.detect_contact_form_url(result.url)
            
            if detection_result.get('form_url'):
                result.inquiry_form_url = detection_result['form_url']
                remarks = detection_result.get('remarks', '')
                logger.info(f"Found contact form URL: {result.inquiry_form_url} ({remarks})")
                
                # Log candidates for audit
                candidates = detection_result.get('candidates', [])
                if candidates:
                    logger.debug(f"Total contact form candidates: {len(candidates)}")
                    for i, candidate in enumerate(candidates[:3], 1):
                        logger.debug(
                            f"Candidate {i}: {candidate.get('url')} "
                            f"(score: {candidate.get('score', 0):.2f}, "
                            f"has_form: {candidate.get('has_form', False)})"
                        )
        except Exception as e:
            logger.error(f"Error in advanced contact form detection: {e}")
            # Fallback to basic detection
            form_urls = parser.detect_forms(content)
            if form_urls:
                result.inquiry_form_url = form_urls[0]
                logger.info(f"Found inquiry form (fallback): {result.inquiry_form_url}")
    
    def _extract_company_name(self, result: CrawlResult, parser: HTMLParser, content: str):
        """
        Extract company name from HTML content.
        
        Args:
            result: CrawlResult object to update
            parser: HTMLParser instance
            content: HTML content to parse
        """
        try:
            # Use advanced company name extractor
            name_extractor = CompanyNameExtractor(
                base_url=result.url,
                fetcher=self.fetcher
            )
            
            name_result = name_extractor.extract(content, result.url)
            
            if name_result.get('company_name'):
                result.company_name = name_result['company_name']
                confidence = name_result.get('company_name_confidence', 0.0)
                source = name_result.get('company_name_source', 'unknown')
                logger.info(
                    f"Extracted company name: {result.company_name} "
                    f"(source: {source}, confidence: {confidence:.2f})"
                )
                
                # Log candidates for audit
                candidates = name_result.get('company_name_candidates', [])
                if candidates:
                    logger.debug(f"Total company name candidates: {len(candidates)}")
                    for i, candidate in enumerate(candidates[:3], 1):
                        logger.debug(
                            f"Candidate {i}: {candidate.get('value')} "
                            f"(source: {candidate.get('source')}, "
                            f"confidence: {candidate.get('confidence', 0):.2f})"
                        )
        except Exception as e:
            logger.error(f"Error in advanced company name extraction: {e}")
            # Fallback to basic extraction
            metadata = parser.extract_metadata(content)
            result.company_name = metadata.get('companyName')
            if result.company_name:
                logger.info(f"Extracted company name (fallback): {result.company_name}")
    
    def _extract_industry(self, result: CrawlResult, parser: HTMLParser, content: str):
        """
        Extract industry from HTML content.
        
        Args:
            result: CrawlResult object to update
            parser: HTMLParser instance
            content: HTML content to parse
        """
        try:
            # Use advanced industry extractor
            industry_extractor = IndustryExtractor(
                base_url=result.url,
                fetcher=self.fetcher
            )
            
            industry_result = industry_extractor.extract(content, result.url)
            
            if industry_result.get('industry'):
                result.industry = industry_result['industry']
                confidence = industry_result.get('industry_confidence', 0.0)
                source = industry_result.get('industry_source', 'unknown')
                logger.info(
                    f"Extracted industry: {result.industry} "
                    f"(source: {source}, confidence: {confidence:.2f})"
                )
                
                # Log candidates for audit
                candidates = industry_result.get('industry_candidates', [])
                if candidates:
                    logger.debug(f"Total industry candidates: {len(candidates)}")
                    for i, candidate in enumerate(candidates[:3], 1):
                        logger.debug(
                            f"Candidate {i}: {candidate.get('value')} "
                            f"(source: {candidate.get('source')}, "
                            f"confidence: {candidate.get('confidence', 0):.2f})"
                        )
        except Exception as e:
            logger.error(f"Error in advanced industry extraction: {e}")
            # Fallback to basic extraction
            metadata = parser.extract_metadata(content)
            result.industry = metadata.get('industry')
            if result.industry:
                logger.info(f"Extracted industry (fallback): {result.industry}")
    
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

