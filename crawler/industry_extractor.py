"""
Upgraded Industry Extraction Module
Advanced industry detection with proper UTF-8, English support, and better heuristics
"""

import re
import json
import logging
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class IndustryCandidate:
    """Represents an industry candidate with confidence."""
    
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


class UpgradedIndustryExtractor:
    """Advanced industry extraction with multilingual and contextual support."""
    
    # Comprehensive industry keywords mapping (English and Japanese, properly encoded)
    INDUSTRY_KEYWORDS = {
        'technology': {
            'en': ['IT', 'software', 'technology', 'tech', 'developer', 'development',
                   'ai', 'artificial intelligence', 'machine learning', 'cloud', 'saas',
                   'web development', 'app development', 'programming', 'system integration',
                   'information technology', 'digital', 'cyber', 'data science'],
            'ja': ['IT', '情報技術', 'ソフトウェア', 'テクノロジー', 'システム開発',
                   'クラウド', 'AI', '人工知能', '情報システム', 'システムインテグレーション',
                   'ウェブ開発', 'アプリ開発', 'プログラミング', 'デジタル']
        },
        'finance': {
            'en': ['finance', 'financial', 'banking', 'bank', 'insurance', 'investment',
                   'securities', 'asset management', 'mortgage', 'credit', 'fintech',
                   'wealth management', 'trading', 'forex'],
            'ja': ['金融', '銀行', '保険', '証券', '投資', '資産運用', 'ファイナンス',
                   '信用金庫', '信用組合', '証券会社', 'ファイナンシャル']
        },
        'retail': {
            'en': ['retail', 'shop', 'store', 'ecommerce', 'e-commerce', 'online',
                   'shopping', 'merchandise', 'commerce', 'sales', 'department store',
                   'supermarket', 'wholesale'],
            'ja': ['小売', 'ショップ', '店舗', 'EC', 'ECサイト', 'オンラインショップ',
                   '通販', 'ネットショップ', '百貨店', 'スーパー', '卸売']
        },
        'healthcare': {
            'en': ['healthcare', 'health', 'medical', 'medicine', 'hospital', 'clinic',
                   'pharma', 'pharmaceutical', 'drug', 'therapy', 'wellness', 'nursing',
                   'dental', 'diagnostic', 'biotech'],
            'ja': ['医療', '病院', 'クリニック', 'ヘルスケア', '製薬', '薬品', '医療機器',
                   '診療所', '医院', '薬局', '歯科', 'バイオテック']
        },
        'education': {
            'en': ['education', 'school', 'university', 'college', 'training', 'academy',
                   'learning', 'course', 'tutor', 'educational', 'elearning', 'online learning'],
            'ja': ['教育', '学校', '大学', '学習', 'トレーニング', 'アカデミー', 'スクール',
                   '塾', '予備校', '専門学校', 'オンライン学習']
        },
        'manufacturing': {
            'en': ['manufacturing', 'manufacturer', 'factory', 'production', 'industrial',
                   'maker', 'fabrication', 'assembly', 'machinery'],
            'ja': ['製造', '工場', '生産', '工業', 'メーカー', '製造業', '生産管理',
                   '工場管理', '部品製造']
        },
        'construction': {
            'en': ['construction', 'builder', 'building', 'civil engineering', 'contractor',
                   'engineering', 'infrastructure', 'development'],
            'ja': ['建設', '建築', '工事', '土木', 'エンジニアリング', '建築設計',
                   '施工管理', '土木工事']
        },
        'real_estate': {
            'en': ['real estate', 'property', 'realty', 'housing', 'apartment', 'real-estate',
                   'land', 'rent', 'rental', 'real estate agent'],
            'ja': ['不動産', '住宅', 'マンション', '土地', '賃貸', '不動産管理',
                   '宅地建物取引', '不動産仲介']
        },
        'food_beverage': {
            'en': ['food', 'beverage', 'restaurant', 'dining', 'cafe', 'café', 'catering',
                   'food service', 'bakery', 'food manufacturing', 'restaurant group'],
            'ja': ['食品', 'レストラン', '飲食', '外食', '飲料', 'フードサービス',
                   '食品製造', '食品加工', 'カフェ', 'ベーカリー']
        },
        'automotive': {
            'en': ['automotive', 'automobile', 'car', 'vehicle', 'auto', 'mobility',
                   'auto parts', 'dealership', 'fleet'],
            'ja': ['自動車', '車', 'カー', 'モビリティ', '自動車関連', '自動車部品',
                   '自動車販売', '自動車修理']
        },
        'energy': {
            'en': ['energy', 'power', 'electric', 'electricity', 'renewable energy',
                   'solar', 'wind', 'generation', 'utility', 'oil', 'gas', 'utility company'],
            'ja': ['エネルギー', '電力', '電気', '再生可能エネルギー', '太陽光', '風力',
                   '発電', '電力会社', 'ガス']
        },
        'logistics': {
            'en': ['logistics', 'transportation', 'shipping', 'delivery', 'supply chain',
                   'transport', 'warehouse', 'distribution'],
            'ja': ['物流', '運輸', '配送', '輸送', 'サプライチェーン', '運送',
                   '倉庫', '物流センター']
        },
        'consulting': {
            'en': ['consulting', 'consultant', 'advisory', 'advising', 'management consulting',
                   'business consultant', 'strategy', 'strategic'],
            'ja': ['コンサルティング', 'コンサル', 'アドバイザリー', '経営コンサル',
                   '経営相談', 'コンサルタント']
        },
        'media': {
            'en': ['media', 'publishing', 'broadcast', 'entertainment', 'advertising',
                   'news', 'television', 'radio', 'production'],
            'ja': ['メディア', '出版', '放送', 'エンターテインメント', '広告',
                   '広告代理店', 'テレビ', 'ラジオ']
        },
        'telecommunications': {
            'en': ['telecommunications', 'telecom', 'communication', 'mobile', 'wireless',
                   'phone', 'network', 'internet service', 'isp'],
            'ja': ['通信', 'テレコム', 'モバイル', '無線', '通信事業', '通信会社',
                   '携帯電話']
        },
        'hospitality': {
            'en': ['hotel', 'hospitality', 'resort', 'accommodation', 'lodging',
                   'tourism', 'travel', 'tour operator'],
            'ja': ['ホテル', 'ホスピタリティ', 'リゾート', '宿泊', '観光',
                   '旅行', 'ツアーオペレーター']
        },
        'entertainment': {
            'en': ['entertainment', 'gaming', 'game', 'esports', 'music', 'movie',
                   'film', 'studio', 'production'],
            'ja': ['エンターテインメント', 'ゲーム', '音楽', '映画', 'スタジオ',
                   'エスポーツ']
        },
        'non_profit': {
            'en': ['non-profit', 'nonprofit', 'ngo', 'charity', 'charitable', 'foundation',
                   'association', 'volunteer'],
            'ja': ['非営利', 'npo', 'ngo', '慈善', 'チャリティ', '財団', '協会']
        }
    }
    
    # Schema.org type mappings
    SCHEMA_TYPE_MAPPING = {
        'softwareapplication': 'technology',
        'websiteapplication': 'technology',
        'computersoftware': 'technology',
        'financialservice': 'finance',
        'bank': 'finance',
        'insuranceagency': 'finance',
        'investmentservice': 'finance',
        'store': 'retail',
        'onlinestore': 'retail',
        'shoppingcenter': 'retail',
        'hospital': 'healthcare',
        'physicianoffice': 'healthcare',
        'dentistoffice': 'healthcare',
        'veterinarycare': 'healthcare',
        'pharmacy': 'healthcare',
        'educationalorganization': 'education',
        'school': 'education',
        'university': 'education',
        'elementaryschool': 'education',
        'middleschool': 'education',
        'highschool': 'education',
        'collegeoruniversity': 'education',
        'localizedschool': 'education',
        'manufacturer': 'manufacturing',
        'contractorservice': 'construction',
        'realestateagent': 'real_estate',
        'residentialarea': 'real_estate',
        'apartmentcomplex': 'real_estate',
        'restaurant': 'food_beverage',
        'cafe': 'food_beverage',
        'bakery': 'food_beverage',
        'foodestablishment': 'food_beverage',
        'automobiledealership': 'automotive',
        'automobilerepair': 'automotive',
        'gasstation': 'energy',
        'shippingservice': 'logistics',
        'storageservice': 'logistics',
        'professionalservice': 'consulting',
        'localbus': 'hospitality',
        'hotel': 'hospitality',
        'broadcaster': 'media',
        'creativework': 'media',
        'televisionstation': 'media',
        'radiochannel': 'media',
        'localbusiness': None,  # Too generic
        'organization': None,    # Too generic
    }

    def __init__(self, base_url: str, fetcher=None):
        """
        Initialize industry extractor.
        
        Args:
            base_url: Base URL of the website
            fetcher: PageFetcher instance for fetching additional pages
        """
        self.base_url = base_url
        self.fetcher = fetcher
    
    @staticmethod
    def _extract_domain_hints(url: str) -> Optional[str]:
        """Extract potential industry hints from domain name."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            domain_name = domain.split('.')[0]
            
            # Very crude matching - only if domain exactly matches known keywords
            for industry, keywords_dict in UpgradedIndustryExtractor.INDUSTRY_KEYWORDS.items():
                for keyword in keywords_dict['en'] + keywords_dict['ja']:
                    if keyword.lower() == domain_name:
                        return industry
        except Exception:
            pass
        
        return None

    def extract(self, html_content: str, final_url: Optional[str] = None, 
                log_candidates: Optional[list] = None) -> Dict:
        """
        Extract industry information using all methods.
        
        Args:
            html_content: HTML content to parse
            final_url: Final URL after redirects
            log_candidates: List to append all candidates to
            
        Returns:
            Dictionary with industry, source, confidence, and candidates
        """
        url = final_url or self.base_url
        candidates: List[IndustryCandidate] = []
        
        # Try domain hints first (low confidence fallback)
        domain_hint = self._extract_domain_hints(url)
        if domain_hint:
            candidates.append(IndustryCandidate(domain_hint, 'domain-hint', 0.4))
        
        # Extract from multiple sources
        jsonld_result = self._extract_from_jsonld(html_content, url)
        if jsonld_result:
            candidates.append(jsonld_result)
        
        meta_result = self._extract_from_metadata(html_content, url)
        if meta_result:
            candidates.append(meta_result)
        
        text_result = self._extract_from_text(html_content, url)
        if text_result:
            candidates.append(text_result)
        
        # Log all candidates if requested
        if log_candidates is not None:
            log_candidates.extend([c.value for c in candidates])
        
        # Select best candidate (highest confidence)
        result = {
            'industry': None,
            'industry_source': None,
            'industry_confidence': 0.0,
            'industry_candidates': [c.to_dict() for c in candidates]
        }
        
        if candidates:
            # Sort by confidence (descending)
            candidates.sort(key=lambda x: x.confidence, reverse=True)
            best = candidates[0]
            result['industry'] = best.value
            result['industry_source'] = best.source
            result['industry_confidence'] = best.confidence
            logger.info(
                f"Extracted industry: {best.value} "
                f"(source: {best.source}, confidence: {best.confidence:.2f})"
            )
        
        return result
    
    def _extract_from_metadata(self, html_content: str, url: str) -> Optional[IndustryCandidate]:
        """Extract industry from meta tags and structured data."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Priority order for meta searches
            meta_sources = [
                ('meta', {'name': 'description'}, 0.8),
                ('meta', {'property': 'og:description'}, 0.8),
                ('meta', {'name': 'keywords'}, 0.75),
                ('meta', {'name': 'industry'}, 0.85),
                ('meta', {'name': 'business'}, 0.8),
            ]
            
            for tag, attrs, confidence in meta_sources:
                element = soup.find(tag, attrs)
                if element:
                    content = element.get('content', '').lower()
                    if content:
                        industry = self._match_industry_keywords(content)
                        if industry:
                            logger.debug(f"Found industry in {attrs}: {industry}")
                            return IndustryCandidate(industry, 'metadata', confidence)
            
        except Exception as e:
            logger.error(f"Error extracting industry from metadata: {e}")
        
        return None
    
    def _extract_from_jsonld(self, html_content: str, url: str) -> Optional[IndustryCandidate]:
        """Extract industry from JSON-LD structured data."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find JSON-LD scripts
            jsonld_scripts = soup.find_all('script', type='application/ld+json')
            for script in jsonld_scripts:
                try:
                    data = json.loads(script.string) if script.string else None
                    if not data:
                        continue
                    
                    # Try to extract industry
                    industry = self._extract_industry_from_json(data)
                    if industry:
                        logger.debug(f"Found industry in JSON-LD: {industry}")
                        return IndustryCandidate(industry, 'jsonld', 0.9)
                except (json.JSONDecodeError, TypeError):
                    continue
            
        except Exception as e:
            logger.error(f"Error extracting industry from JSON-LD: {e}")
        
        return None
    
    def _extract_industry_from_json(self, data: any) -> Optional[str]:
        """Recursively extract industry from JSON structure."""
        if isinstance(data, dict):
            # Check for explicit industry fields
            industry_fields = ['industry', 'sector', 'businessType', 'description']
            for field in industry_fields:
                if field in data:
                    value = str(data[field]).lower()
                    industry = self._match_industry_keywords(value)
                    if industry:
                        return industry
            
            # Check @type for schema.org types
            if '@type' in data:
                schema_type = str(data['@type']).lower()
                if schema_type in self.SCHEMA_TYPE_MAPPING:
                    mapped = self.SCHEMA_TYPE_MAPPING[schema_type]
                    if mapped:
                        return mapped
            
            # Check description field
            if 'description' in data:
                industry = self._match_industry_keywords(str(data['description']).lower())
                if industry:
                    return industry
            
            # Recursively search other fields
            for value in data.values():
                if isinstance(value, (dict, list)):
                    result = self._extract_industry_from_json(value)
                    if result:
                        return result
        
        elif isinstance(data, list):
            for item in data:
                result = self._extract_industry_from_json(item)
                if result:
                    return result
        
        return None
    
    def _extract_from_text(self, html_content: str, url: str) -> Optional[IndustryCandidate]:
        """Extract industry from page text content with context weighting."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove noise
            for element in soup(['script', 'style']):
                element.decompose()
            
            # Weighted text extraction from key sections
            sections = []
            
            # Title (highest weight)
            title_tag = soup.find('title')
            if title_tag:
                sections.append((title_tag.get_text(), 2))
            
            # H1 tags (high weight)
            h1_tags = soup.find_all('h1')
            for h1 in h1_tags[:3]:
                sections.append((h1.get_text(), 1.5))
            
            # Meta description
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc:
                sections.append((meta_desc.get('content', ''), 1.2))
            
            # About/company info sections (moderate weight)
            for element in soup.find_all(['section', 'div']):
                classes = element.get('class', [])
                ids = element.get('id', '').lower()
                
                if any(c in str(classes).lower() for c in ['about', 'company', 'intro', 'description']):
                    text = element.get_text()[:500]  # Limit length
                    sections.append((text, 0.8))
            
            # Combine and search
            combined_text = ' '.join([text for text, _ in sections]).lower()
            industry = self._match_industry_keywords(combined_text)
            
            if industry:
                logger.debug(f"Found industry in text: {industry}")
                return IndustryCandidate(industry, 'text', 0.7)
            
        except Exception as e:
            logger.error(f"Error extracting industry from text: {e}")
        
        return None
    
    def _match_industry_keywords(self, text: str) -> Optional[str]:
        """Match text against industry keywords and return best match."""
        if not text:
            return None
        
        best_match = None
        best_score = 0
        
        for industry, keywords_dict in self.INDUSTRY_KEYWORDS.items():
            score = 0
            
            # Check both English and Japanese keywords
            for lang in ['en', 'ja']:
                keywords = keywords_dict.get(lang, [])
                for keyword in keywords:
                    # Case-insensitive search for English, case-sensitive for Japanese
                    if lang == 'en':
                        if keyword.lower() in text:
                            score += 1
                    else:
                        if keyword in text:
                            score += 1
            
            if score > best_score:
                best_score = score
                best_match = industry
        
        return best_match if best_score > 0 else None


# Compatibility alias for older imports expecting `IndustryExtractor`
# Provide a module-level alias so `from crawler.industry_extractor import IndustryExtractor`
# continues to work even though the class is named `UpgradedIndustryExtractor`.
IndustryExtractor = UpgradedIndustryExtractor