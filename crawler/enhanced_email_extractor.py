"""
Enhanced Email Extraction Module
Focused on finding primary business contact emails
"""

import re
import logging
from typing import List, Optional, Set, Tuple
from urllib.parse import urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class EnhancedEmailExtractor:
    """Enhanced email extraction focused on business contact emails."""
    
    # Email regex pattern
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )
    
    # Common non-business email domains to exclude
    EXCLUDE_DOMAINS = {
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'aol.com', 'mail.com', 'protonmail.com', 'icloud.com',
        'qq.com', 'sina.com', 'gmail.jp', 'yahoo.co.jp'
    }
    
    # Priority keywords for business emails
    PRIORITY_KEYWORDS = [
        'contact', 'info', 'inquiry', 'business', 'support',
        'sales', 'support', 'hello', 'team',
        'お問い合わせ', '問い合わせ', 'info', 'contact'
    ]
    
    @staticmethod
    def extract_emails(html_content: str, domain: str = None) -> List[str]:
        """
        Extract business emails from HTML content.
        
        Args:
            html_content: HTML content to parse
            domain: Domain name for filtering (e.g., 'example.com')
            
        Returns:
            List of unique emails found
        """
        if not html_content:
            return []
        
        emails = set()
        
        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style', 'meta']):
                script.decompose()
            
            # Extract text content
            text = soup.get_text()
            
            # Find all email patterns
            found_emails = EnhancedEmailExtractor.EMAIL_PATTERN.findall(text)
            
            for email in found_emails:
                email_lower = email.lower()
                
                # Filter out common non-business domains
                domain_part = email_lower.split('@')[1]
                if domain_part in EnhancedEmailExtractor.EXCLUDE_DOMAINS:
                    continue
                
                # Filter out common no-reply emails
                if 'noreply' in email_lower or 'no-reply' in email_lower:
                    continue
                
                emails.add(email_lower)
            
            # Also check common contact attributes and elements
            emails.update(EnhancedEmailExtractor._extract_from_attributes(soup))
            
            return list(emails)
            
        except Exception as e:
            logger.error(f"Error extracting emails: {e}")
            return []
    
    @staticmethod
    def _extract_from_attributes(soup: BeautifulSoup) -> Set[str]:
        """Extract emails from HTML attributes."""
        emails = set()
        
        try:
            # Check mailto links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '').lower()
                if href.startswith('mailto:'):
                    email = href.replace('mailto:', '').split('?')[0].strip()
                    if '@' in email and '.' in email:
                        emails.add(email)
            
            # Check data attributes
            for element in soup.find_all(True):
                for attr in ['data-email', 'data-contact', 'data-mail']:
                    if element.has_attr(attr):
                        value = element.get(attr, '')
                        if '@' in value and '.' in value:
                            emails.add(value.lower())
            
        except Exception as e:
            logger.debug(f"Error extracting from attributes: {e}")
        
        return emails
    
    @staticmethod
    def get_best_email(emails: List[str]) -> Optional[str]:
        """
        Get the best email from list based on priority keywords.
        
        Args:
            emails: List of emails to score
            
        Returns:
            Best email or None if list empty
        """
        if not emails:
            return None
        
        if len(emails) == 1:
            return emails[0]
        
        # Score emails based on priority keywords
        scored = []
        for email in emails:
            score = 0
            local_part = email.split('@')[0].lower()
            
            # Check for priority keywords in local part
            for keyword in EnhancedEmailExtractor.PRIORITY_KEYWORDS:
                if keyword in local_part:
                    score += 10
            
            # Prefer shorter local parts (usually more professional)
            if len(local_part) < 10:
                score += 5
            
            # Prefer domain matching patterns
            if len(local_part) <= 20:
                score += 3
            
            scored.append((email, score))
        
        # Return highest scored email
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0]
