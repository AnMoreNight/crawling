"""
Optimized Company Name Extraction Module
Improved extraction with better heuristics for Japanese and English companies
"""

import re
import logging
from typing import List, Optional, Dict, Tuple
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class OptimizedCompanyNameExtractor:
    # Legal entity suffixes for normalization
    LEGAL_SUFFIXES = [
        '株式会社', '有限会社', '合同会社', '合資会社', '合名会社',
        '一般社団法人', '一般財団法人', '公益社団法人', '公益財団法人', '特定非営利活動法人',
        'Inc.', 'LLC', 'Ltd.', 'Co.', 'Corp.', 'G.K.', 'Y.K.'
    ]

    JAPANESE_LEGAL_ENTITIES = [
        '株式会社', '有限会社', '合同会社', '合資会社', '合名会社',
        '一般社団法人', '一般財団法人', '公益社団法人', '公益財団法人', '特定非営利活動法人',
    ]

    JUNK_KEYWORDS = [
        'ウェブサイト', 'ホームページ', 'サイト', 'サービス', 'ページ', '公式',
        'official', 'Home', 'Top', 'Welcome', '結婚', '婚活', 'Wedding', 'Marriage',
        'お気軽に', 'お問い合わせ', 'サポート', '相談', '予約'
    ]

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize company name for comparison."""
        if not name:
            return ''
        name = name.strip()
        # Remove legal suffixes
        for suffix in OptimizedCompanyNameExtractor.LEGAL_SUFFIXES:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
        # Remove symbols and whitespace
        name = re.sub(r'[\s\|｜\-\–\—\~\～\「\」\'"""'']', '', name)
        return name

    @staticmethod
    def _fuzzy_match(target: str, candidates: list) -> Optional[str]:
        """Return the candidate with highest similarity to target."""
        import difflib
        if not target or not candidates:
            return None
        norm_target = OptimizedCompanyNameExtractor._normalize_name(target)
        norm_candidates = [OptimizedCompanyNameExtractor._normalize_name(c) for c in candidates]
        matches = difflib.get_close_matches(norm_target, norm_candidates, n=1, cutoff=0.7)
        if matches:
            idx = norm_candidates.index(matches[0])
            return candidates[idx]
        return None

    @staticmethod
    def _is_valid_company_name(text: str) -> bool:
        """Check if text is likely a valid company name."""
        if not text or len(text) < 2 or len(text) > 100:
            return False
        
        # Contains too many junk keywords
        for keyword in OptimizedCompanyNameExtractor.JUNK_KEYWORDS:
            if keyword in text and len(text) < len(keyword) * 2:
                return False
        
        return True

    @staticmethod
    def _score_candidate(text: str) -> int:
        """Score a candidate name. Higher is better."""
        score = 0
        
        # Prefer shorter names (more likely to be actual company name)
        if len(text) <= 30:
            score += 10
        elif len(text) <= 50:
            score += 5
        
        # Prefer candidates with legal entity patterns
        for pattern in OptimizedCompanyNameExtractor.JAPANESE_LEGAL_ENTITIES:
            if pattern in text:
                score += 20
                break
        
        # Prefer Japanese katakana/hiragana names (common for companies)
        if re.search(r'[\u30a0-\u30ff\u3040-\u309f]', text):
            score += 8
        
        # Penalize if contains too many symbols/separators
        if len(re.findall(r'[|｜\-\–\—]', text)) > 2:
            score -= 10
        
        # Penalize if contains junk keywords
        for keyword in OptimizedCompanyNameExtractor.JUNK_KEYWORDS:
            if keyword in text:
                score -= 5
        
        return score

    @staticmethod
    def _extract_from_title(title: str) -> Optional[str]:
        """
        Extract company name from title tag.
        Title format: "Company Name | Service | Other Info"
        """
        if not title:
            return None
        
        title = title.strip()
        
        # Japanese and common separators - check longest first
        separators = ['｜', '|', '—', '–', '〜', '～', '\\', '/', '-']
        
        for sep in separators:
            if sep in title:
                parts = title.split(sep)
                company_part = parts[0].strip()
                
                # Remove junk keywords
                for keyword in OptimizedCompanyNameExtractor.JUNK_KEYWORDS:
                    if keyword in company_part:
                        company_part = company_part.split(keyword)[0].strip()
                
                if OptimizedCompanyNameExtractor._is_valid_company_name(company_part):
                    return company_part
        
        # No separator found
        if OptimizedCompanyNameExtractor._is_valid_company_name(title):
            for keyword in OptimizedCompanyNameExtractor.JUNK_KEYWORDS:
                if keyword in title:
                    return None
            return title
        
        return None

    @staticmethod
    def extract_company_name(html_content: str, reference_name: Optional[str] = None, 
                            log_candidates: Optional[list] = None) -> Optional[str]:
        """
        Extract company name from HTML content with improved heuristics.
        
        Args:
            html_content: HTML content to parse
            reference_name: Reference name for fuzzy matching
            log_candidates: List to append all candidates to
            
        Returns:
            Company name or None if not found
        """
        if not html_content:
            return None
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            candidates = []
            
            # 1. Title tag
            title = soup.find('title')
            if title and title.string:
                extracted = OptimizedCompanyNameExtractor._extract_from_title(title.string.strip())
                if extracted:
                    candidates.append((extracted, 'title'))
            
            # 2. og:title meta
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                text = og_title['content'].strip()
                if OptimizedCompanyNameExtractor._is_valid_company_name(text):
                    candidates.append((text, 'og:title'))
            
            # 3. h1 tag
            h1 = soup.find('h1')
            if h1 and h1.string:
                text = h1.string.strip()
                if OptimizedCompanyNameExtractor._is_valid_company_name(text):
                    candidates.append((text, 'h1'))
            
            # 4. Common class selectors
            for selector in ['site-title', 'company-name', 'brand', 'logo-text', 'company-logo', 'brand-name']:
                element = soup.find(class_=selector)
                if element:
                    text = element.get_text(strip=True) if element else None
                    if text and OptimizedCompanyNameExtractor._is_valid_company_name(text):
                        candidates.append((text, f'class:{selector}'))
            
            # 5. JSON-LD structured data
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    import json
                    data = json.loads(script.string) if script.string else None
                    if not data:
                        continue
                    
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if isinstance(item, dict):
                            if item.get('@type') in ['Organization', 'LocalBusiness', 'Corporation']:
                                name = item.get('name')
                                if name and OptimizedCompanyNameExtractor._is_valid_company_name(str(name)):
                                    candidates.append((str(name).strip(), 'json-ld'))
                except Exception:
                    continue
            
            # 6. Meta tags
            for meta_name in ['organization', 'business', 'author', 'publisher', 'company']:
                meta = soup.find('meta', attrs={'name': meta_name})
                if meta and meta.get('content'):
                    text = meta['content'].strip()
                    if OptimizedCompanyNameExtractor._is_valid_company_name(text):
                        candidates.append((text, f'meta:{meta_name}'))
            
            # 7. Image alt attributes (for logos)
            for img in soup.find_all('img'):
                alt = img.get('alt', '').strip()
                if alt and len(alt) < 50 and not any(k in alt for k in ['icon', 'logo', 'image', '画像']):
                    if OptimizedCompanyNameExtractor._is_valid_company_name(alt):
                        candidates.append((alt, 'img:alt'))
            
            # 8. Japanese legal entity patterns in page text
            text = soup.get_text()
            for pattern in OptimizedCompanyNameExtractor.JAPANESE_LEGAL_ENTITIES:
                if pattern in text:
                    idx = text.find(pattern)
                    start = max(0, idx - 50)
                    segment = text[start:idx + len(pattern) + 20]
                    for line in segment.split('\n'):
                        if pattern in line:
                            line = line.strip()
                            if OptimizedCompanyNameExtractor._is_valid_company_name(line):
                                candidates.append((line, 'legal-entity-pattern'))
            
            # Remove duplicates
            seen = set()
            unique_candidates = []
            for text, source in candidates:
                normalized = OptimizedCompanyNameExtractor._normalize_name(text)
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    unique_candidates.append((text, source))
            
            # Log candidates if requested
            if log_candidates is not None:
                log_candidates.extend([c[0] for c in unique_candidates])
            
            # Fuzzy match to reference if provided
            if reference_name and unique_candidates:
                best = OptimizedCompanyNameExtractor._fuzzy_match(
                    reference_name, 
                    [c[0] for c in unique_candidates]
                )
                if best:
                    return best
            
            # Score and select best candidate
            if unique_candidates:
                scored = [(text, OptimizedCompanyNameExtractor._score_candidate(text)) 
                         for text, _ in unique_candidates]
                scored.sort(key=lambda x: x[1], reverse=True)
                
                # Return top candidate if it has positive score
                if scored[0][1] > 0:
                    return scored[0][0]
                # Otherwise return first valid candidate
                return scored[0][0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting company name: {e}")
            return None
    
    @staticmethod
    def extract_all_candidates(html_content: str) -> List[Dict[str, str]]:
        """
        Extract all possible company name candidates with sources.
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            List of dicts with 'name' and 'source' keys
        """
        candidates = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Title
            title = soup.find('title')
            if title and title.string:
                extracted = OptimizedCompanyNameExtractor._extract_from_title(title.string.strip())
                if extracted:
                    candidates.append({'name': extracted, 'source': 'title'})
            
            # h1
            h1 = soup.find('h1')
            if h1:
                text = h1.get_text(strip=True)
                if OptimizedCompanyNameExtractor._is_valid_company_name(text):
                    candidates.append({'name': text, 'source': 'h1'})
            
            # og:title
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                candidates.append({'name': og_title['content'].strip(), 'source': 'og:title'})
            
            # Remove duplicates
            seen = set()
            unique = []
            for c in candidates:
                normalized = OptimizedCompanyNameExtractor._normalize_name(c['name'])
                if normalized not in seen:
                    seen.add(normalized)
                    unique.append(c)
            
            return unique
            
        except Exception as e:
            logger.error(f"Error extracting candidates: {e}")
            return []


# Compatibility alias for older imports expecting this class name
# Some parts of the codebase import `EnhancedCompanyNameExtractor` —
# provide a thin alias to avoid ImportError without renaming the class.
EnhancedCompanyNameExtractor = OptimizedCompanyNameExtractor