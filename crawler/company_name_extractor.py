"""
Company Name Extraction Module for Japanese Corporate Websites
Implements multiple extraction methods with confidence scoring.
"""

import re
import unicodedata
import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class CompanyNameCandidate:
    """Represents a company name candidate with metadata."""
    
    def __init__(self, value: str, source: str, confidence: float):
        self.value = value
        self.source = source
        self.confidence = confidence
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'value': self.value,
            'source': self.source,
            'confidence': self.confidence
        }


class CompanyNameExtractor:
    """Extracts company names from Japanese corporate websites."""
    
    # Japanese legal entity patterns
    LEGAL_ENTITY_PATTERNS = [
        r'株式会社',
        r'有限会社',
        r'合同会社',
        r'合資会社',
        r'合名会社',
        r'一般社団法人',
        r'一般財団法人',
        r'公益社団法人',
        r'公益財団法人',
        r'特定非営利活動法人',
        r'学校法人',
        r'医療法人',
        r'社会医療法人',
        r'社会福祉法人',
        r'宗教法人',
    ]
    
    # Legal entity regex pattern
    LEGAL_ENTITY_REGEX = re.compile(
        r'(株式会社|有限会社|合同会社|合資会社|合名会社|一般社団法人|一般財団法人|'
        r'公益社団法人|公益財団法人|特定非営利活動法人|学校法人|医療法人|'
        r'社会医療法人|社会福祉法人|宗教法人)'
        r'[A-Za-z0-9一-龥ぁ-んァ-ン・ー\s]+'
    )
    
    # Suffixes to clean
    CLEAN_SUFFIXES = [
        r'\s*[|｜]\s*公式サイト',
        r'\s*[|｜]\s*Official',
        r'\s*-\s*Home',
        r'\s*-\s*TOP',
        r'\s*トップ',
        r'\s*TOP',
        r'\s*ホーム',
        r'\s*Home',
        r'\s*-\s*企業名',
        r'\s*-\s*会社情報',
    ]
    
    # Company info page keywords
    COMPANY_INFO_KEYWORDS = [
        '会社概要',
        '会社情報',
        '企業情報',
        '企業概要',
        'About',
        'About us',
        'About Us',
        '会社について',
        '企業について',
    ]
    
    # Company name field keywords
    COMPANY_NAME_FIELDS = [
        '会社名',
        'Company Name',
        '法人名',
        '企業名',
        '商号',
        '名称',
    ]
    
    def __init__(self, base_url: str, fetcher=None):
        """
        Initialize company name extractor.
        
        Args:
            base_url: Base URL of the website
            fetcher: PageFetcher instance for fetching company profile pages
        """
        self.base_url = base_url
        self.fetcher = fetcher
        self.parsed_base = urlparse(base_url)
        self.domain = self.parsed_base.netloc
    
    def extract(self, html_content: str, final_url: Optional[str] = None) -> Dict:
        """
        Extract company name using all methods in priority order.
        
        Args:
            html_content: HTML content to parse
            final_url: Final URL after redirects
            
        Returns:
            Dictionary with company_name, source, confidence, and candidates
        """
        url = final_url or self.base_url
        candidates: List[CompanyNameCandidate] = []
        
        # 1. Extract from header image alt text (highest priority)
        header_image_result = self._extract_from_header_image_alt(html_content, url)
        if header_image_result:
            candidates.append(header_image_result)
            print(f"Candidate from header image alt: {header_image_result}")

        # 2. Extract from metadata
        metadata_result = self._extract_from_metadata(html_content, url)
        if metadata_result:
            candidates.append(metadata_result)
            print(f"Candidate from metadata: {metadata_result}")

        # 3. Extract from header/footer
        header_footer_result = self._extract_from_header_footer(html_content, url)
        if header_footer_result:
            candidates.append(header_footer_result)
            print(f"Candidate from header/footer: {header_footer_result}")

        # 4. Extract from company profile page
        profile_result = self._extract_from_company_profile_page(html_content, url)
        if profile_result:
            candidates.append(profile_result)
            print(f"Candidate from company profile page: {profile_result}")

        # 5. Extract from main text (NER-like)
        text_result = self._extract_from_text(html_content, url)
        if text_result:
            candidates.append(text_result)
            print(f"Candidate from main text: {text_result}")

        # 6. Domain fallback (last resort)
        domain_result = self._domain_fallback(url)
        if domain_result:
            candidates.append(domain_result)
            print(f"Candidate from domain fallback: {domain_result}")
        
        # Select best candidate (highest confidence)
        result = {
            'company_name': None,
            'company_name_source': None,
            'company_name_confidence': 0.0,
            'company_name_candidates': [c.to_dict() for c in candidates]
        }
        
        if candidates:
            # Sort by confidence (descending)
            candidates.sort(key=lambda x: x.confidence, reverse=True)
            best = candidates[0]
            
            result['company_name'] = best.value
            result['company_name_source'] = best.source
            result['company_name_confidence'] = best.confidence
            
            logger.info(
                f"Extracted company name: {best.value} "
                f"(source: {best.source}, confidence: {best.confidence:.2f})"
            )
        
        return result
    
    def _extract_from_metadata(self, html_content: str, url: str) -> Optional[CompanyNameCandidate]:
        """Extract company name from metadata tags."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Check <meta property="og:site_name">
            og_site_name = soup.find('meta', property='og:site_name')
            if og_site_name:
                name = og_site_name.get('content', '').strip()
                if name:
                    cleaned = self._clean_name(name)
                    if cleaned:
                        logger.debug(f"Found company name in og:site_name: {cleaned}")
                        return CompanyNameCandidate(cleaned, 'metadata', 0.9)
            
            # Check <meta name="application-name">
            app_name = soup.find('meta', attrs={'name': 'application-name'})
            if app_name:
                name = app_name.get('content', '').strip()
                if name:
                    cleaned = self._clean_name(name)
                    if cleaned:
                        logger.debug(f"Found company name in application-name: {cleaned}")
                        return CompanyNameCandidate(cleaned, 'metadata', 0.9)
            
            # Check <meta itemprop="name">
            itemprop_name = soup.find('meta', attrs={'itemprop': 'name'})
            if itemprop_name:
                name = itemprop_name.get('content', '').strip()
                if name:
                    cleaned = self._clean_name(name)
                    if cleaned:
                        logger.debug(f"Found company name in itemprop: {cleaned}")
                        return CompanyNameCandidate(cleaned, 'metadata', 0.9)
            
            # Check <title> (cleaned)
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
                cleaned = self._clean_name(title)
                if cleaned:
                    logger.debug(f"Found company name in title: {cleaned}")
                    return CompanyNameCandidate(cleaned, 'metadata', 0.9)
            
        except Exception as e:
            logger.error(f"Error extracting from metadata: {e}")
        
        return None
    
    def _extract_from_header_image_alt(self, html_content: str, url: str) -> Optional[CompanyNameCandidate]:
        """Extract company name from image alt text in header."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find header element
            header = soup.find('header') or soup.find('div', id='header') or soup.find('div', class_=re.compile(r'header', re.I))
            
            if not header:
                return None
            
            # Find images in header (logo images)
            images = header.find_all('img')
            
            for img in images:
                alt_text = img.get('alt', '').strip()
                if not alt_text:
                    continue
                
                # Check if alt text contains legal entity pattern
                if self.LEGAL_ENTITY_REGEX.search(alt_text):
                    # Extract the full match
                    match = self.LEGAL_ENTITY_REGEX.search(alt_text)
                    if match:
                        company_name = match.group(0).strip()
                        cleaned = self._clean_name(company_name)
                        if cleaned and self._is_valid_company_name(cleaned):
                            logger.debug(f"Found company name in header image alt: {cleaned}")
                            return CompanyNameCandidate(cleaned, 'header_image_alt', 0.95)
                
                # Also check if alt text itself looks like a company name
                cleaned = self._clean_name(alt_text)
                if cleaned and self._is_valid_company_name(cleaned):
                    # Check if it contains legal entity or Japanese characters
                    has_legal_entity = any(entity in cleaned for entity in ['株式会社', '有限会社', '合同会社', '合資会社', '合名会社'])
                    has_japanese = bool(re.search(r'[一-龥ぁ-んァ-ン]', cleaned))
                    
                    if has_legal_entity or has_japanese:
                        logger.debug(f"Found company name in header image alt (direct): {cleaned}")
                        return CompanyNameCandidate(cleaned, 'header_image_alt', 0.95)
            
        except Exception as e:
            logger.error(f"Error extracting from header image alt: {e}")
        
        return None
    
    def _extract_from_header_footer(self, html_content: str, url: str) -> Optional[CompanyNameCandidate]:
        """Extract company name from header/footer sections."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find header and footer elements
            header = soup.find('header') or soup.find('div', id='header') or soup.find('div', class_=re.compile(r'header', re.I))
            footer = soup.find('footer') or soup.find('div', id='footer') or soup.find('div', class_=re.compile(r'footer', re.I))
            
            sections = []
            if header:
                sections.append(header)
            if footer:
                sections.append(footer)
            
            # Search for legal entity patterns
            for section in sections:
                if not section:
                    continue
                
                text = section.get_text()
                
                # Look for Japanese legal entity patterns
                matches = self.LEGAL_ENTITY_REGEX.findall(text)
                if matches:
                    # Find full match including the entity name
                    full_matches = self.LEGAL_ENTITY_REGEX.finditer(text)
                    for match in full_matches:
                        company_name = match.group(0).strip()
                        cleaned = self._clean_name(company_name)
                        if cleaned and self._is_valid_company_name(cleaned):
                            logger.debug(f"Found company name in header/footer: {cleaned}")
                            return CompanyNameCandidate(cleaned, 'header_footer', 0.8)
                
                # Also check for copyright patterns: © 株式会社〇〇
                copyright_pattern = re.compile(r'[©©]\s*(株式会社|有限会社|合同会社)[A-Za-z0-9一-龥ぁ-んァ-ン・ー\s]+')
                copyright_matches = copyright_pattern.finditer(text)
                for match in copyright_matches:
                    company_name = match.group(0).replace('©', '').replace('©', '').strip()
                    cleaned = self._clean_name(company_name)
                    if cleaned and self._is_valid_company_name(cleaned):
                        logger.debug(f"Found company name in copyright: {cleaned}")
                        return CompanyNameCandidate(cleaned, 'header_footer', 0.8)
            
        except Exception as e:
            logger.error(f"Error extracting from header/footer: {e}")
        
        return None
    
    def _extract_from_company_profile_page(self, html_content: str, url: str) -> Optional[CompanyNameCandidate]:
        """Extract company name from company profile/info page."""
        if not self.fetcher:
            return None
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find links to company info pages
            company_info_url = None
            links = soup.find_all('a', href=True)
            
            for link in links:
                link_text = link.get_text().strip()
                href = link.get('href', '')
                
                # Check if link text matches company info keywords
                if any(keyword in link_text for keyword in self.COMPANY_INFO_KEYWORDS):
                    absolute_url = urljoin(url, href)
                    company_info_url = absolute_url
                    logger.debug(f"Found company info page link: {company_info_url}")
                    break
            
            if not company_info_url:
                return None
            
            # Fetch company profile page
            content, status_code, final_url, error_message = self.fetcher.fetch_page(company_info_url)
            
            if not content or status_code != 200:
                logger.warning(f"Failed to fetch company profile page: {company_info_url}")
                return None
            
            # Parse company profile page
            profile_soup = BeautifulSoup(content, 'html.parser')
            
            # Look for company name in table cells
            # Pattern: <th>会社名</th><td>株式会社〇〇</td>
            th_tags = profile_soup.find_all('th')
            for th in th_tags:
                th_text = th.get_text().strip()
                if any(field in th_text for field in self.COMPANY_NAME_FIELDS):
                    # Find corresponding td
                    td = th.find_next_sibling('td')
                    if not td:
                        # Try finding in parent row
                        tr = th.find_parent('tr')
                        if tr:
                            tds = tr.find_all('td')
                            if tds:
                                td = tds[0]
                    
                    if td:
                        company_name = td.get_text().strip()
                        cleaned = self._clean_name(company_name)
                        if cleaned and self._is_valid_company_name(cleaned):
                            logger.debug(f"Found company name in profile page: {cleaned}")
                            return CompanyNameCandidate(cleaned, 'company_profile_page', 0.85)
            
            # Also search for legal entity patterns in the page
            page_text = profile_soup.get_text()
            matches = self.LEGAL_ENTITY_REGEX.finditer(page_text)
            for match in matches:
                company_name = match.group(0).strip()
                cleaned = self._clean_name(company_name)
                if cleaned and self._is_valid_company_name(cleaned):
                    logger.debug(f"Found company name in profile page text: {cleaned}")
                    return CompanyNameCandidate(cleaned, 'company_profile_page', 0.85)
            
        except Exception as e:
            logger.error(f"Error extracting from company profile page: {e}")
        
        return None
    
    def _extract_from_text(self, html_content: str, url: str) -> Optional[CompanyNameCandidate]:
        """Extract company name from main text using NER-like heuristics."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Search in H1, H2, H3 tags first
            headings = soup.find_all(['h1', 'h2', 'h3'])
            for heading in headings:
                text = heading.get_text()
                matches = self.LEGAL_ENTITY_REGEX.finditer(text)
                for match in matches:
                    company_name = match.group(0).strip()
                    cleaned = self._clean_name(company_name)
                    if cleaned and self._is_valid_company_name(cleaned):
                        logger.debug(f"Found company name in heading: {cleaned}")
                        return CompanyNameCandidate(cleaned, 'text_ner', 0.6)
            
            # Search in body text
            body = soup.find('body')
            if body:
                text = body.get_text()
                # Prefer names starting with legal entities
                matches = self.LEGAL_ENTITY_REGEX.finditer(text)
                for match in matches:
                    company_name = match.group(0).strip()
                    cleaned = self._clean_name(company_name)
                    if cleaned and self._is_valid_company_name(cleaned):
                        logger.debug(f"Found company name in body text: {cleaned}")
                        return CompanyNameCandidate(cleaned, 'text_ner', 0.6)
            
        except Exception as e:
            logger.error(f"Error extracting from text: {e}")
        
        return None
    
    def _domain_fallback(self, url: str) -> Optional[CompanyNameCandidate]:
        """Fallback to domain-based company name."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Remove www. prefix
            domain = re.sub(r'^www\.', '', domain, flags=re.I)
            
            # Remove common TLDs
            domain = re.sub(r'\.(co\.jp|com|jp|net|org|co|biz)$', '', domain, flags=re.I)
            
            # Split by dots and take the main part
            parts = domain.split('.')
            main_part = parts[-1] if parts else domain
            
            # Replace hyphens with spaces
            name = main_part.replace('-', ' ').replace('_', ' ')
            
            # Title case
            name = name.title()
            
            if name and len(name) > 1:
                logger.debug(f"Using domain fallback: {name}")
                return CompanyNameCandidate(name, 'domain_fallback', 0.3)
            
        except Exception as e:
            logger.error(f"Error in domain fallback: {e}")
        
        return None
    
    def _clean_name(self, name: str) -> str:
        """Clean and normalize company name."""
        if not name:
            return ''
        
        # Normalize Japanese full/half width
        name = unicodedata.normalize('NFKC', name)
        
        # Remove common suffixes
        for suffix_pattern in self.CLEAN_SUFFIXES:
            name = re.sub(suffix_pattern, '', name, flags=re.I)
        
        # Clean whitespace
        name = re.sub(r'\s+', ' ', name)
        name = name.strip()
        
        # Remove leading/trailing punctuation
        name = re.sub(r'^[^\w\u4e00-\u9fff]+|[^\w\u4e00-\u9fff]+$', '', name)
        
        return name
    
    def _is_valid_company_name(self, name: str) -> bool:
        """Validate if name is a valid company name."""
        if not name or len(name) < 2:
            return False
        
        # Must contain at least one Japanese character or legal entity keyword
        has_japanese = bool(re.search(r'[一-龥ぁ-んァ-ン]', name))
        has_legal_entity = any(entity in name for entity in ['株式会社', '有限会社', '合同会社', '合資会社', '合名会社'])
        
        if not (has_japanese or has_legal_entity):
            # For non-Japanese names, check if it's not just generic text
            generic_patterns = [
                r'^(home|top|index|page|site|website)$',
                r'^(company|corporation|inc|ltd)$',
            ]
            for pattern in generic_patterns:
                if re.match(pattern, name, re.I):
                    return False
        
        # Avoid product names or service names (heuristic)
        product_keywords = ['サービス', 'サービス', 'product', 'service', 'solution']
        if any(keyword in name.lower() for keyword in product_keywords):
            return False
        
        return True

