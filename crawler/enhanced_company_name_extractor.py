"""
Enhanced Company Name Extraction Module
Improved extraction with proper UTF-8 handling for Japanese names
"""

import re
import logging
from typing import List, Optional, Dict
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class EnhancedCompanyNameExtractor:
    """Extracts company names from websites with proper UTF-8 encoding."""
    
    # Japanese legal entity patterns
    JAPANESE_LEGAL_ENTITIES = [
        '株式会社',
        '有限会社',
        '合同会社',
        '合資会社',
        '合名会社',
        '一般社団法人',
        '一般財団法人',
        '公益社団法人',
        '公益財団法人',
        '特定非営利活動法人',
    ]
    
    @staticmethod
    def extract_company_name(html_content: str) -> Optional[str]:
        """
        Extract company name from HTML content.
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            Company name or None if not found
        """
        if not html_content:
            return None
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try multiple extraction methods in priority order
            
            # 1. Check title tag
            title = soup.find('title')
            if title and title.string:
                company_name = EnhancedCompanyNameExtractor._extract_from_title(title.string)
                if company_name:
                    return company_name
            
            # 2. Check og:title meta tag
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                company_name = EnhancedCompanyNameExtractor._extract_from_title(og_title['content'])
                if company_name:
                    return company_name
            
            # 3. Check h1 tag
            h1 = soup.find('h1')
            if h1 and h1.string:
                text = h1.string.strip()
                if len(text) > 2 and len(text) < 100:
                    return text
            
            # 4. Check site title or company name in common classes
            for selector in ['site-title', 'company-name', 'brand', 'logo-text']:
                element = soup.find(class_=selector)
                if element and element.string:
                    text = element.string.strip()
                    if text and len(text) > 2 and len(text) < 100:
                        return text
            
            # 5. Check Japanese legal entity patterns
            text = soup.get_text()
            for pattern in EnhancedCompanyNameExtractor.JAPANESE_LEGAL_ENTITIES:
                if pattern in text:
                    # Extract company name around the pattern
                    idx = text.find(pattern)
                    # Get text before pattern (usually company name)
                    start = max(0, idx - 50)
                    segment = text[start:idx + len(pattern) + 20]
                    
                    # Clean up the segment
                    lines = segment.split('\n')
                    for line in lines:
                        if pattern in line:
                            line = line.strip()
                            if len(line) > 2 and len(line) < 100:
                                return line
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting company name: {e}")
            return None
    
    @staticmethod
    def _extract_from_title(title: str) -> Optional[str]:
        """
        Extract company name from title tag.
        
        Title format is often: "Company Name | Service | Other Info"
        
        Args:
            title: Title string
            
        Returns:
            Extracted company name
        """
        if not title:
            return None
        
        title = title.strip()
        
        # Remove common suffixes
        remove_suffixes = ['|', '—', '–', '-', '\\', '/', '「', '」']
        
        for suffix in remove_suffixes:
            if suffix in title:
                parts = title.split(suffix)
                # Usually company name is first part
                company_part = parts[0].strip()
                if len(company_part) > 2 and len(company_part) < 100:
                    return company_part
        
        # If no separator found and title is reasonable length
        if len(title) > 2 and len(title) < 100:
            return title
        
        return None
    
    @staticmethod
    def extract_all_candidates(html_content: str) -> List[str]:
        """
        Extract all possible company name candidates.
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            List of company name candidates
        """
        candidates = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Collect from various sources
            sources = [
                ('title', soup.find('title')),
                ('h1', soup.find('h1')),
                ('og:title', soup.find('meta', property='og:title')),
                ('description', soup.find('meta', name='description')),
            ]
            
            for source_name, element in sources:
                if element:
                    if hasattr(element, 'string'):
                        text = element.string
                    elif hasattr(element, 'get'):
                        text = element.get('content')
                    else:
                        text = None
                    
                    if text:
                        text = text.strip()
                        if len(text) > 2 and len(text) < 150:
                            candidates.append(text)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_candidates = []
            for c in candidates:
                if c not in seen:
                    seen.add(c)
                    unique_candidates.append(c)
            
            return unique_candidates
            
        except Exception as e:
            logger.error(f"Error extracting candidates: {e}")
            return []
