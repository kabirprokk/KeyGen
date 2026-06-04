import re
import random
import json
import os
import ssl
import urllib.request
import urllib.parse
import hashlib
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

class KeyGenAI:
    def __init__(self, knowledge_dir="knowledge", data_file="data.json", gk_file="gk_knowledge.json"):
        self.name = "KeyGen.ai"
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.knowledge_dir = os.path.join(self.script_dir, knowledge_dir)
        self.data_file = os.path.join(self.script_dir, data_file)
        self.gk_file = os.path.join(self.script_dir, gk_file)
        self.user_mem_file = os.path.join(self.knowledge_dir, "user_mem.txt")
        self.verified_web_file = os.path.join(self.knowledge_dir, "verified_web.txt")
        self.search_cache_file = os.path.join(self.knowledge_dir, "search_cache.json")
        self.raw_data_chunks = []
        self.knowledge_base = []
        self.gk_base = []
        self.search_cache = {}
        
        # Google CSE ID
        self.cse_cx = "c0ddac3f347514713"
        
        self.stopwords = {
            "a", "an", "the", "and", "or", "but", "is", "are", "was", "were",
            "to", "at", "by", "for", "of", "with", "in", "on", "that", "this",
            "it", "its", "be", "been", "being", "have", "has", "had", "do", "does",
            "did", "will", "would", "could", "should", "may", "might", "can", "shall"
        }
        
        # Common country names for nationality detection
        self.country_names = {
            "afghanistan", "albania", "algeria", "argentina", "armenia", "australia",
            "austria", "azerbaijan", "bahamas", "bahrain", "bangladesh", "belarus",
            "belgium", "belize", "benin", "bhutan", "bolivia", "bosnia", "botswana",
            "brazil", "brunei", "bulgaria", "burkina faso", "burundi", "cambodia",
            "cameroon", "canada", "chad", "chile", "china", "colombia", "congo",
            "costa rica", "croatia", "cuba", "cyprus", "czech republic", "denmark",
            "egypt", "england", "ethiopia", "fiji", "finland", "france", "germany",
            "ghana", "greece", "haiti", "hungary", "iceland", "india", "indonesia",
            "iran", "iraq", "ireland", "israel", "italy", "jamaica", "japan", "jordan",
            "kazakhstan", "kenya", "kuwait", "laos", "lebanon", "liberia", "libya",
            "lithuania", "luxembourg", "madagascar", "malawi", "malaysia", "maldives",
            "mali", "malta", "mexico", "mongolia", "morocco", "mozambique", "myanmar",
            "namibia", "nepal", "netherlands", "new zealand", "nicaragua", "niger",
            "nigeria", "north korea", "norway", "oman", "pakistan", "palestine",
            "panama", "paraguay", "peru", "philippines", "poland", "portugal", "qatar",
            "romania", "russia", "rwanda", "saudi arabia", "senegal", "serbia",
            "singapore", "slovakia", "slovenia", "somalia", "south africa", "south korea",
            "spain", "sri lanka", "sudan", "sweden", "switzerland", "syria", "taiwan",
            "tanzania", "thailand", "togo", "trinidad", "tunisia", "turkey", "uganda",
            "ukraine", "united arab emirates", "united kingdom", "united states",
            "uruguay", "uzbekistan", "venezuela", "vietnam", "yemen", "zambia", "zimbabwe",
            "wales", "scotland", "northern ireland", "kosovo", "montenegro", "sudan"
        }
        
        self.greetings = {
            "patterns": [r'^hi$', r'^hello$', r'^hey$', r'^good morning$', r'^good afternoon$',
                         r'^good evening$', r'^howdy$', r'^greetings$', r'^sup$', r"^what's up$",
                         r'^yo$', r'^hola$', r'^bonjour$', r'^heya$', r'^heyy$', r'^hii$',
                         r'^helloo$', r'^morning$', r'^evening$'],
            "responses": [
                "Hello! 👋 How can I help you today?",
                "Hi there! 😊 What would you like to know?",
                "Hey! ✨ Ask me anything!",
                "Greetings! 🌟 How can I assist you?",
                "Hello! 🚀 What can I help you with?",
                "Hi! 💫 What's on your mind?",
                "Hey there! 🎯 Feel free to ask me anything!",
                "Welcome! 🤖 How can I help?"
            ]
        }
        
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        os.makedirs(self.knowledge_dir, exist_ok=True)
        self.load_all_data()
        self.load_search_cache()

    # ---------- Cache ----------
    def load_search_cache(self):
        try:
            if os.path.exists(self.search_cache_file):
                with open(self.search_cache_file, 'r', encoding='utf-8') as f:
                    self.search_cache = json.load(f)
        except:
            self.search_cache = {}

    def save_search_cache(self):
        try:
            if len(self.search_cache) > 500:
                keys = list(self.search_cache.keys())[-500:]
                self.search_cache = {k: self.search_cache[k] for k in keys}
            with open(self.search_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.search_cache, f, indent=2)
        except:
            pass

    # ---------- Tokenization ----------
    def tokenize(self, text):
        if not text:
            return []
        return re.findall(r'\b\w+\b', str(text).lower())

    # ---------- Greetings ----------
    def is_greeting(self, text):
        text_lower = text.lower().strip().rstrip('!.,? ')
        for pattern in self.greetings["patterns"]:
            if re.fullmatch(pattern, text_lower):
                return True
        if len(text_lower.split()) == 1:
            if text_lower in {"hi", "hello", "hey", "yo", "sup", "hola", "bonjour", "heya", "heyy", "hii", "helloo"}:
                return True
        return False

    def get_greeting_response(self):
        return random.choice(self.greetings["responses"])

    def grammar_checker(self, text):
        if not text or not isinstance(text, str):
            return ""
        text = text.strip()
        if not text:
            return ""
        if len(text) > 1:
            text = text[0].upper() + text[1:]
        if text[-1] not in ".!?:\"'":
            text += "."
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\bi\b(?![\'\.])', 'I', text)
        return text

    def clean_text(self, text):
        clean = re.sub(r'<.*?>', '', text)
        noise = ['click here', 'read more', 'cookie', 'privacy policy', 'subscribe', 'advertisement', '©', 'Cached']
        for n in noise:
            clean = re.sub(r'(?i)' + re.escape(n), '', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        clean = re.sub(r'([.!?])\1+', r'\1', clean)
        return clean

    def make_http_request(self, url, timeout=10, json_response=False, headers_extra=None):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        if headers_extra:
            headers.update(headers_extra)
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout, context=self.ssl_context) as resp:
                if json_response:
                    return json.loads(resp.read().decode('utf-8'))
                return resp.read().decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"Request error: {e}")
            return None

    # ---------- Answer Type Detection ----------
    def detect_question_intent(self, question):
        q = question.lower().strip()
        if q.startswith("who"):
            return "person"
        if q.startswith("which nation") or q.startswith("which country") or q.startswith("what country"):
            return "country"
        if q.startswith("which") and ("disease" in q or "illness" in q or "outbreak" in q):
            return "disease"
        if q.startswith("which") and ("team" in q or "club" in q or "player" in q):
            return "team_or_person"
        if q.startswith("which") or q.startswith("what is the name"):
            return "general_choice"
        if q.startswith("what") and ("disease" in q or "outbreak" in q or "virus" in q):
            return "disease"
        if q.startswith("when"):
            return "date"
        if q.startswith("where"):
            return "place"
        if q.startswith("how many"):
            return "number"
        return "general"

    def build_search_query(self, question):
        intent = self.detect_question_intent(question)
        q = question.strip()
        cleaned = re.sub(r'^(who|what|when|where|why|how|which|is|are|do|does)\s+', '', q, flags=re.I).strip()
        
        if intent == "person":
            return f"{cleaned} winner champion name"
        if intent == "country":
            return f"{cleaned} winner champion nation country"
        if intent == "team_or_person":
            return f"{cleaned} winner champion"
        if intent == "disease":
            return f"{cleaned} outbreak disease virus name"
        if intent == "date":
            return f"{cleaned} date schedule"
        if intent == "place":
            return f"{cleaned} location venue"
        if intent == "number":
            return f"{cleaned} total count number"
        return f"{cleaned} answer result"

    # ---------- Entity Extractors ----------
    def extract_winner(self, text):
        patterns = [
            r'(?:won by|champion[:\s]+|victory for|winner[:\s]+|title to|gold to|awarded to)\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
            r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:won|claimed|secured|captured|earned|took|retained|became|crowned)',
            r'(?:defeated|beat|overcame)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
            r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:is|are|was|were)\s+(?:the\s+)?(?:champion|winner|victor)',
            r'(?:champion|winner)[:\s]+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
            r'(?:title|trophy)\s+(?:to|went to|won by)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                winner = match.group(1).strip()
                if len(winner) > 2 and winner.lower() not in {'the', 'and', 'for', 'was', 'has'}:
                    return winner
        return None

    def extract_country(self, text):
        text_lower = text.lower()
        for country in sorted(self.country_names, key=len, reverse=True):
            if country in text_lower:
                return country.title()
        match = re.search(r'(?:won by|champion[:\s]+|winner[:\s]+)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)
        if match:
            return match.group(1)
        return None

    def extract_disease_name(self, text):
        patterns = [
            r'(?:disease|illness|outbreak)\s+(?:of|is|was|called|named)?\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
            r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:virus|disease|fever|syndrome)',
            r'called\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
            r'known as\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                return m.group(1).strip()
        return None

    def extract_date(self, text):
        m = re.search(r'(?:\d{1,2}\s+)?(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}', text)
        if m:
            return m.group(0)
        m = re.search(r'\b(20\d{2})\b', text)
        if m:
            return m.group(0)
        return None

    def extract_place(self, text):
        m = re.search(r'(?:in|at|from|to|venue[:\s]+)\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)', text)
        if m:
            return m.group(1)
        return None

    def extract_answer_from_text(self, question, text, intent):
        if not text:
            return None
        
        text = self.clean_text(text)
        
        # FIXED: De-nested logic blocks so every separate intent executes correctly
        if intent in ("person", "team_or_person", "country", "general_choice"):
            winner = self.extract_winner(text)
            if winner:
                return winner
            
        if intent == "country":
            country = self.extract_country(text)
            if country:
                return country
        
        if intent == "disease":
            disease = self.extract_disease_name(text)
            if disease:
                return disease
        
        if intent == "date":
            date = self.extract_date(text)
            if date:
                return date
        
        if intent == "place":
            place = self.extract_place(text)
            if place:
                return place
        
        # Fallback Indicator Search
        indicator_words = ['won', 'winner', 'champion', 'victory', 'defeated', 'announced', 
                          'declared', 'confirmed', 'result', 'outcome', 'named', 'selected',
                          'chosen', 'elected', 'appointed', 'crowned']
        
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for sent in sentences:
            if any(word in sent.lower() for word in indicator_words):
                for extractor in [self.extract_winner, self.extract_country, 
                                  self.extract_disease_name, self.extract_date, self.extract_place]:
                    result = extractor(sent)
                    if result:
                        return result
                return sent.strip()
        
        for sent in sentences:
            if len(sent) > 20:
                return sent.strip()
        
        return text[:300]

    # ---------- Google CSE Search ----------
       # ---------- Google CSE Search (Fixed) ----------
    def search_cse(self, query):
        """Search using your Google Custom Search Engine with improved parsing."""
        try:
            cse_url = f"https://cse.google.com/cse?cx={self.cse_cx}&q={urllib.parse.quote(query)}"
            
            print(f"🔍 Searching CSE: {query}")
            html = self.make_http_request(cse_url, timeout=10)
            
            if not html:
                print("❌ CSE returned no HTML")
                return None
            
            # Extract structured results
            results = []
            
            # Pattern 1: Extract complete result blocks (title + snippet)
            result_blocks = re.findall(
                r'<div class="gsc-webResult[^"]*".*?</div>\s*</div>\s*</div>',
                html, re.DOTALL
            )
            
            for block in result_blocks[:5]:  # Top 5 results
                # Extract title
                title_match = re.search(r'<a class="gs-title"[^>]*>(.*?)</a>', block, re.DOTALL)
                title = re.sub(r'<.*?>', '', title_match.group(1)).strip() if title_match else ""
                
                # Extract snippet
                snippet_match = re.search(r'<div class="gs-bidi-start-align gs-snippet"[^>]*>(.*?)</div>', block, re.DOTALL)
                if not snippet_match:
                    snippet_match = re.search(r'<div class="gs-snippet"[^>]*>(.*?)</div>', block, re.DOTALL)
                
                snippet = re.sub(r'<.*?>', '', snippet_match.group(1)).strip() if snippet_match else ""
                snippet = re.sub(r'\s+', ' ', snippet)
                
                # Extract visible URL
                url_match = re.search(r'<div class="gs-bidi-start-align gs-visibleUrl[^"]*"[^>]*>(.*?)</div>', block, re.DOTALL)
                url = re.sub(r'<.*?>', '', url_match.group(1)).strip() if url_match else ""
                
                if title or snippet:
                    results.append({
                        'title': self.clean_text(title),
                        'snippet': self.clean_text(snippet),
                        'url': url
                    })
            
            # Pattern 2: If blocks didn't work, try direct snippet extraction
            if not results:
                snippet_matches = re.findall(
                    r'<div class="gs-bidi-start-align gs-snippet"[^>]*>(.*?)</div>',
                    html, re.DOTALL
                )
                for match in snippet_matches[:5]:
                    clean = re.sub(r'<.*?>', '', match)
                    clean = re.sub(r'\s+', ' ', clean).strip()
                    if len(clean) > 50:
                        results.append({
                            'title': '',
                            'snippet': self.clean_text(clean),
                            'url': ''
                        })
            
            if results:
                # Combine titles and snippets for better context
                combined_texts = []
                for r in results[:3]:
                    combined = f"{r['title']}. {r['snippet']}"
                    combined_texts.append(combined)
                
                full_text = " | ".join(combined_texts)
                return self.clean_text(full_text)
            
            print("❌ No snippets found in CSE results")
            return None
            
        except Exception as e:
            print(f"CSE error: {e}")
            return None

    # ---------- Answer Validation ----------
    def validate_answer(self, answer, intent, question):
        """Validate that the extracted answer makes sense for the question type."""
        if not answer:
            return False
        
        answer_lower = answer.lower()
        question_lower = question.lower()
        
        # Reject if answer is just a year for "who" questions
        if intent == "person" and re.match(r'^\d{4}$', answer.strip()):
            return False
        
        # Reject if answer is "La Liga", "Premier League" etc for "club" questions
        if "club" in question_lower and answer_lower in {"la liga", "premier league", "serie a", "bundesliga", "ligue 1", "mls"}:
            return False
        
        # Reject if answer is too short for complex questions
        if len(answer.split()) <= 1 and len(question.split()) > 8:
            # Single word answers are suspicious for long questions
            if intent in ("person", "team_or_person") and not any(c.isupper() for c in answer):
                return False
        
        # Reject generic/definition answers for specific questions
        generic_starts = [
            "the world records", "a list of", "this is a", "refers to",
            "is a term", "is defined", "the history of", "according to"
        ]
        if any(answer_lower.startswith(gs) for gs in generic_starts):
            return False
        
        # Reject if answer is just repeating the question
        question_words = set(self.tokenize(question_lower))
        answer_words = set(self.tokenize(answer_lower))
        if len(answer_words) <= 3 and answer_words.issubset(question_words):
            return False
        
        return True

    # ---------- Improved Answer Extraction ----------
    def extract_answer_from_text(self, question, text, intent):
        """Extract the most direct answer from text based on intent."""
        if not text:
            return None
        
        text = self.clean_text(text)
        candidates = []
        
        # Strategy 1: Look for question-relevant keywords first
        q_lower = question.lower()
        
        # For "which club" questions - look for club names
        if "club" in q_lower or "team" in q_lower:
            club_patterns = [
                r'([A-Z][a-zA-Z]+(?:\s+(?:United|City|Town|Rovers|Rangers|Athletic|Albion|Villa|Forest|Palace|Hotspur|Wednesday|County|Wanderers|Alexandra|Stanley|Orient|Argyle))(?:\s+FC)?)',
                r'([A-Z][a-zA-Z]+(?:\s+FC|\s+Football Club))',
                r'(?:defeated|beat|won against)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
                r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:won|claimed|secured|lifted|took)\s+the',
                r'(?:winner|champion|victory for|trophy to)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
            ]
            for pattern in club_patterns:
                match = re.search(pattern, text)
                if match:
                    club = match.group(1).strip()
                    if len(club) > 3 and club.lower() not in {'the', 'and', 'for', 'was', 'has', 'their', 'this', 'that', 'with', 'from'}:
                        candidates.append(("club_pattern", club))
        
        # For "who" questions about people
        if intent == "person":
            person_patterns = [
                r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:won|claimed|secured|became|crowned|named|selected|elected)',
                r'(?:won by|awarded to|title to|champion[:\s]+|winner[:\s]+)\s*([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:is|was|became)\s+(?:the\s+)?(?:champion|winner|victor)',
            ]
            for pattern in person_patterns:
                match = re.search(pattern, text)
                if match:
                    person = match.group(1).strip()
                    if len(person) > 5 and person.lower() not in {'the world', 'the international', 'the united'}:
                        candidates.append(("person_pattern", person))
        
        # General winner extraction
        winner = self.extract_winner(text)
        if winner:
            candidates.append(("winner", winner))
        
        # Country extraction
        if intent == "country":
            country = self.extract_country(text)
            if country:
                candidates.append(("country", country))
        
        # Disease extraction
        if intent == "disease":
            disease = self.extract_disease_name(text)
            if disease:
                candidates.append(("disease", disease))
        
        # Date extraction
        if intent == "date":
            date = self.extract_date(text)
            if date:
                candidates.append(("date", date))
        
        # Place extraction
        if intent == "place":
            place = self.extract_place(text)
            if place:
                candidates.append(("place", place))
        
        # Validate candidates
        valid_candidates = []
        for source, candidate in candidates:
            if self.validate_answer(candidate, intent, question):
                valid_candidates.append((source, candidate))
        
        if valid_candidates:
            # Return the first valid candidate
            return valid_candidates[0][1]
        
        # Strategy 2: Look for answer-indicator sentences
        indicator_words = ['won', 'winner', 'champion', 'victory', 'defeated', 'announced', 
                          'declared', 'confirmed', 'result', 'crowned', 'lifted', 'secured',
                          'triumphed', 'emerged', 'claimed', 'captured']
        
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        scored_sentences = []
        for sent in sentences:
            sent_clean = sent.strip()
            if len(sent_clean) < 15:
                continue
            
            score = sum(1 for word in indicator_words if word in sent_clean.lower())
            # Bonus for containing capitalized words (likely entities)
            score += len(re.findall(r'\b[A-Z][a-z]+\b', sent_clean)) * 2
            # Penalty for definition-like sentences
            if re.search(r'\b(is a|refers to|defined as|means|known as)\b', sent_clean, re.I):
                score -= 3
            
            if score > 0:
                scored_sentences.append((score, sent_clean))
        
        if scored_sentences:
            scored_sentences.sort(reverse=True, key=lambda x: x[0])
            best_sent = scored_sentences[0][1]
            
            # Try to extract entity from best sentence
            for extractor in [self.extract_winner, self.extract_country, self.extract_disease_name]:
                result = extractor(best_sent)
                if result and self.validate_answer(result, intent, question):
                    return result
            
            return best_sent
        
        # Strategy 3: Return first meaningful sentence
        for sent in sentences:
            if len(sent) > 30 and not any(word in sent.lower() for word in ['cookie', 'privacy', 'subscribe']):
                return sent.strip()
        
        return text[:300]
        
    # ---------- Wikipedia Search (Backup) ----------
    def search_wikipedia(self, query):
        try:
            api_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json&srlimit=1"
            data = self.make_http_request(api_url, json_response=True)
            if not data or not data.get('query', {}).get('search'):
                return None
            page_id = data['query']['search'][0]['pageid']
            extract_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&pageids={page_id}&format=json"
            extract_data = self.make_http_request(extract_url, json_response=True)
            pages = extract_data.get('query', {}).get('pages', {})
            for pid, page in pages.items():
                return page.get('extract', '')[:1000]
        except:
            pass
        return None

    # ---------- DuckDuckGo Search (Backup) ----------
    def search_duckduckgo(self, query):
        try:
            ddg_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
            data = self.make_http_request(ddg_url, json_response=True)
            if data:
                abstract = data.get('AbstractText', '')
                answer = data.get('Answer', '')
                if answer and len(answer) > 5:
                    return self.clean_text(answer)
                elif abstract and len(abstract) > 40:
                    return self.clean_text(abstract)
        except Exception as e:
            print(f"DuckDuckGo error: {e}")
        return None

    # ---------- Google Web Search (Last Resort) ----------
    def search_google_web(self, query):
        google_html = self.make_http_request(
            f"https://www.google.com/search?q={urllib.parse.quote(query)}&hl=en"
        )
        if google_html:
            patterns = [
                r'<div class="BNeawe\s+s3v9rd\s+AP7Wnd">(.*?)</div>',
                r'<span class="st">(.*?)</span>',
            ]
            for pattern in patterns:
                match = re.search(pattern, google_html, re.DOTALL)
                if match:
                    text = re.sub(r'<.*?>', '', match.group(1))
                    text = re.sub(r'\s+', ' ', text).strip()
                    if 60 < len(text) < 2000:
                        return self.clean_text(text)
        return None

    # ---------- Main Search Pipeline ----------
    def web_search(self, question):
        cache_key = hashlib.md5(question.lower().encode()).hexdigest()
        if cache_key in self.search_cache:
            entry = self.search_cache[cache_key]
            if time.time() - entry['timestamp'] < 3600:
                print("✓ Cache hit")
                return entry['data']

        print(f"\n🔍 Searching for: {question}")
        
        years = re.findall(r'\b(20\d{2})\b', question)
        current_year = time.localtime().tm_year
        if years and all(int(y) > current_year for y in years):
            result = "This event is in the future – reliable data is not yet available."
            self.search_cache[cache_key] = {'data': result, 'timestamp': time.time()}
            self.save_search_cache()
            return result

        intent = self.detect_question_intent(question)
        search_query = self.build_search_query(question)
        candidates = []

        print("📡 Trying CSE (primary)...")
        cse_result = self.search_cse(search_query)
        if cse_result:
            candidates.append(("cse", cse_result))
            print("✓ CSE result found")

        print("📡 Trying Wikipedia...")
        wiki_result = self.search_wikipedia(search_query)
        if wiki_result:
            candidates.append(("wikipedia", self.clean_text(wiki_result)))
            print("✓ Wikipedia result found")

        print("📡 Trying DuckDuckGo...")
        ddg_result = self.search_duckduckgo(search_query)
        if ddg_result:
            candidates.append(("ddg", ddg_result))
            print("✓ DuckDuckGo result found")

        print("📡 Trying Google Web...")
        google_result = self.search_google_web(search_query)
        if google_result:
            candidates.append(("google", google_result))
            print("✓ Google result found")

        if not candidates:
            print("❌ No results from any source")
            return None

        for source, text in candidates:
            answer = self.extract_answer_from_text(question, text, intent)
            if answer and len(answer) > 1:
                if len(answer.split()) <= 5:
                    result = answer
                    self.search_cache[cache_key] = {'data': result, 'timestamp': time.time()}
                    self.save_search_cache()
                    print(f"✓ Extracted answer: {result}")
                    return result
                if any(word in answer.lower() for word in ['won', 'winner', 'champion', 'defeated']):
                    result = answer
                    self.search_cache[cache_key] = {'data': result, 'timestamp': time.time()}
                    self.save_search_cache()
                    print(f"✓ Extracted sentence: {result[:100]}...")
                    return result

        best_text = ""
        best_score = -1
        q_words = set(self.tokenize(question))
        
        for source, text in candidates:
            score = len(q_words.intersection(set(self.tokenize(text)))) * 2
            if re.search(r'\b(won|champion|victory|winner|awarded|defeated|result)\b', text, re.I):
                score += 30
            if len(text) < 400:
                score += 10
            source_weights = {"cse": 15, "wikipedia": 10, "ddg": 5, "google": 3}
            score += source_weights.get(source, 0)
            
            if score > best_score:
                best_score = score
                best_text = text

        if best_text and len(best_text) > 20:
            sentences = re.split(r'(?<=[.!?])\s+', best_text)
            final = sentences[0] if sentences else best_text
            final = self.clean_text(final)
            if len(final) > 500:
                final = final[:500].rsplit(' ', 1)[0] + "..."
            
            self.search_cache[cache_key] = {'data': final, 'timestamp': time.time()}
            self.save_search_cache()
            print(f"✓  {final[:100]}...")
            return final

        return None

    # ---------- Local Knowledge ----------
    def calculate_relevance_score(self, question, text):
        if not question or not text:
            return 0
        q_words = set(self.tokenize(question))
        t_words = set(self.tokenize(text))
        if not q_words:
            return 0
        intersection = len(q_words.intersection(t_words))
        union = len(q_words.union(t_words))
        return intersection / union if union > 0 else 0

    def search_local_knowledge(self, query):
        if not query:
            return None, 0
        tokens = self.tokenize(query)
        keywords = [t for t in tokens if t not in self.stopwords and len(t) > 2]
        if not keywords:
            return None, 0
        best_match = None
        highest_score = 0
        for sentence in self.raw_data_chunks:
            score = self.calculate_relevance_score(query, sentence)
            score += sum(1 for kw in keywords if kw in sentence.lower()) * 0.05
            if score > highest_score:
                highest_score = score
                best_match = sentence
        return best_match, highest_score

    # ---------- Response Pipeline ----------
    def get_answer_with_fallback(self, question):
        fact_starters = ("who", "what", "when", "where", "why", "how", "which", "is", "are", "do", "does")
        if question.lower().startswith(fact_starters) or "?" in question:
            return self.web_search(question)
        local, conf = self.search_local_knowledge(question)
        if local and conf > 0.3 and len(local) > 80:
            return local
        return self.web_search(question)

    def learn_from_user(self, text):
        if not text or len(text.split()) < 8 or "?" in text:
            return False
        factual_patterns = [" is ", " was ", " are ", " were ", " has ", " have "]
        if any(pattern in text.lower() for pattern in factual_patterns):
            try:
                with open(self.user_mem_file, 'a', encoding='utf-8') as f:
                    f.write(text.strip() + ".\n")
                self.raw_data_chunks.append(text.strip())
                return True
            except:
                pass
        return False

    def load_all_data(self):
        json_files = [(self.data_file, 'knowledge_base'), (self.gk_file, 'gk_base')]
        for file_path, attr_name in json_files:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        setattr(self, attr_name, json.load(f))
                else:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump([], f)
                    setattr(self, attr_name, [])
            except:
                setattr(self, attr_name, [])
        if os.path.exists(self.knowledge_dir):
            for filename in os.listdir(self.knowledge_dir):
                if filename.endswith(".txt"):
                    filepath = os.path.join(self.knowledge_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            text = f.read()
                            if text.strip():
                                sentences = re.split(r'(?<=[.!?])\s+', text)
                                self.raw_data_chunks.extend([s.strip() for s in sentences if len(s) > 10])
                    except:
                        pass

    def get_response(self, user_input):
        if not user_input or not user_input.strip():
            return "Please ask me something! 😊"
        raw = user_input.strip()
        low = raw.lower()

        if self.is_greeting(raw):
            return self.get_greeting_response()

        if low.startswith("learn about "):
            topic = raw[12:].strip()
            result = self.web_search(topic)
            if result:
                return result
            return f"Couldn't find information about '{topic}'."

        answer = self.get_answer_with_fallback(raw)
        if answer:
            # Try parsing metadata context updates implicitly
            self.learn_from_user(raw)
            return self.grammar_checker(answer)
        return "I couldn't find a reliable answer. Try rephrasing your question."


# ---------- Web Server ----------
# Global instances for server binding
bot_instance = KeyGenAI()

class ChatHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # FIXED: Closed out and structured the elegant Dark UI HTML view fully
            html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KeyGen.ai - CSE Powered</title>
    <style>
        :root { --bg: #000; --surface: #0a0a0a; --surface2: #111; --border: #1a1a1a; --text: #fff; --text-secondary: #888; --glow: #fff; --accent: #4285f4; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 16px; }
        .container { background: var(--surface); border-radius: 20px; max-width: 750px; width: 100%; overflow: hidden; border: 1px solid var(--border); box-shadow: 0 0 30px rgba(255,255,255,0.03); }
        .header { padding: 20px 24px; display: flex; align-items: center; gap: 14px; border-bottom: 1px solid var(--border); background: var(--surface2); }
        .header-icon { width: 42px; height: 42px; background: var(--bg); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; border: 1px solid var(--border); }
        .header-text h1 { color: var(--text); font-size: 18px; font-weight: 600; }
        .header-text p { color: var(--text-secondary); font-size: 12px; }
        .status-dot { width: 6px; height: 6px; background: #4CAF50; border-radius: 50%; display: inline-block; margin-right: 6px; box-shadow: 0 0 8px #4CAF50; animation: glow 2s infinite; }
        @keyframes glow { 0%, 100% { box-shadow: 0 0 8px #4CAF50; } 50% { box-shadow: 0 0 16px #4CAF50; } }
        #chat-container { height: 420px; overflow-y: auto; padding: 20px; background: var(--surface); scroll-behavior: smooth; }
        #chat-container::-webkit-scrollbar { width: 4px; } #chat-container::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
        .message-wrapper { display: flex; margin-bottom: 16px; animation: slideIn 0.25s ease-out; }
        @keyframes slideIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        .message-wrapper.user { justify-content: flex-end; }
        .message { max-width: 78%; padding: 12px 16px; border-radius: 16px; position: relative; line-height: 1.45; font-size: 14px; word-wrap: break-word; white-space: pre-wrap; }
        .message-wrapper.user .message { background: var(--text); color: var(--bg); border-bottom-right-radius: 4px; font-weight: 500; }
        .message-wrapper.ai .message { background: var(--surface2); color: var(--text); border-bottom-left-radius: 4px; border: 1px solid var(--border); }
        .input-area { padding: 16px 20px; background: var(--surface2); border-top: 1px solid var(--border); display: flex; gap: 12px; }
        input { flex: 1; background: var(--bg); border: 1px solid var(--border); border-radius: 12px; padding: 14px 16px; color: var(--text); font-size: 14px; outline: none; transition: border-color 0.2s; }
        input:focus { border-color: #555; }
        button { background: var(--text); color: var(--bg); border: none; padding: 0 24px; border-radius: 12px; font-weight: 600; font-size: 14px; cursor: pointer; transition: opacity 0.2s; }
        button:hover { opacity: 0.9; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-icon">🤖</div>
            <div class="header-text">
                <h1>KeyGen.ai</h1>
                <p><span class="status-dot"></span>Online | Multi-Engine Knowledge Node</p>
            </div>
        </div>
        <div id="chat-container">
            <div class="message-wrapper ai">
                <div class="message">Hello! I am KeyGen.ai. Ask me anything, or type "learn about &lt;topic&gt;" to research. 👋</div>
            </div>
        </div>
        <div class="input-area">
            <input type="text" id="user-input" placeholder="Ask a question or feed knowledge..." onkeypress="if(event.key==='Enter') sendMessage()">
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        const chatContainer = document.getElementById('chat-container');
        const userInput = document.getElementById('user-input');

        function appendMessage(text, sender) {
            const wrapper = document.createElement('div');
            wrapper.className = `message-wrapper ${sender}`;
            const msgNode = document.createElement('div');
            msgNode.className = 'message';
            msgNode.textContent = text;
            wrapper.appendChild(msgNode);
            chatContainer.appendChild(wrapper);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        async function sendMessage() {
            const text = userInput.value.trim();
            if(!text) return;
            
            appendMessage(text, 'user');
            userInput.value = '';
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                const data = await response.json();
                appendMessage(data.reply, 'ai');
            } catch (err) {
                appendMessage('Error establishing connection to agent.', 'ai');
            }
        }
    </script>
</body>
</html>
'''
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_error(404, "File Not Found")

    # FIXED: Added the required POST intercept router to process chat updates dynamically
    def do_POST(self):
        if self.path == '/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                req_json = json.loads(post_data.decode('utf-8'))
                user_msg = req_json.get('message', '')
                
                # Fetch output from global agent
                bot_reply = bot_instance.get_response(user_msg)
                
                response_data = json.dumps({"reply": bot_reply})
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(response_data.encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self.send_error(404)

def run_server(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, ChatHandler)
    print(f"🚀 KeyGen.ai server running locally on http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping engine server pipeline safely...")
        httpd.server_close()

if __name__ == "__main__":
    # Runs the app locally
    run_server()
