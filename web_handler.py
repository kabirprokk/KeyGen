"""
Web Search Handler for KeyGen.ai
Handles all external web searches with multiple fallback engines.
Includes automatic data collection, cleaning, and deduplication.
"""

import re
import json
import ssl
import urllib.request
import urllib.parse
import urllib.error
import hashlib
import time
import os
import threading
from collections import defaultdict
from datetime import datetime

class WebSearchHandler:
    """Handles all web search operations with caching and fallback engines."""
    
    def __init__(self, cache_dir="knowledge", cache_file="web_search_cache.json"):
        self.cache_dir = cache_dir
        self.cache_file = f"{cache_dir}/{cache_file}"
        self.collected_dir = f"{cache_dir}/collected"
        self.search_cache = {}
        self.collected_hashes = set()
        self.collection_counter = 0
        self.is_collecting = False
        self.collection_thread = None
        self.collection_topics = [
            "artificial intelligence latest developments",
            "machine learning breakthroughs",
            "technology news today",
            "science discoveries",
            "world news headlines",
            "sports results",
            "health medical advances",
            "space exploration updates",
            "climate change news",
            "economic updates"
        ]
        
        # SSL context for HTTPS requests
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # Create directories
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.collected_dir, exist_ok=True)
        
        # Search engine configurations
        self.engines = {
            "duckduckgo_api": {
                "url": "https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1",
                "parser": self._parse_duckduckgo_api,
                "type": "json",
                "timeout": 8
            },
            "duckduckgo_html": {
                "url": "https://html.duckduckgo.com/html/?q={query}",
                "parser": self._parse_duckduckgo_html,
                "type": "html",
                "timeout": 10
            },
            "google": {
                "url": "https://www.google.com/search?q={query}&hl=en",
                "parser": self._parse_google,
                "type": "html",
                "timeout": 10
            },
            "wikipedia": {
                "url": "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json&srlimit=3",
                "parser": self._parse_wikipedia,
                "type": "json",
                "timeout": 10
            },
            "bing": {
                "url": "https://www.bing.com/search?q={query}",
                "parser": self._parse_bing,
                "type": "html",
                "timeout": 10
            }
        }
        
        # Alternative search engines for fallback
        self.fallback_engines = {
            "yahoo": {
                "url": "https://search.yahoo.com/search?p={query}",
                "parser": self._parse_generic_html,
                "type": "html",
                "timeout": 10
            },
            "ask": {
                "url": "https://www.ask.com/web?q={query}",
                "parser": self._parse_generic_html,
                "type": "html",
                "timeout": 10
            },
            "ecosia": {
                "url": "https://www.ecosia.org/search?q={query}",
                "parser": self._parse_generic_html,
                "type": "html",
                "timeout": 10
            }
        }
        
        # Load cache and hashes
        self.load_cache()
        self.load_collected_hashes()
        self.find_latest_counter()
    
    # ========== CACHE MANAGEMENT ==========
    
    def load_cache(self):
        """Load search cache from disk."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.search_cache = json.load(f)
                print(f"✓ Loaded {len(self.search_cache)} cached searches")
        except Exception as e:
            print(f"Cache load error: {e}")
            self.search_cache = {}
    
    def save_cache(self):
        """Save search cache to disk."""
        try:
            if len(self.search_cache) > 500:
                keys = list(self.search_cache.keys())[-500:]
                self.search_cache = {k: self.search_cache[k] for k in keys}
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.search_cache, f, indent=2)
        except Exception as e:
            print(f"Cache save error: {e}")
    
    def get_cache_key(self, query):
        """Generate a unique cache key for a query."""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    def get_cached_result(self, query, max_age=3600):
        """Get cached result if it exists and is fresh."""
        cache_key = self.get_cache_key(query)
        if cache_key in self.search_cache:
            entry = self.search_cache[cache_key]
            if time.time() - entry.get('timestamp', 0) < max_age:
                return entry.get('data')
        return None
    
    def cache_result(self, query, data, source="unknown"):
        """Cache a search result."""
        cache_key = self.get_cache_key(query)
        self.search_cache[cache_key] = {
            'data': data,
            'timestamp': time.time(),
            'source': source,
            'query': query[:200]
        }
        self.save_cache()
    
    # ========== COLLECTED DATA MANAGEMENT ==========
    
    def load_collected_hashes(self):
        """Load hashes of previously collected data."""
        try:
            hash_file = f"{self.collected_dir}/collected_hashes.json"
            if os.path.exists(hash_file):
                with open(hash_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.collected_hashes = set(data.get('hashes', []))
                print(f"✓ Loaded {len(self.collected_hashes)} collected data hashes")
        except Exception as e:
            print(f"Hash load error: {e}")
            self.collected_hashes = set()
    
    def save_collected_hashes(self):
        """Save hashes of collected data."""
        try:
            hash_file = f"{self.collected_dir}/collected_hashes.json"
            with open(hash_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'hashes': list(self.collected_hashes),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"Hash save error: {e}")
    
    def find_latest_counter(self):
        """Find the latest collection counter number."""
        try:
            existing_files = os.listdir(self.collected_dir)
            counters = []
            for filename in existing_files:
                match = re.match(r'collected_data_(\d+)\.txt', filename)
                if match:
                    counters.append(int(match.group(1)))
            self.collection_counter = max(counters) if counters else 0
            print(f"✓ Collection counter starting at: {self.collection_counter}")
        except Exception as e:
            print(f"Counter find error: {e}")
            self.collection_counter = 0
    
    def get_next_filename(self):
        """Get the next available collection filename."""
        self.collection_counter += 1
        return f"{self.collected_dir}/collected_data_{self.collection_counter}.txt"
    
    # ========== DATA CLEANING ==========
    
    def clean_text(self, text):
        """Enhanced text cleaning for collected data."""
        if not text:
            return ""
        
        # Remove HTML tags
        clean = re.sub(r'<.*?>', '', text)
        
        # Remove scripts and styles
        clean = re.sub(r'<script[^>]*>.*?</script>', '', clean, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove common noise
        noise_patterns = [
            r'(?i)click here',
            r'(?i)read more',
            r'(?i)cookies?',
            r'(?i)privacy policy',
            r'(?i)subscribe',
            r'(?i)advertisement',
            r'(?i)sponsored',
            r'(?i)©',
            r'(?i)all rights reserved',
            r'(?i)terms of (use|service)',
            r'(?i)accept cookies',
            r'(?i)sign in',
            r'(?i)log in',
            r'(?i)create account',
            r'(?i)accessibility',
            r'(?i)feedback',
            r'\bCached\b',
            r'\bSimilar\b',
            r'(?i)share on facebook',
            r'(?i)share on twitter',
            r'(?i)follow us on',
            r'(?i)newsletter',
            r'(?i)ad Choices',
            r'(?i)powered by',
            r'(?i)copyright \d{4}',
            r'\[\d+\]',  # Citation brackets
            r'\[\w+\]',  # Wiki-style citations
        ]
        
        for pattern in noise_patterns:
            clean = re.sub(pattern, '', clean)
        
        # Remove URLs
        clean = re.sub(r'https?://\S+', '', clean)
        
        # Remove email addresses
        clean = re.sub(r'\S+@\S+', '', clean)
        
        # Remove extra whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        # Remove repeated punctuation
        clean = re.sub(r'([.!?])\1+', r'\1', clean)
        clean = re.sub(r'([,;:])\1+', r'\1', clean)
        
        # Remove lines that are too short
        lines = clean.split('\n')
        lines = [l.strip() for l in lines if len(l.strip()) > 20]
        clean = '\n'.join(lines)
        
        return clean
    
    def clean_sentence(self, sentence):
        """Clean a single sentence for better readability."""
        if not sentence:
            return ""
        
        # Capitalize first letter
        sentence = sentence.strip()
        if len(sentence) > 1:
            sentence = sentence[0].upper() + sentence[1:]
        
        # Ensure proper ending
        if sentence[-1] not in '.!?"\'':
            sentence += '.'
        
        return sentence
    
    def split_into_sentences(self, text):
        """Split text into clean sentences."""
        if not text:
            return []
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Clean each sentence
        cleaned = []
        for sent in sentences:
            sent = self.clean_sentence(sent.strip())
            if len(sent) > 15 and not any(
                word in sent.lower() 
                for word in ['cookie', 'subscribe', 'advertisement', 'click here', 'sign up']
            ):
                cleaned.append(sent)
        
        return cleaned
    
    def extract_key_sentences(self, text, max_sentences=10):
        """Extract the most informative sentences from text."""
        sentences = self.split_into_sentences(text)
        
        if len(sentences) <= max_sentences:
            return sentences
        
        # Score sentences by information density
        scored = []
        for sent in sentences:
            score = 0
            words = sent.split()
            
            # Longer sentences often have more info
            if len(words) > 8:
                score += 2
            if len(words) > 15:
                score += 3
            
            # Sentences with numbers/statistics
            if re.search(r'\d+', sent):
                score += 3
            
            # Sentences with proper nouns
            if re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+', sent):
                score += 3
            
            # Sentences with factual indicators
            factual_words = ['is', 'are', 'was', 'were', 'has', 'have', 'according', 'research', 
                           'study', 'found', 'discovered', 'announced', 'reported', 'confirmed']
            score += sum(1 for w in factual_words if w in sent.lower()) * 2
            
            # Penalize question sentences
            if sent.endswith('?'):
                score -= 5
            
            scored.append((score, sent))
        
        # Sort by score and take top sentences
        scored.sort(reverse=True, key=lambda x: x[0])
        top_sentences = [s[1] for s in scored[:max_sentences]]
        
        # Sort back to original order
        ordered = [s for s in sentences if s in top_sentences]
        
        return ordered
    
    # ========== DEDUPLICATION ==========
    
    def get_text_hash(self, text):
        """Generate a hash for text deduplication."""
        # Normalize text
        normalized = text.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Use first 200 chars for hash
        sample = normalized[:200]
        return hashlib.md5(sample.encode()).hexdigest()
    
    def get_sentence_similarity(self, sent1, sent2):
        """Calculate similarity between two sentences."""
        words1 = set(sent1.lower().split())
        words2 = set(sent2.lower().split())
        
        if not words1 or not words2:
            return 0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0
    
    def is_duplicate(self, text, existing_texts, threshold=0.7):
        """Check if text is a duplicate of any existing text."""
        text_hash = self.get_text_hash(text)
        
        # Check hash first
        if text_hash in self.collected_hashes:
            return True
        
        # Check similarity with existing texts
        sentences = self.split_into_sentences(text)
        for existing in existing_texts:
            existing_sentences = self.split_into_sentences(existing)
            for sent in sentences:
                for exist_sent in existing_sentences:
                    if self.get_sentence_similarity(sent, exist_sent) > threshold:
                        return True
        
        return False
    
    def remove_duplicates_from_text(self, text, existing_texts):
        """Remove duplicate sentences from text."""
        sentences = self.split_into_sentences(text)
        unique_sentences = []
        
        for sent in sentences:
            is_dup = False
            for existing in existing_texts:
                existing_sentences = self.split_into_sentences(existing)
                for exist_sent in existing_sentences:
                    if self.get_sentence_similarity(sent, exist_sent) > 0.6:
                        is_dup = True
                        break
                if is_dup:
                    break
            
            if not is_dup:
                sent_hash = self.get_text_hash(sent)
                if sent_hash not in self.collected_hashes:
                    unique_sentences.append(sent)
                    self.collected_hashes.add(sent_hash)
        
        return ' '.join(unique_sentences)
    
    # ========== KNOWLEDGE FOLDER CHECK ==========
    
    def get_existing_knowledge(self):
        """Get all existing text from knowledge folder."""
        existing_texts = []
        
        try:
            # Check knowledge directory
            if os.path.exists(self.cache_dir):
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.txt') and filename != 'web_search_cache.json':
                        filepath = os.path.join(self.cache_dir, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                text = f.read()
                                if text.strip():
                                    existing_texts.append(text)
                        except:
                            pass
            
            # Check collected directory
            if os.path.exists(self.collected_dir):
                for filename in os.listdir(self.collected_dir):
                    if filename.endswith('.txt'):
                        filepath = os.path.join(self.collected_dir, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                text = f.read()
                                if text.strip():
                                    existing_texts.append(text)
                        except:
                            pass
        except Exception as e:
            print(f"Error reading existing knowledge: {e}")
        
        return existing_texts
    
    # ========== HTTP REQUEST HANDLER ==========
    
    def make_request(self, url, timeout=10, json_response=False, custom_headers=None):
        """Make an HTTP request with proper error handling."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        if custom_headers:
            headers.update(custom_headers)
        
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout, context=self.ssl_context) as response:
                if json_response:
                    return json.loads(response.read().decode('utf-8'))
                return response.read().decode('utf-8', errors='ignore')
        except urllib.error.HTTPError as e:
            print(f"  HTTP Error {e.code} for {url[:60]}...")
            return None
        except urllib.error.URLError as e:
            print(f"  URL Error for {url[:60]}...: {e.reason}")
            return None
        except Exception as e:
            print(f"  Request error for {url[:60]}...: {e}")
            return None
    
    # ========== PARSERS ==========
    
    def _parse_duckduckgo_api(self, data):
        """Parse DuckDuckGo API JSON response."""
        if not data:
            return []
        
        results = []
        
        abstract = data.get('AbstractText', '')
        if abstract and len(abstract) > 40:
            results.append({
                'text': self.clean_text(abstract),
                'source': 'DuckDuckGo Abstract',
                'type': 'abstract'
            })
        
        answer = data.get('Answer', '')
        if answer and len(answer) > 5:
            results.append({
                'text': self.clean_text(answer),
                'source': 'DuckDuckGo Answer',
                'type': 'answer'
            })
        
        related = data.get('RelatedTopics', [])
        for topic in related[:3]:
            if isinstance(topic, dict):
                text = topic.get('Text', '')
                if text and len(text) > 40:
                    results.append({
                        'text': self.clean_text(text),
                        'source': 'DuckDuckGo Related',
                        'type': 'related'
                    })
        
        return results
    
    def _parse_duckduckgo_html(self, html):
        """Parse DuckDuckGo HTML search results."""
        if not html:
            return []
        
        results = []
        snippet_patterns = [
            r'<a class="result__snippet"[^>]*>(.*?)</a>',
            r'<td class="result-sn-abstract[^"]*">(.*?)</td>',
            r'<div class="result__body[^"]*"[^>]*>(.*?)</div>',
        ]
        
        for pattern in snippet_patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            for match in matches[:5]:
                clean = self.clean_text(match)
                if len(clean) > 60:
                    results.append({
                        'text': clean,
                        'source': 'DuckDuckGo HTML',
                        'type': 'snippet'
                    })
        
        return results
    
    def _parse_google(self, html):
        """Parse Google search results."""
        if not html:
            return []
        
        results = []
        snippet_patterns = [
            r'<div class="BNeawe\s+s3v9rd\s+AP7Wnd">(.*?)</div>',
            r'<span class="st">(.*?)</span>',
            r'<div class="VwiC3b[^"]*">(.*?)</div>',
        ]
        
        for pattern in snippet_patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            for match in matches[:3]:
                clean = self.clean_text(match)
                if 60 < len(clean) < 2000:
                    results.append({
                        'text': clean,
                        'source': 'Google Snippet',
                        'type': 'snippet'
                    })
        
        kp_patterns = [
            r'<div class="kno-rdesc"[^>]*>.*?<span[^>]*>(.*?)</span>',
            r'<div class="LGOjhe"[^>]*>.*?<span[^>]*>(.*?)</span>',
            r'<div class="kno-ecr-pt"[^>]*>(.*?)</div>',
        ]
        
        for pattern in kp_patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                clean = self.clean_text(match.group(1))
                if 20 < len(clean) < 800:
                    results.append({
                        'text': clean,
                        'source': 'Google Knowledge Panel',
                        'type': 'knowledge'
                    })
        
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
        for p in paragraphs[:5]:
            clean = self.clean_text(p)
            if len(clean) > 100:
                results.append({
                    'text': clean,
                    'source': 'Google Organic',
                    'type': 'organic'
                })
        
        return results
    
    def _parse_wikipedia(self, data):
        """Parse Wikipedia API response."""
        if not data or 'query' not in data:
            return []
        
        results = []
        search_results = data['query'].get('search', [])
        
        for item in search_results[:3]:
            title = item.get('title', '')
            snippet = item.get('snippet', '')
            
            if snippet:
                clean = self.clean_text(snippet)
                if len(clean) > 40:
                    results.append({
                        'text': clean,
                        'source': f'Wikipedia: {title}',
                        'type': 'wikipedia',
                        'pageid': item.get('pageid')
                    })
        
        return results
    
    def _parse_bing(self, html):
        """Parse Bing search results."""
        if not html:
            return []
        
        results = []
        snippet_patterns = [
            r'<p[^>]*>(.*?)</p>',
            r'<div class="b_caption[^"]*"[^>]*>.*?<p[^>]*>(.*?)</p>',
        ]
        
        for pattern in snippet_patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            for match in matches[:5]:
                clean = self.clean_text(match)
                if len(clean) > 60:
                    results.append({
                        'text': clean,
                        'source': 'Bing',
                        'type': 'snippet'
                    })
        
        return results
    
    def _parse_generic_html(self, html):
        """Generic HTML parser for fallback engines."""
        if not html:
            return []
        
        results = []
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
        for p in paragraphs[:10]:
            clean = self.clean_text(p)
            if 60 < len(clean) < 1000:
                results.append({
                    'text': clean,
                    'source': 'Generic Search',
                    'type': 'organic'
                })
        
        return results
    
    # ========== WIKIPEDIA DEEP SEARCH ==========
    
    def get_wikipedia_extract(self, page_id):
        """Get the full intro extract from a Wikipedia page."""
        try:
            url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&pageids={page_id}&format=json"
            data = self.make_request(url, json_response=True, timeout=10)
            
            if data and 'query' in data:
                pages = data['query'].get('pages', {})
                for pid, page in pages.items():
                    extract = page.get('extract', '')
                    if extract and len(extract) > 100:
                        if len(extract) > 2000:
                            extract = extract[:2000].rsplit('.', 1)[0] + '.'
                        return extract
        except Exception as e:
            print(f"  Wikipedia extract error: {e}")
        
        return None
    
    # ========== WEBSITE SCRAPING ==========
    
    def scrape_website(self, url, timeout=15):
        """Scrape content from a website URL."""
        print(f"  🌐 Scraping: {url[:80]}...")
        
        try:
            html = self.make_request(url, timeout=timeout)
            if not html:
                return None
            
            # Extract main content
            content = self._extract_main_content(html)
            
            if content and len(content) > 100:
                return self.clean_text(content)
            
            return None
            
        except Exception as e:
            print(f"  ✗ Scrape error: {e}")
            return None
    
    def _extract_main_content(self, html):
        """Extract main content from HTML."""
        if not html:
            return ""
        
        # Remove scripts, styles, nav, footer
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<footer[^>]*>.*?</footer>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<header[^>]*>.*?</header>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Look for main content areas
        content_patterns = [
            r'<article[^>]*>(.*?)</article>',
            r'<main[^>]*>(.*?)</main>',
            r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*id="[^"]*content[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*article[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*post[^"]*"[^>]*>(.*?)</div>',
        ]
        
        for pattern in content_patterns:
            match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1)
                if len(content) > 200:
                    return self.clean_text(content)
        
        # Fallback: extract all paragraphs
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL | re.IGNORECASE)
        if paragraphs:
            content = ' '.join(paragraphs)
            if len(content) > 200:
                return self.clean_text(content)
        
        # Last resort: get body text
        body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
        if body_match:
            return self.clean_text(body_match.group(1))
        
        return self.clean_text(html)
    
    # ========== MAIN SEARCH FUNCTIONS ==========
    
    def search(self, query, max_results=5, use_cache=True):
        """Main search function that tries multiple engines."""
        if not query or not query.strip():
            return []
        
        query = query.strip()
        print(f"  🔍 Searching: {query[:80]}...")
        
        if use_cache:
            cached = self.get_cached_result(query)
            if cached:
                print(f"  ✓ Cache hit")
                return cached
        
        all_results = []
        engine_order = ["duckduckgo_api", "google", "wikipedia", "bing", "duckduckgo_html"]
        
        for engine_name in engine_order:
            if len(all_results) >= max_results * 2:
                break
            
            engine = self.engines.get(engine_name)
            if not engine:
                continue
            
            try:
                url = engine['url'].format(query=urllib.parse.quote(query))
                is_json = engine['type'] == 'json'
                response = self.make_request(url, timeout=engine['timeout'], json_response=is_json)
                
                if response:
                    parser = engine['parser']
                    results = parser(response)
                    
                    if results:
                        all_results.extend(results)
                
            except Exception as e:
                print(f"  ✗ {engine_name}: {e}")
                continue
        
        # Remove duplicates
        seen = set()
        unique_results = []
        for result in all_results:
            text = result['text'][:200]
            if text not in seen:
                seen.add(text)
                unique_results.append(result)
        
        unique_results = unique_results[:max_results]
        
        if unique_results:
            self.cache_result(query, unique_results)
        
        return unique_results
    
    def search_single_answer(self, query):
        """Search for a single best answer."""
        results = self.search(query, max_results=3)
        
        if not results:
            return None
        
        scored = []
        for result in results:
            score = 0
            if result['type'] in ['answer', 'abstract']:
                score += 30
            if result['type'] == 'knowledge':
                score += 25
            if result['type'] == 'wikipedia_extract':
                score += 20
            if result['type'] == 'snippet':
                score += 15
            if len(result['text']) > 100:
                score += 10
            if len(result['text']) > 500:
                score -= 5
            scored.append((score, result))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        return scored[0][1]['text'] if scored else None
    
    # ========== AUTO COLLECTION FUNCTION ==========
    
    def collect_data_auto(self):
        """
        Automatically collect data from web searches.
        Cleans, deduplicates, and saves new unique content.
        Runs every 2.5 minutes.
        """
        if self.is_collecting:
            print("⚠ Already collecting data...")
            return
        
        self.is_collecting = True
        print(f"\n{'='*60}")
        print(f"📥 AUTO DATA COLLECTION STARTED - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        try:
            # Get existing knowledge for deduplication
            existing_texts = self.get_existing_knowledge()
            print(f"📚 Existing knowledge: {len(existing_texts)} files loaded")
            
            all_new_content = []
            
            # Search and scrape for each topic
            for i, topic in enumerate(self.collection_topics, 1):
                print(f"\n📌 Topic {i}/{len(self.collection_topics)}: {topic}")
                
                try:
                    # Search for the topic
                    results = self.search(topic, max_results=3, use_cache=False)
                    
                    if not results:
                        print(f"  ⚠ No results, trying fallback engines...")
                        results = self._search_with_fallbacks(topic)
                    
                    if results:
                        for result in results:
                            text = result.get('text', '')
                            
                            if text and len(text) > 50:
                                # Get key sentences
                                key_sentences = self.extract_key_sentences(text, max_sentences=5)
                                combined = ' '.join(key_sentences)
                                
                                # Check for duplicates
                                if not self.is_duplicate(combined, existing_texts):
                                    all_new_content.append({
                                        'topic': topic,
                                        'text': combined,
                                        'source': result.get('source', 'Unknown'),
                                        'timestamp': datetime.now().isoformat()
                                    })
                                    existing_texts.append(combined)
                                    print(f"  ✓ New content found ({len(combined)} chars)")
                                else:
                                    print(f"  - Duplicate content skipped")
                    
                    # Also try to scrape URLs from results
                    if results:
                        for result in results[:2]:
                            # Try to get Wikipedia extracts
                            if result.get('type') == 'wikipedia' and result.get('pageid'):
                                extract = self.get_wikipedia_extract(result['pageid'])
                                if extract:
                                    key_sentences = self.extract_key_sentences(extract, max_sentences=5)
                                    combined = ' '.join(key_sentences)
                                    if not self.is_duplicate(combined, existing_texts):
                                        all_new_content.append({
                                            'topic': topic,
                                            'text': combined,
                                            'source': 'Wikipedia Extract',
                                            'timestamp': datetime.now().isoformat()
                                        })
                                        existing_texts.append(combined)
                                        print(f"  ✓ Wikipedia extract added")
                
                except Exception as e:
                    print(f"  ✗ Error on topic '{topic}': {e}")
                    continue
                
                # Small delay between topics
                time.sleep(1)
            
            # Save all new content
            if all_new_content:
                filename = self.get_next_filename()
                print(f"\n💾 Saving {len(all_new_content)} new entries to: {filename}")
                
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"=== Auto-Collected Data ===\n")
                        f.write(f"Collection Date: {datetime.now().isoformat()}\n")
                        f.write(f"Total Entries: {len(all_new_content)}\n")
                        f.write(f"{'='*50}\n\n")
                        
                        for i, entry in enumerate(all_new_content, 1):
                            f.write(f"[{i}] Topic: {entry['topic']}\n")
                            f.write(f"Source: {entry['source']}\n")
                            f.write(f"Content: {entry['text']}\n")
                            f.write(f"{'-'*50}\n\n")
                    
                    # Save updated hashes
                    for entry in all_new_content:
                        sentences = self.split_into_sentences(entry['text'])
                        for sent in sentences:
                            sent_hash = self.get_text_hash(sent)
                            self.collected_hashes.add(sent_hash)
                    
                    self.save_collected_hashes()
                    print(f"✅ Successfully saved {len(all_new_content)} entries")
                    
                except Exception as e:
                    print(f"❌ Error saving file: {e}")
            else:
                print(f"\n📭 No new unique content found in this cycle")
        
        except Exception as e:
            print(f"\n❌ Collection error: {e}")
        
        finally:
            self.is_collecting = False
            print(f"\n{'='*60}")
            print(f"📥 AUTO DATA COLLECTION COMPLETED - {datetime.now().strftime('%H:%M:%S')}")
            print(f"📊 New entries collected: {len(all_new_content) if 'all_new_content' in dir() else 0}")
            print(f"{'='*60}\n")
    
    def _search_with_fallbacks(self, query):
        """Search using fallback engines when main engines fail."""
        results = []
        
        for engine_name, engine in self.fallback_engines.items():
            try:
                url = engine['url'].format(query=urllib.parse.quote(query))
                response = self.make_request(url, timeout=engine['timeout'])
                
                if response:
                    parser = engine['parser']
                    engine_results = parser(response)
                    if engine_results:
                        results.extend(engine_results)
                        break
            except Exception as e:
                continue
        
        return results
    
    # ========== BACKGROUND COLLECTION THREAD ==========
    
    def start_auto_collection(self):
        """Start automatic data collection in background thread."""
        if self.collection_thread and self.collection_thread.is_alive():
            print("⚠ Auto collection is already running")
            return
        
        print("🚀 Starting auto data collection (every 2.5 minutes)...")
        self._run_collection_loop()
    
    def _run_collection_loop(self):
        """Run the collection loop in a thread."""
        def loop():
            while True:
                try:
                    self.collect_data_auto()
                except Exception as e:
                    print(f"❌ Collection loop error: {e}")
                
                # Wait 2.5 minutes (150 seconds)
                print(f"⏰ Next collection in 2.5 minutes...")
                time.sleep(150)
        
        self.collection_thread = threading.Thread(target=loop, daemon=True)
        self.collection_thread.start()
    
    def stop_auto_collection(self):
        """Stop automatic data collection."""
        self.is_collecting = False
        print("🛑 Auto collection stopped")
    
    def set_collection_topics(self, topics):
        """Set custom topics for data collection."""
        if isinstance(topics, list):
            self.collection_topics = topics
            print(f"✓ Collection topics updated: {len(topics)} topics")
    
    def add_collection_topic(self, topic):
        """Add a single topic to collection list."""
        if topic not in self.collection_topics:
            self.collection_topics.append(topic)
            print(f"✓ Topic added: {topic}")
    
    # ========== UTILITY FUNCTIONS ==========
    
    def clear_cache(self):
        """Clear all cached searches."""
        self.search_cache = {}
        self.save_cache()
        print("✓ Cache cleared")
    
    def get_cache_stats(self):
        """Get cache statistics."""
        total = len(self.search_cache)
        sources = defaultdict(int)
        for key, entry in self.search_cache.items():
            sources[entry.get('source', 'unknown')] += 1
        
        return {
            'total_entries': total,
            'sources': dict(sources)
        }
    
    def get_collection_stats(self):
        """Get collection statistics."""
        try:
            collected_files = [f for f in os.listdir(self.collected_dir) 
                             if f.startswith('collected_data_') and f.endswith('.txt')]
            total_size = sum(os.path.getsize(os.path.join(self.collected_dir, f)) 
                           for f in collected_files)
            
            return {
                'total_files': len(collected_files),
                'total_hashes': len(self.collected_hashes),
                'total_size_kb': round(total_size / 1024, 2),
                'counter': self.collection_counter
            }
        except Exception as e:
            return {'error': str(e)}
    
    def is_connected(self):
        """Check if internet connection is available."""
        try:
            url = "https://www.google.com"
            self.make_request(url, timeout=5)
            return True
        except:
            return False


