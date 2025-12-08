"""
Storage utilities
Handles crawl result formatting and storage.
"""

from datetime import datetime
from typing import Optional, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)


class CrawlResult:
    """Represents a crawl result."""
    
    def __init__(
        self,
        url: str,
        email: Optional[str] = None,
        inquiry_form_url: Optional[str] = None,
        company_name: Optional[str] = None,
        industry: Optional[str] = None,
        http_status: int = 0,
        robots_allowed: bool = True,
        crawl_status: str = "success",
        error_message: Optional[str] = None
    ):
        """
        Initialize crawl result.
        
        Args:
            url: Crawled URL
            email: Extracted email address
            inquiry_form_url: Detected inquiry form URL
            company_name: Extracted company name
            industry: Detected industry
            http_status: HTTP status code
            robots_allowed: Whether robots.txt allowed crawling
            crawl_status: "success", "error", or "retry"
            error_message: Error message if any
        """
        self.url = url
        self.email = email
        self.inquiry_form_url = inquiry_form_url
        self.company_name = company_name
        self.industry = industry
        self.http_status = http_status
        self.robots_allowed = robots_allowed
        self.last_crawled_at = datetime.utcnow()
        self.crawl_status = crawl_status
        self.error_message = error_message
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert crawl result to dictionary.
        
        Returns:
            Dictionary representation ready for JSON serialization
        """
        return {
            'url': self.url,
            'email': self.email,
            'inquiryFormUrl': self.inquiry_form_url,
            'companyName': self.company_name,
            'industry': self.industry,
            'httpStatus': self.http_status,
            'robotsAllowed': self.robots_allowed,
            'lastCrawledAt': self.last_crawled_at.isoformat(),
            'crawlStatus': self.crawl_status,
            'errorMessage': self.error_message
        }
    
    def to_json(self) -> str:
        """
        Convert crawl result to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


def store_crawl_result(result: CrawlResult, output_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Store crawl result to file or return as dictionary.
    
    Args:
        result: CrawlResult instance
        output_file: Optional file path to append result
        
    Returns:
        Dictionary representation of the result
    """
    result_dict = result.to_dict()
    
    if output_file:
        try:
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(result_dict, ensure_ascii=False) + '\n')
            logger.debug(f"Stored crawl result to {output_file}")
        except Exception as e:
            logger.error(f"Failed to store crawl result to {output_file}: {e}")
    
    return result_dict

