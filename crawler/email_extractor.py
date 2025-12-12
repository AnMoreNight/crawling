"""
Advanced email extraction module
Implements multiple detection methods, normalization, validation, and scoring.
"""

import re
import html
import unicodedata
import json
import logging
from typing import List, Dict, Optional, Set, Tuple
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import socket
try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailCandidate:
    """Represents an email candidate with metadata."""
    
    def __init__(
        self,
        email: str,
        detection_method: str,
        source_url: str,
        selector: Optional[str] = None,
        context_snippet: Optional[str] = None,
        score: float = 0.0
    ):
        self.email = email
        self.detection_method = detection_method
        self.source_url = source_url
        self.selector = selector
        self.context_snippet = context_snippet
        self.score = score
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'email': self.email,
            'confidence': self.score,
            'source_url': self.source_url,
            'selector': self.selector,
            'detection_method': self.detection_method,
            'context_snippet': self.context_snippet
        }


class EmailExtractor:
    """Advanced email extractor with multiple detection methods."""
    
    # Basic email regex pattern
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )
    
    # Obfuscation patterns
    OBFUSCATION_PATTERNS = [
        (r'\[at\]', '@'),
        (r'\(at\)', '@'),
        (r'\s+at\s+', '@'),
        (r'\[dot\]', '.'),
        (r'\(dot\)', '.'),
        (r'\s+dot\s+', '.'),
        (r'\[AT\]', '@'),
        (r'\(AT\)', '@'),
        (r'\[DOT\]', '.'),
        (r'\(DOT\)', '.'),
    ]
    
    # JS assembly patterns
    JS_ASSEMBLY_PATTERNS = [
        re.compile(r'["\']([^"\']+)["\']\s*\+\s*["\']@["\']\s*\+\s*["\']([^"\']+)["\']'),
        re.compile(r'["\']([^"\']+)["\']\s*\+\s*["\']@["\']\s*\+\s*["\']([^"\']+)["\']'),
        re.compile(r'String\.fromCharCode\(64\)', re.I),  # @ symbol
    ]
    
    def __init__(self, base_url: str, use_playwright: bool = True, validate_mx: bool = False):
        """
        Initialize email extractor.
        
        Args:
            base_url: Base URL for resolving relative links
            use_playwright: Whether to use Playwright for JS rendering
            validate_mx: Whether to validate MX/A records (throttled)
        """
        self.base_url = base_url
        self.use_playwright = use_playwright
        self.validate_mx = validate_mx
        self.parsed_base = urlparse(base_url)
        self.domain = self.parsed_base.netloc
        
        # Playwright browser instance (lazy loaded)
        self._browser = None
        self._playwright = None
    
    def extract(self, html_content: str, final_url: Optional[str] = None, log_candidates: Optional[list] = None) -> Dict:
        """
        Extract emails with all detection methods.
        
        Args:
            html_content: HTML content to parse
            final_url: Final URL after redirects
            
        Returns:
            Dictionary with 'email' (top candidate) and 'candidates' (all candidates)
        """
        url = final_url or self.base_url
        candidates: List[EmailCandidate] = []
        # Check if page likely uses JS for email (heuristic)
        needs_js_rendering = self._needs_js_rendering(html_content)
        # If no candidates found and page likely uses JS, render with Playwright
        if needs_js_rendering and self.use_playwright:
            try:
                rendered_html = self._render_with_playwright(url)
                if rendered_html:
                    html_content = rendered_html
                    logger.info(f"Rendered page with Playwright for {url}")
            except Exception as e:
                logger.warning(f"Failed to render with Playwright: {e}")
        # Run detectors in order
        candidates.extend(self._detect_mailto_links(html_content, url))
        candidates.extend(self._detect_plain_emails(html_content, url))
        candidates.extend(self._detect_obfuscated_emails(html_content, url))
        candidates.extend(self._detect_jsonld_schema(html_content, url))
        candidates.extend(self._detect_form_placeholders(html_content, url))
        candidates.extend(self._detect_js_assembly(html_content, url))
        # Fallback: if no candidates, try all <a> and visible text again
        if not candidates:
            candidates.extend(self._detect_mailto_links(html_content, url))
            candidates.extend(self._detect_plain_emails(html_content, url))
        # Normalize all candidates
        normalized_candidates = []
        seen_emails = set()
        for candidate in candidates:
            normalized = self._normalize_email(candidate.email)
            if normalized and normalized not in seen_emails:
                seen_emails.add(normalized)
                candidate.email = normalized
                normalized_candidates.append(candidate)
        # Validate candidates
        validated_candidates = []
        for candidate in normalized_candidates:
            if self._validate_email(candidate.email):
                validated_candidates.append(candidate)
        # Score candidates
        scored_candidates = []
        for candidate in validated_candidates:
            score = self._score_candidate(candidate, html_content)
            candidate.score = score
            scored_candidates.append(candidate)
            logger.info(
                f"Email candidate: {candidate.email} "
                f"(method: {candidate.detection_method}, score: {score:.2f})"
            )
        # Sort by score (descending)
        scored_candidates.sort(key=lambda x: x.score, reverse=True)
        # Log all candidates if requested
        if log_candidates is not None:
            log_candidates.extend([c.email for c in scored_candidates])
        # Return top candidate if score >= 0.6
        result = {
            'email': None,
            'confidence': 0.0,
            'candidates': [c.to_dict() for c in scored_candidates]
        }
        if scored_candidates and scored_candidates[0].score >= 0.6:
            top = scored_candidates[0]
            result['email'] = top.email
            result['confidence'] = top.score
            logger.info(f"Selected top email: {top.email} (confidence: {top.score:.2f})")
        return result
    
    def _needs_js_rendering(self, html_content: str) -> bool:
        """Check if page likely builds email via JS."""
        # Heuristics: check for script tags, React/Vue indicators, etc.
        has_scripts = bool(re.search(r'<script[^>]*>', html_content, re.I))
        has_react = 'react' in html_content.lower() or 'React' in html_content
        has_vue = 'vue' in html_content.lower() or 'Vue' in html_content
        has_angular = 'angular' in html_content.lower() or 'ng-' in html_content
        
        # Check if initial detectors find no candidates
        initial_candidates = (
            self._detect_mailto_links(html_content, self.base_url) +
            self._detect_plain_emails(html_content, self.base_url)
        )
        
        return (has_scripts or has_react or has_vue or has_angular) and len(initial_candidates) == 0
    
    def _render_with_playwright(self, url: str) -> Optional[str]:
        """Render page with Playwright to execute JavaScript."""
        try:
            from playwright.sync_api import sync_playwright
            
            if not self._playwright:
                self._playwright = sync_playwright().start()
            
            if not self._browser:
                self._browser = self._playwright.chromium.launch(headless=True)
            
            page = self._browser.new_page()
            page.goto(url, wait_until='networkidle', timeout=30000)
            content = page.content()
            page.close()
            
            return content
        except ImportError:
            logger.warning("Playwright not installed. Install with: pip install playwright && playwright install")
            return None
        except Exception as e:
            logger.error(f"Playwright rendering failed: {e}")
            return None
    
    def _detect_mailto_links(self, html_content: str, url: str) -> List[EmailCandidate]:
        """Detect emails from mailto: links."""
        candidates = []
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
            
            for link in mailto_links:
                href = link.get('href', '')
                # Extract email from mailto: link
                match = re.search(self.EMAIL_PATTERN, href)
                if match:
                    email = match.group()
                    context = link.get_text().strip()[:100] if link.get_text() else None
                    candidate = EmailCandidate(
                        email=email,
                        detection_method='mailto_link',
                        source_url=url,
                        selector=f"a[href^='mailto:']",
                        context_snippet=context
                    )
                    candidates.append(candidate)
                    logger.debug(f"Found mailto link: {email}")
        except Exception as e:
            logger.error(f"Error detecting mailto links: {e}")
        
        return candidates
    
    def _detect_plain_emails(self, html_content: str, url: str) -> List[EmailCandidate]:
        """Detect plain email addresses using regex."""
        candidates = []
        try:
            matches = self.EMAIL_PATTERN.findall(html_content)
            for email in matches:
                # Get context snippet
                context = self._get_context_snippet(html_content, email)
                candidate = EmailCandidate(
                    email=email,
                    detection_method='regex_plain',
                    source_url=url,
                    context_snippet=context
                )
                candidates.append(candidate)
                logger.debug(f"Found plain email: {email}")
        except Exception as e:
            logger.error(f"Error detecting plain emails: {e}")
        
        return candidates
    
    def _detect_obfuscated_emails(self, html_content: str, url: str) -> List[EmailCandidate]:
        """Detect obfuscated email patterns."""
        candidates = []
        try:
            # Try each obfuscation pattern
            for pattern, replacement in self.OBFUSCATION_PATTERNS:
                matches = re.finditer(pattern, html_content, re.I)
                for match in matches:
                    # Try to reconstruct email around the match
                    start = max(0, match.start() - 50)
                    end = min(len(html_content), match.end() + 50)
                    snippet = html_content[start:end]
                    
                    # Replace obfuscation tokens
                    deobfuscated = re.sub(pattern, replacement, snippet, flags=re.I)
                    
                    # Try to find email in deobfuscated snippet
                    email_match = self.EMAIL_PATTERN.search(deobfuscated)
                    if email_match:
                        email = email_match.group()
                        candidate = EmailCandidate(
                            email=email,
                            detection_method='obfuscated_pattern',
                            source_url=url,
                            context_snippet=snippet[:100]
                        )
                        candidates.append(candidate)
                        logger.debug(f"Found obfuscated email: {email}")
        except Exception as e:
            logger.error(f"Error detecting obfuscated emails: {e}")
        
        return candidates
    
    def _detect_jsonld_schema(self, html_content: str, url: str) -> List[EmailCandidate]:
        """Detect emails from JSON-LD and schema.org structured data."""
        candidates = []
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find JSON-LD scripts
            jsonld_scripts = soup.find_all('script', type='application/ld+json')
            for script in jsonld_scripts:
                try:
                    data = json.loads(script.string)
                    emails = self._extract_emails_from_json(data)
                    for email in emails:
                        candidate = EmailCandidate(
                            email=email,
                            detection_method='jsonld_schema',
                            source_url=url,
                            selector='script[type="application/ld+json"]'
                        )
                        candidates.append(candidate)
                        logger.debug(f"Found JSON-LD email: {email}")
                except (json.JSONDecodeError, TypeError):
                    continue
            
            # Check schema.org microdata
            schema_elements = soup.find_all(attrs={'itemtype': re.compile(r'schema\.org', re.I)})
            for element in schema_elements:
                email_attrs = element.find_all(attrs={'itemprop': re.compile(r'email', re.I)})
                for attr in email_attrs:
                    email = attr.get('content') or attr.get_text()
                    if self.EMAIL_PATTERN.match(email):
                        candidate = EmailCandidate(
                            email=email,
                            detection_method='schema_microdata',
                            source_url=url,
                            selector='[itemtype*="schema.org"]'
                        )
                        candidates.append(candidate)
                        logger.debug(f"Found schema.org email: {email}")
        except Exception as e:
            logger.error(f"Error detecting JSON-LD/schema emails: {e}")
        
        return candidates
    
    def _extract_emails_from_json(self, data: any, emails: Optional[Set[str]] = None) -> Set[str]:
        """Recursively extract emails from JSON structure."""
        if emails is None:
            emails = set()
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and self.EMAIL_PATTERN.match(value):
                    emails.add(value)
                elif isinstance(value, (dict, list)):
                    self._extract_emails_from_json(value, emails)
        elif isinstance(data, list):
            for item in data:
                self._extract_emails_from_json(item, emails)
        
        return emails
    
    def _detect_form_placeholders(self, html_content: str, url: str) -> List[EmailCandidate]:
        """Detect emails from form input placeholders."""
        candidates = []
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find input fields with email type or email-related placeholders
            email_inputs = soup.find_all('input', type='email')
            email_inputs.extend(soup.find_all('input', placeholder=re.compile(r'email', re.I)))
            
            for input_field in email_inputs:
                placeholder = input_field.get('placeholder', '')
                value = input_field.get('value', '')
                
                # Check placeholder
                if placeholder:
                    match = self.EMAIL_PATTERN.search(placeholder)
                    if match:
                        email = match.group()
                        candidate = EmailCandidate(
                            email=email,
                            detection_method='form_placeholder',
                            source_url=url,
                            selector='input[type="email"]'
                        )
                        candidates.append(candidate)
                        logger.debug(f"Found form placeholder email: {email}")
                
                # Check value
                if value:
                    match = self.EMAIL_PATTERN.search(value)
                    if match:
                        email = match.group()
                        candidate = EmailCandidate(
                            email=email,
                            detection_method='form_value',
                            source_url=url,
                            selector='input[type="email"]'
                        )
                        candidates.append(candidate)
        except Exception as e:
            logger.error(f"Error detecting form placeholders: {e}")
        
        return candidates
    
    def _detect_js_assembly(self, html_content: str, url: str) -> List[EmailCandidate]:
        """Detect emails assembled via JavaScript."""
        candidates = []
        try:
            # Find script tags
            soup = BeautifulSoup(html_content, 'html.parser')
            scripts = soup.find_all('script')
            
            for script in scripts:
                script_content = script.string
                if not script_content:
                    continue
                
                # Look for JS assembly patterns
                for pattern in self.JS_ASSEMBLY_PATTERNS:
                    matches = pattern.finditer(script_content)
                    for match in matches:
                        # Try to extract email parts
                        parts = match.groups()
                        if len(parts) >= 2:
                            # Attempt to reconstruct email
                            local_part = parts[0]
                            domain_part = parts[1] if len(parts) > 1 else ''
                            
                            if '@' not in local_part and domain_part:
                                potential_email = f"{local_part}@{domain_part}"
                                if self.EMAIL_PATTERN.match(potential_email):
                                    candidate = EmailCandidate(
                                        email=potential_email,
                                        detection_method='js_assembly',
                                        source_url=url,
                                        selector='script',
                                        context_snippet=script_content[match.start():match.end()+50]
                                    )
                                    candidates.append(candidate)
                                    logger.debug(f"Found JS-assembled email: {potential_email}")
        except Exception as e:
            logger.error(f"Error detecting JS assembly: {e}")
        
        return candidates
    
    def _normalize_email(self, email: str) -> Optional[str]:
        """Normalize email address."""
        if not email:
            return None
        
        # HTML entity decode
        normalized = html.unescape(email)
        
        # Unicode NFKC normalization
        normalized = unicodedata.normalize('NFKC', normalized)
        
        # Convert fullwidth characters to ASCII
        normalized = normalized.translate(str.maketrans(
            '０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ＠．',
            '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz@.'
        ))
        
        # Replace obfuscation tokens
        for pattern, replacement in self.OBFUSCATION_PATTERNS:
            normalized = re.sub(pattern, replacement, normalized, flags=re.I)
        
        # Convert to lowercase and strip
        normalized = normalized.lower().strip()
        
        # Remove mailto: prefix
        normalized = re.sub(r'^mailto:', '', normalized, flags=re.I)
        
        # Remove query parameters
        normalized = re.sub(r'\?.*$', '', normalized)
        
        # Basic validation
        if not self.EMAIL_PATTERN.match(normalized):
            return None
        
        # Punycode for IDN domains
        try:
            parts = normalized.split('@')
            if len(parts) == 2:
                local, domain = parts
                # Encode domain to punycode if needed
                domain = domain.encode('idna').decode('ascii')
                normalized = f"{local}@{domain}"
        except Exception:
            pass
        
        return normalized if len(normalized) > 5 else None
    
    def _validate_email(self, email: str) -> bool:
        """Validate email syntactically and optionally check MX records."""
        if not email:
            return False
        
        # Basic syntax validation
        if not self.EMAIL_PATTERN.match(email):
            return False
        
        # Check for common invalid patterns
        invalid_patterns = [
            r'example\.com',
            r'test@',
            r'@test',
            r'noreply',
            r'no-reply',
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, email, re.I):
                return False
        
        # Optional MX/A record validation (throttled)
        if self.validate_mx and DNS_AVAILABLE:
            try:
                domain = email.split('@')[1]
                # Check MX records
                try:
                    mx_records = dns.resolver.resolve(domain, 'MX')
                    if len(list(mx_records)) > 0:
                        return True
                except:
                    # Fallback to A record
                    try:
                        a_records = dns.resolver.resolve(domain, 'A')
                        if len(list(a_records)) > 0:
                            return True
                    except:
                        return False
            except Exception as e:
                logger.debug(f"MX validation failed for {email}: {e}")
                # Don't fail on validation errors, just log
                return True
        elif self.validate_mx and not DNS_AVAILABLE:
            logger.warning("DNS validation requested but dnspython not available")
        
        return True
    
    def _score_candidate(self, candidate: EmailCandidate, html_content: str) -> float:
        """Score email candidate based on various rules."""
        score = 0.0
        
        # Base scores by detection method
        method_scores = {
            'mailto_link': 40,
            'jsonld_schema': 30,
            'schema_microdata': 30,
            'regex_plain': 20,
            'form_placeholder': 15,
            'form_value': 15,
            'obfuscated_pattern': 10,
            'js_assembly': 5,
        }
        
        score += method_scores.get(candidate.detection_method, 10)
        
        # Footer bonus (+15)
        if self._is_in_footer(html_content, candidate.email):
            score += 15
        
        # Same domain bonus (+20)
        if self._is_same_domain(candidate.email):
            score += 20
        
        # Obfuscation penalty (-10)
        if candidate.detection_method == 'obfuscated_pattern':
            score -= 10
        
        # Normalize to 0-1 range (assuming max score around 100)
        score = max(0.0, min(1.0, score / 100.0))
        
        return score
    
    def _is_in_footer(self, html_content: str, email: str) -> bool:
        """Check if email appears in footer section."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            footer = soup.find('footer') or soup.find(id='footer') or soup.find(class_=re.compile(r'footer', re.I))
            if footer:
                return email.lower() in footer.get_text().lower()
        except:
            pass
        return False
    
    def _is_same_domain(self, email: str) -> bool:
        """Check if email domain matches page domain."""
        try:
            email_domain = email.split('@')[1]
            page_domain = self.domain.lstrip('www.')
            email_domain = email_domain.lstrip('www.')
            return email_domain == page_domain
        except:
            return False
    
    def _get_context_snippet(self, html_content: str, email: str, context_size: int = 50) -> str:
        """Get context snippet around email."""
        try:
            index = html_content.lower().find(email.lower())
            if index != -1:
                start = max(0, index - context_size)
                end = min(len(html_content), index + len(email) + context_size)
                snippet = html_content[start:end]
                # Clean up snippet
                snippet = re.sub(r'\s+', ' ', snippet)
                return snippet.strip()
        except:
            pass
        return ''
    
    def close(self):
        """Clean up resources."""
        if self._browser:
            try:
                self._browser.close()
            except:
                pass
        if self._playwright:
            try:
                self._playwright.stop()
            except:
                pass