# ========== STANDALONE TEST ==========
if __name__ == "__main__":
    print("=" * 60)
    print("🌐 Web Search Handler - Auto Collection Test")
    print("=" * 60)
    
    handler = WebSearchHandler()
    
    # Check connection
    print("\n📡 Checking internet connection...")
    if handler.is_connected():
        print("✓ Internet connection available")
    else:
        print("✗ No internet connection - some features may not work")
    
    # Show stats
    print("\n📊 Cache Statistics:")
    stats = handler.get_cache_stats()
    print(f"  Total cached searches: {stats['total_entries']}")
    
    print("\n📊 Collection Statistics:")
    col_stats = handler.get_collection_stats()
    for key, value in col_stats.items():
        print(f"  {key}: {value}")
    
    # Run one manual collection
    print("\n" + "=" * 60)
    print("RUNNING MANUAL DATA COLLECTION")
    print("=" * 60)
    
    handler.collect_data_auto()
    
    # Show updated stats
    print("\n📊 Updated Collection Statistics:")
    col_stats = handler.get_collection_stats()
    for key, value in col_stats.items():
        print(f"  {key}: {value}")
    
    # Ask to start auto collection
    print("\n" + "=" * 60)
    response = input("Start auto collection (every 2.5 min)? (y/n): ").strip().lower()
    
    if response == 'y':
        handler.start_auto_collection()
        print("\n🔄 Auto collection running in background...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping...")
            handler.stop_auto_collection()
