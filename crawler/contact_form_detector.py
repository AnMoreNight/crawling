"""
Contact Form URL Detection Module
Finds the best contact form URL for a website using multiple detection methods.
"""

import re
import logging
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ContactFormCandidate:
    """Represents a contact form candidate with scoring."""
    
    def __init__(self, url: str, score: float = 0.0, has_form: bool = False, keywords: List[str] = None):
        self.url = url
        self.score = score
        self.has_form = has_form
        self.keywords = keywords or []
        self.link_text = None
        self.has_email_fields = False
        self.in_header_footer = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'url': self.url,
            'score': round(self.score, 2),
            'has_form': self.has_form,
            'keywords': self.keywords
        }


class ContactFormDetector:
    """Detects contact form URLs on websites."""

    @staticmethod
    def _normalize_url_path(url: str) -> str:
        """Normalize URL path for comparison (remove trailing slashes, unify contact/index.html, etc)."""
        from urllib.parse import urlparse
        path = urlparse(url).path.lower()
        # Remove trailing slashes
        if path.endswith('/') and path != '/':
            path = path[:-1]
        # Unify common contact page patterns
        for pat in ['/index.html', '/index.htm', '/contactus.html', '/contact.html', '/inquiry.html']:
            if path.endswith(pat):
                path = path[:-len(pat)]
        return path

    @staticmethod
    def _fuzzy_path_match(target: str, candidates: list) -> Optional[str]:
        """Return the candidate URL with the highest path similarity to target."""
        import difflib
        if not target or not candidates:
            return None
        norm_target = ContactFormDetector._normalize_url_path(target)
        norm_candidates = [ContactFormDetector._normalize_url_path(c) for c in candidates]
        matches = difflib.get_close_matches(norm_target, norm_candidates, n=1, cutoff=0.7)
        if matches:
            idx = norm_candidates.index(matches[0])
            return candidates[idx]
        return None

    # Japanese keywords for contact pages
    JAPANESE_KEYWORDS = [
        'お問い合わせ',
        'お問合せ',
        '問い合わせ',
        'ご相談',
        '資料請求',
        '応募フォーム',
        'コンタクト',
        'お申し込み',
        'お問い合わせフォーム',
        '問い合わせフォーム',
    ]
    
    # English keywords for contact pages
    ENGLISH_KEYWORDS = [
        'contact',
        'inquiry',
        'inquiry',
        'support',
        'form',
        'request',
        'consultation',
    ]
    
    # URL pattern regex
    URL_PATTERN = re.compile(
        r'/(contact|inquiry|support|form|otoiawase|toiawase|contact-us|soudan|shiryou|oubo)(/|$)',
        re.I
    )
    
    # Email field patterns
    EMAIL_FIELD_PATTERNS = [
        r'type=["\']email["\']',
        r'name=["\'][^"\']*email[^"\']*["\']',
        r'id=["\'][^"\']*email[^"\']*["\']',
        r'placeholder=["\'][^"\']*email[^"\']*["\']',
    ]
    
    def __init__(self, fetcher=None, robots_checker=None):
        """
        Initialize contact form detector.
        
        Args:
            fetcher: PageFetcher instance for fetching pages
            robots_checker: RobotsChecker instance for robots.txt checking
        """
        self.fetcher = fetcher
        self.robots_checker = robots_checker
    
    def detect_contact_form_url(self, root_url: str, reference_url: Optional[str] = None, log_candidates: Optional[list] = None) -> Dict:
        """
        Detect the best contact form URL for a website.
        
        Args:
            root_url: Root URL of the website
            
        Returns:
            Dictionary with form_url, candidates, and remarks
        """
        try:
            # Step 1: Fetch root page and extract internal links
            if not self.fetcher:
                return {
                    'form_url': None,
                    'candidates': [],
                    'remarks': 'Fetcher not available'
                }
            
            content, status_code, final_url, error_message = self.fetcher.fetch_page(root_url)
            
            if not content or status_code != 200:
                return {
                    'form_url': None,
                    'candidates': [],
                    'remarks': f'Failed to fetch root page: {error_message or f"HTTP {status_code}"}'
                }
            
            # Extract internal links
            internal_links = self._extract_internal_links(content, root_url)
            logger.info(f"Found {len(internal_links)} internal links from {root_url}")
            
            # Step 2: Identify potential contact pages
            candidates = self._identify_contact_candidates(internal_links, content, root_url)
            logger.info(f"Identified {len(candidates)} contact page candidates")
            # Step 3 & 4: Fetch each candidate and score
            scored_candidates = []
            for candidate in candidates:
                scored = self._score_candidate(candidate, root_url)
                if scored:
                    scored_candidates.append(scored)
                    logger.debug(f"Candidate {scored.url}: score={scored.score:.2f}, has_form={scored.has_form}")
            # Log all candidates if requested
            if log_candidates is not None:
                log_candidates.extend([c.url for c in scored_candidates])
            # Step 5: Select best candidate
            result = {
                'form_url': None,
                'candidates': [c.to_dict() for c in scored_candidates],
                'remarks': ''
            }
            # Fuzzy/path match to reference if provided
            if reference_url:
                urls = [c.url for c in scored_candidates]
                best_url = self._fuzzy_path_match(reference_url, urls)
                if best_url:
                    best = next(c for c in scored_candidates if c.url == best_url)
                    result['form_url'] = best.url
                    result['remarks'] = self._generate_remarks(best, scored_candidates) + ' (fuzzy/path match)'
                    return result
            # Otherwise, use best score
            if scored_candidates:
                scored_candidates.sort(key=lambda x: x.score, reverse=True)
                best = scored_candidates[0]
                if best.score > 0:
                    result['form_url'] = best.url
                    result['remarks'] = self._generate_remarks(best, scored_candidates)
                    logger.info(f"Selected contact form URL: {best.url} (score: {best.score:.2f})")
                else:
                    result['remarks'] = 'No candidate scored above 0'
            else:
                result['remarks'] = 'No contact form candidates found'
            return result
            
        except Exception as e:
            logger.error(f"Error detecting contact form URL: {e}")
            return {
                'form_url': None,
                'candidates': [],
                'remarks': f'Error: {str(e)}'
            }
    
    def _extract_internal_links(self, html_content: str, base_url: str) -> Set[str]:
        """Extract all internal links from HTML content."""
        links = set()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            parsed_base = urlparse(base_url)
            base_domain = parsed_base.netloc
            
            # Find all anchor tags
            for tag in soup.find_all('a', href=True):
                href = tag['href']
                absolute_url = urljoin(base_url, href)
                
                # Only include HTTP/HTTPS URLs from same domain
                parsed = urlparse(absolute_url)
                if parsed.scheme in ['http', 'https']:
                    if parsed.netloc == base_domain:
                        links.add(absolute_url)
            
        except Exception as e:
            logger.error(f"Error extracting internal links: {e}")
        
        return links
    
    def _identify_contact_candidates(self, links: Set[str], html_content: str, base_url: str) -> List[ContactFormCandidate]:
        """Identify potential contact page URLs."""
        candidates = []
        seen_urls = set()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Check all links
            for link_tag in soup.find_all('a', href=True):
                href = link_tag['href']
                link_text = link_tag.get_text().strip()
                absolute_url = urljoin(base_url, href)
                
                if absolute_url in seen_urls:
                    continue
                
                # Check if URL matches pattern
                url_matches = bool(self.URL_PATTERN.search(absolute_url))
                
                # Check if link text matches keywords
                text_matches_jp = any(keyword in link_text for keyword in self.JAPANESE_KEYWORDS)
                text_matches_en = any(keyword.lower() in link_text.lower() for keyword in self.ENGLISH_KEYWORDS)
                
                # Check if URL path matches keywords
                url_path = urlparse(absolute_url).path.lower()
                path_matches_jp = any(keyword in url_path for keyword in self.JAPANESE_KEYWORDS)
                path_matches_en = any(keyword in url_path for keyword in self.ENGLISH_KEYWORDS)
                
                if url_matches or text_matches_jp or text_matches_en or path_matches_jp or path_matches_en:
                    keywords = []
                    if text_matches_jp:
                        keywords.extend([k for k in self.JAPANESE_KEYWORDS if k in link_text])
                    if text_matches_en:
                        keywords.extend([k for k in self.ENGLISH_KEYWORDS if k.lower() in link_text.lower()])
                    if url_matches:
                        keywords.append('url_pattern')
                    
                    candidate = ContactFormCandidate(
                        url=absolute_url,
                        keywords=keywords
                    )
                    candidate.link_text = link_text
                    candidates.append(candidate)
                    seen_urls.add(absolute_url)
            
            # Also check links directly for URL patterns
            for link_url in links:
                if link_url in seen_urls:
                    continue
                
                if self.URL_PATTERN.search(link_url):
                    candidate = ContactFormCandidate(
                        url=link_url,
                        keywords=['url_pattern']
                    )
                    candidates.append(candidate)
                    seen_urls.add(link_url)
            
        except Exception as e:
            logger.error(f"Error identifying contact candidates: {e}")
        
        return candidates
    
    def _score_candidate(self, candidate: ContactFormCandidate, root_url: str) -> Optional[ContactFormCandidate]:
        """Fetch candidate URL and score it."""
        try:
            # Check robots.txt if available
            if self.robots_checker:
                if not self.robots_checker.is_allowed(candidate.url, "respect"):
                    logger.debug(f"Robots.txt disallows: {candidate.url}")
                    return None
            
            # Fetch the candidate page
            content, status_code, final_url, error_message = self.fetcher.fetch_page(candidate.url)
            
            if not content or status_code != 200:
                logger.debug(f"Failed to fetch candidate {candidate.url}: {error_message or f'HTTP {status_code}'}")
                return None
            
            candidate.url = final_url or candidate.url
            
            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Score components
            
            # +0.6 for link text match
            if candidate.link_text:
                text_matches_jp = any(keyword in candidate.link_text for keyword in self.JAPANESE_KEYWORDS)
                text_matches_en = any(keyword.lower() in candidate.link_text.lower() for keyword in self.ENGLISH_KEYWORDS)
                if text_matches_jp or text_matches_en:
                    candidate.score += 0.6
            
            # +0.5 for URL keyword match
            if self.URL_PATTERN.search(candidate.url):
                candidate.score += 0.5
            
            # +0.8 for page contains <form>
            forms = soup.find_all('form')
            if forms:
                candidate.has_form = True
                candidate.score += 0.8
                
                # Check for email fields in forms
                form_html = str(soup)
                for pattern in self.EMAIL_FIELD_PATTERNS:
                    if re.search(pattern, form_html, re.I):
                        candidate.has_email_fields = True
                        candidate.score += 0.2
                        break
            
            # +0.3 for appears in header/footer
            if self._is_in_header_footer(content, candidate.url, root_url):
                candidate.in_header_footer = True
                candidate.score += 0.3
            
            return candidate
            
        except Exception as e:
            logger.error(f"Error scoring candidate {candidate.url}: {e}")
            return None
    
    def _is_in_header_footer(self, html_content: str, url: str, root_url: str) -> bool:
        """Check if URL appears in header/footer sections."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find header and footer
            header = soup.find('header') or soup.find('div', id='header') or soup.find('div', class_=re.compile(r'header', re.I))
            footer = soup.find('footer') or soup.find('div', id='footer') or soup.find('div', class_=re.compile(r'footer', re.I))
            
            sections = []
            if header:
                sections.append(header)
            if footer:
                sections.append(footer)
            
            # Check if URL is linked in header/footer
            for section in sections:
                if not section:
                    continue
                
                links = section.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    absolute_href = urljoin(root_url, href)
                    if absolute_href == url:
                        return True
            
        except Exception as e:
            logger.debug(f"Error checking header/footer: {e}")
        
        return False
    
    def _generate_remarks(self, best: ContactFormCandidate, all_candidates: List[ContactFormCandidate]) -> str:
        """Generate remarks explaining why this candidate was selected."""
        remarks_parts = []
        
        if best.has_form:
            remarks_parts.append("Contains form tag")
        else:
            remarks_parts.append("No form tag found")
        
        if best.keywords:
            remarks_parts.append(f"Keywords: {', '.join(best.keywords[:3])}")
        
        if best.has_email_fields:
            remarks_parts.append("Has email fields")
        
        if best.in_header_footer:
            remarks_parts.append("Found in header/footer")
        
        remarks_parts.append(f"Score: {best.score:.2f}")
        
        if len(all_candidates) > 1:
            remarks_parts.append(f"Selected from {len(all_candidates)} candidates")
        
        return "; ".join(remarks_parts)

