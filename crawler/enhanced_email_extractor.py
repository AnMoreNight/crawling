"""
Upgraded Email Extraction Module
Advanced extraction with context awareness and company domain detection
"""

import re
import logging
from typing import List, Optional, Set, Tuple, Dict
from urllib.parse import urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class UpgradedEmailExtractor:
    """Advanced email extraction with context awareness and domain intelligence."""
    
    # Enhanced email regex (handles international domains)
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
        re.UNICODE
    )
    
    # Common non-business email domains to exclude
    EXCLUDE_DOMAINS = {
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'aol.com', 'mail.com', 'protonmail.com', 'icloud.com',
        'qq.com', 'sina.com', 'gmail.jp', 'yahoo.co.jp',
        '163.com', '126.com', '139.com', 'naver.com', 'daum.net'
    }
    
    # Strict reject patterns (automated/system emails)
    REJECT_PATTERNS = [
        'noreply', 'no-reply', 'no_reply', 'donotreply',
        'notification', 'alert', 'system', 'robot', 'bot',
        'automated', 'auto-reply', 'bounce'
    ]
    
    # Priority keywords for business/contact emails (fixed UTF-8)
    PRIORITY_KEYWORDS = {
        'en': [
            'contact', 'info', 'inquiry', 'business', 'support',
            'sales', 'hello', 'team', 'admin', 'representative',
            'manager', 'director', 'ceo', 'president', 'enquiry',
            'service', 'help', 'assistance', 'general'
        ],
        'ja': [
            'お問い合わせ', '問い合わせ', 'info', 'contact',
            'inquiry', 'support', '相談', '営業', 'sales'
        ]
    }
    
    # High-value page sections (contact-related)
    CONTACT_SECTIONS = [
        'contact', 'footer', 'inquiry', 'support', 'help',
        'about', 'company-info', 'company-contact', 'reach-us',
        'お問い合わせ', '問い合わせ', 'contact-us', 'get-in-touch'
    ]
    
    # Low-value page sections (author bios, comments, etc)
    LOW_VALUE_SECTIONS = [
        'comment', 'author', 'blog', 'article', 'post', 'news',
        'sidebar', 'related', 'social', 'follow'
    ]

    @staticmethod
    def _extract_domain_from_url(url: str) -> Optional[str]:
        """Extract domain from URL (e.g., 'example.com' from 'https://www.example.com')."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return None

    @staticmethod
    def _get_element_context_score(element) -> int:
        """
        Score based on where the email appears in the page.
        Higher score = more likely to be primary contact.
        """
        score = 0
        
        # Walk up the DOM tree to find parent sections
        parent = element.parent
        while parent:
            parent_str = str(parent).lower()
            parent_class = parent.get('class', [])
            parent_id = parent.get('id', '').lower()
            
            # Check for high-value sections
            for section in UpgradedEmailExtractor.CONTACT_SECTIONS:
                if (section in parent_class or section in parent_id or 
                    section in parent_str[:200]):  # Check early content
                    score += 25
                    break
            
            # Penalize low-value sections
            for section in UpgradedEmailExtractor.LOW_VALUE_SECTIONS:
                if section in parent_class or section in parent_id:
                    score -= 15
                    break
            
            parent = parent.parent
        
        return score

    @staticmethod
    def extract_emails(html_content: str, page_url: str = None) -> List[Dict[str, any]]:
        """
        Extract business emails with context and scoring.
        
        Args:
            html_content: HTML content to parse
            page_url: The page URL (for company domain detection)
            
        Returns:
            List of dicts with 'email', 'score', 'source' keys
        """
        if not html_content:
            return []
        
        emails_dict = {}  # email -> {score, sources, context_score}
        company_domain = None
        
        if page_url:
            company_domain = UpgradedEmailExtractor._extract_domain_from_url(page_url)
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove noise
            for element in soup(['script', 'style']):
                element.decompose()
            
            # 1. Extract from mailto links (high priority - explicit contact)
            for link in soup.find_all('a', href=True):
                href = link.get('href', '').lower()
                if href.startswith('mailto:'):
                    email = href.replace('mailto:', '').split('?')[0].strip()
                    if UpgradedEmailExtractor._is_valid_email(email):
                        context_score = UpgradedEmailExtractor._get_element_context_score(link)
                        UpgradedEmailExtractor._add_email(
                            emails_dict, email, 'mailto-link', context_score + 30
                        )
            
            # 2. Extract from data attributes
            for element in soup.find_all(True):
                for attr in ['data-email', 'data-contact', 'data-mail']:
                    if element.has_attr(attr):
                        email = element.get(attr, '').strip().lower()
                        if UpgradedEmailExtractor._is_valid_email(email):
                            context_score = UpgradedEmailExtractor._get_element_context_score(element)
                            UpgradedEmailExtractor._add_email(
                                emails_dict, email, f'data-{attr}', context_score + 20
                            )
            
            # 3. Extract from page text
            text = soup.get_text()
            for email_match in UpgradedEmailExtractor.EMAIL_PATTERN.finditer(text):
                email = email_match.group().lower()
                if UpgradedEmailExtractor._is_valid_email(email):
                    # Find the element containing this text
                    for element in soup.find_all(string=re.compile(re.escape(email))):
                        context_score = UpgradedEmailExtractor._get_element_context_score(element.parent)
                        UpgradedEmailExtractor._add_email(
                            emails_dict, email, 'text-content', context_score
                        )
                        break
            
            # 4. Score each email
            results = []
            for email, data in emails_dict.items():
                total_score = UpgradedEmailExtractor._calculate_email_score(
                    email, data, company_domain
                )
                results.append({
                    'email': email,
                    'score': total_score,
                    'context_score': data['context_score'],
                    'sources': data['sources']
                })
            
            # Sort by score
            results.sort(key=lambda x: x['score'], reverse=True)
            return results
            
        except Exception as e:
            logger.error(f"Error extracting emails: {e}")
            return []

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Check if email is valid format and not excluded."""
        if not email or '@' not in email or '.' not in email:
            return False
        
        try:
            domain = email.split('@')[1].lower()
            
            # Exclude personal domains
            if domain in UpgradedEmailExtractor.EXCLUDE_DOMAINS:
                return False
            
            # Exclude strict reject patterns
            for pattern in UpgradedEmailExtractor.REJECT_PATTERNS:
                if pattern in email.lower():
                    return False
            
            return True
        except Exception:
            return False

    @staticmethod
    def _add_email(emails_dict: Dict, email: str, source: str, context_score: int = 0):
        """Add email to tracking dict, updating scores."""
        if email not in emails_dict:
            emails_dict[email] = {
                'sources': [],
                'context_score': context_score
            }
        
        emails_dict[email]['sources'].append(source)
        # Use highest context score found
        emails_dict[email]['context_score'] = max(
            emails_dict[email]['context_score'], 
            context_score
        )

    @staticmethod
    def _calculate_email_score(email: str, data: Dict, company_domain: Optional[str] = None) -> int:
        """Calculate comprehensive score for an email."""
        score = data['context_score']  # Start with context score
        local_part = email.split('@')[0].lower()
        domain_part = email.split('@')[1].lower()
        
        # Priority keyword matching (both languages)
        all_keywords = (
            UpgradedEmailExtractor.PRIORITY_KEYWORDS.get('en', []) +
            UpgradedEmailExtractor.PRIORITY_KEYWORDS.get('ja', [])
        )
        for keyword in all_keywords:
            if keyword in local_part:
                score += 20
                break
        
        # Company domain detection (strong signal)
        if company_domain and company_domain in domain_part:
            score += 25
        
        # Shorter local parts preferred (more professional)
        if len(local_part) < 12:
            score += 10
        elif len(local_part) < 20:
            score += 5
        
        # Professional domain structure (has dash, multiple parts)
        if '-' in domain_part:
            score += 8
        
        # Multiple sources increase confidence
        if len(data['sources']) > 1:
            score += 10
        
        # Penalize very long/auto-generated looking addresses
        if len(local_part) > 30:
            score -= 5
        
        # Penalize generic catch-alls
        if local_part in ['admin', 'owner', 'webmaster', 'postmaster', 'mail']:
            score -= 10
        
        return score

    @staticmethod
    def get_best_email(results: List[Dict]) -> Optional[str]:
        """
        Get the single best email from extraction results.
        
        Args:
            results: List of dicts from extract_emails()
            
        Returns:
            Best email string or None
        """
        if not results:
            return None
        
        if len(results) == 1:
            return results[0]['email']
        
        # Return highest scored email
        return results[0]['email']

    @staticmethod
    def extract_all_emails(html_content: str, page_url: str = None) -> List[str]:
        """
        Simple wrapper to get all unique emails as strings.
        
        Args:
            html_content: HTML content to parse
            page_url: The page URL (optional)
            
        Returns:
            List of unique email addresses
        """
        results = UpgradedEmailExtractor.extract_emails(html_content, page_url)
        return [r['email'] for r in results]

    @staticmethod
    def get_contact_email(html_content: str, page_url: str = None) -> Optional[str]:
        """
        Convenience method to get the single best contact email.
        
        Args:
            html_content: HTML content to parse
            page_url: The page URL (optional)
            
        Returns:
            Best email string or None
        """
        results = UpgradedEmailExtractor.extract_emails(html_content, page_url)
        return UpgradedEmailExtractor.get_best_email(results)


# Compatibility alias for older imports expecting this class name
# Some modules import `EnhancedEmailExtractor`; provide an alias
EnhancedEmailExtractor = UpgradedEmailExtractor