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
        self.stopwords = {
            "a", "an", "the", "and", "or", "but", "is", "are", "was", "were",
            "to", "at", "by", "for", "of", "with", "in", "on", "that", "this",
            "it", "its", "be", "been", "being", "have", "has", "had", "do", "does",
            "did", "will", "would", "could", "should", "may", "might", "can", "shall"
        }
        # Common country names (lowercase) for nationality detection
        self.country_names = {
            "afghanistan", "albania", "algeria", "andorra", "angola", "argentina", "armenia", "australia",
            "austria", "azerbaijan", "bahamas", "bahrain", "bangladesh", "barbados", "belarus", "belgium",
            "belize", "benin", "bhutan", "bolivia", "bosnia", "botswana", "brazil", "brunei", "bulgaria",
            "burkina faso", "burundi", "cambodia", "cameroon", "canada", "cape verde", "chad", "chile",
            "china", "colombia", "comoros", "congo", "costa rica", "croatia", "cuba", "cyprus",
            "czech republic", "denmark", "djibouti", "dominica", "dominican republic", "ecuador", "egypt",
            "el salvador", "equatorial guinea", "eritrea", "estonia", "ethiopia", "fiji", "finland", "france",
            "gabon", "gambia", "georgia", "germany", "ghana", "greece", "grenada", "guatemala", "guinea",
            "guinea-bissau", "guyana", "haiti", "honduras", "hungary", "iceland", "india", "indonesia",
            "iran", "iraq", "ireland", "israel", "italy", "jamaica", "japan", "jordan", "kazakhstan",
            "kenya", "kiribati", "korea, north", "korea, south", "kosovo", "kuwait", "kyrgyzstan", "laos",
            "latvia", "lebanon", "lesotho", "liberia", "libya", "liechtenstein", "lithuania", "luxembourg",
            "macedonia", "madagascar", "malawi", "malaysia", "maldives", "mali", "malta", "marshall islands",
            "mauritania", "mauritius", "mexico", "micronesia", "moldova", "monaco", "mongolia", "montenegro",
            "morocco", "mozambique", "myanmar", "namibia", "nauru", "nepal", "netherlands", "new zealand",
            "nicaragua", "niger", "nigeria", "norway", "oman", "pakistan", "palau", "panama",
            "papua new guinea", "paraguay", "peru", "philippines", "poland", "portugal", "qatar", "romania",
            "russia", "rwanda", "saint kitts", "saint lucia", "saint vincent", "samoa", "san marino",
            "sao tome", "saudi arabia", "senegal", "serbia", "seychelles", "sierra leone", "singapore",
            "slovakia", "slovenia", "solomon islands", "somalia", "south africa", "south sudan", "spain",
            "sri lanka", "sudan", "suriname", "swaziland", "sweden", "switzerland", "syria", "taiwan",
            "tajikistan", "tanzania", "thailand", "timor-leste", "togo", "tonga", "trinidad and tobago",
            "tunisia", "turkey", "turkmenistan", "tuvalu", "uganda", "ukraine", "united arab emirates",
            "united kingdom", "united states", "uruguay", "uzbekistan", "vanuatu", "vatican", "venezuela",
            "vietnam", "yemen", "zambia", "zimbabwe", "england", "scotland", "wales", "northern ireland"
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

    # Cache
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

    def tokenize(self, text):
        if not text:
            return []
        return re.findall(r'\b\w+\b', str(text).lower())

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
        noise = ['click here', 'read more', 'cookie', 'privacy policy', 'subscribe', 'advertisement', '©']
        for n in noise:
            clean = re.sub(r'(?i)' + re.escape(n), '', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        clean = re.sub(r'([.!?])\1+', r'\1', clean)
        return clean

    def make_http_request(self, url, timeout=8, json_response=False, headers_extra=None):
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

    # ----- Answer extraction -----
    def detect_question_intent(self, question):
        """Return the type of answer expected."""
        q = question.lower().strip()
        if q.startswith("who"):
            return "person"
        if q.startswith("which nation") or q.startswith("which country") or q.startswith("what country"):
            return "country"
        if q.startswith("which") and ("disease" in q or "illness" in q or "outbreak" in q):
            return "disease"
        if q.startswith("which") and ("team" in q or "club" in q or "player" in q):
            return "team_or_person"
        if q.startswith("which"):
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
        """Reformulate the question to get a more targeted answer."""
        intent = self.detect_question_intent(question)
        q = question.strip()
        # Remove leading question words
        cleaned = re.sub(r'^(who|what|when|where|why|how|which|is|are|do|does)\s+', '', q, flags=re.I).strip()
        if intent == "person":
            return f"{cleaned} name who"
        if intent == "country":
            return f"{cleaned} winner nation"
        if intent == "team_or_person":
            return f"{cleaned} winner"
        if intent == "disease":
            return f"{cleaned} outbreak disease name"
        if intent == "date":
            return f"{cleaned} date"
        if intent == "place":
            return f"{cleaned} location"
        if intent == "number":
            return f"{cleaned} count"
        # For general, just add "answer"
        return f"{cleaned} answer"

    def extract_winner(self, text):
        """Try to find a winner/loser/champion from text."""
        patterns = [
            r'(?:won by|champion[:\s]+|victory for|defeated by|title went to|gold medal to|winner[:\s]+|was awarded to)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:won|claimed|secured|captured|earned|took|retained)',
            r'(?:defeated|beat|overcame)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:is|are|was|were)\s+(?:the\s+)?(?:champion|winner|victor)',
            r'(?:the\s+)?(?:champion|winner|victor)\s+(?:is|was)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None

    def extract_country(self, text):
        """Extract a country name from text using known list + capitalization."""
        # First try exact match with known countries (case-insensitive)
        text_lower = text.lower()
        for country in self.country_names:
            if country in text_lower:
                # Return properly capitalized version
                return country.title()
        # Fallback: look for a capitalized phrase that might be a country
        match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', text)
        if match:
            return match.group(1)
        return None

    def extract_disease_name(self, text):
        patterns = [
            r'(?:disease|illness|outbreak)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+virus',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+disease',
            r'called\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                return m.group(1)
        return None

    def extract_date(self, text):
        m = re.search(r'(?:\d{1,2}\s+)?(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}', text)
        if m:
            return m.group(0)
        m = re.search(r'\b(20\d{2})\b', text)
        if m:
            return m.group(0)
        return None

    def extract_place(self, text):
        m = re.search(r'(?:in|at|from|to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)
        if m:
            return m.group(1)
        return None

    def extract_best_answer(self, question, text, intent):
        """Given a text snippet, try to extract the most direct answer."""
        if not text:
            return None
        # Clean
        text = self.clean_text(text)
        # Try winner extraction first if intent implies a winner
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
        # Fallback: take the first sentence that seems to contain an answer indicator
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Look for sentences with the word "won", "champion", "winner", "awarded", etc.
        for sent in sentences:
            if re.search(r'(?i)\b(won|champion|victory|awarded|title|gold|medal|defeated)\b', sent):
                return sent.strip()
        # If nothing, return first sentence
        if sentences:
            return sentences[0].strip()
        return text

    # ----- Web search (multi‑source) -----
    def web_search(self, question):
        cache_key = hashlib.md5(question.lower().encode()).hexdigest()
        if cache_key in self.search_cache:
            entry = self.search_cache[cache_key]
            if time.time() - entry['timestamp'] < 3600:
                return entry['data']

        print(f"🔍 Searching: {question}")
        # Check for purely future events
        years = re.findall(r'\b(20\d{2})\b', question)
        current_year = time.localtime().tm_year
        if years and all(int(y) > current_year for y in years):
            result = "This event is in the future – no reliable data yet."
            self.search_cache[cache_key] = {'data': result, 'timestamp': time.time()}
            self.save_search_cache()
            return result

        intent = self.detect_question_intent(question)
        search_query = self.build_search_query(question)

        candidates = []

        # 1. DuckDuckGo Instant Answer
        try:
            ddg_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(search_query)}&format=json&no_html=1&skip_disambig=1"
            data = self.make_http_request(ddg_url, json_response=True)
            if data:
                abstract = data.get('AbstractText', '')
                answer = data.get('Answer', '')
                if answer and len(answer) > 5:
                    candidates.append(("ddg_direct", self.clean_text(answer)))
                elif abstract and len(abstract) > 40:
                    candidates.append(("ddg_abstract", self.clean_text(abstract)))
        except Exception as e:
            print(f"DuckDuckGo error: {e}")

        # 2. Wikipedia (but only first paragraph)
        wiki = self.search_wikipedia(search_query)
        if wiki:
            candidates.append(("wikipedia", self.clean_text(wiki)))

        # 3. Google snippet (featured snippet)
        google_html = self.make_http_request(
            f"https://www.google.com/search?q={urllib.parse.quote(search_query)}&hl=en"
        )
        if google_html:
            snippet = self.extract_google_snippet(google_html)
            if snippet:
                candidates.append(("google_snippet", self.clean_text(snippet)))
            # Also try knowledge panel (definitions)
            kp = self.extract_google_knowledge_panel(google_html)
            if kp:
                candidates.append(("google_kp", self.clean_text(kp)))

        # 4. Reddit (top posts)
        try:
            reddit_url = f"https://www.reddit.com/search.json?q={urllib.parse.quote(search_query)}&limit=2&sort=relevance"
            reddit_data = self.make_http_request(reddit_url, json_response=True, headers_extra={'User-Agent': 'KeyGenAI/1.0'})
            if reddit_data and 'data' in reddit_data:
                for post in reddit_data['data']['children'][:2]:
                    pdata = post['data']
                    content = pdata.get('title', '') + ' ' + pdata.get('selftext', '')
                    if len(content) > 40:
                        candidates.append(("reddit", self.clean_text(content)))
        except Exception as e:
            print(f"Reddit error: {e}")

        if not candidates:
            print("❌ No results")
            return None

        # Try to extract direct answer
        for source, text in candidates:
            answer = self.extract_best_answer(question, text, intent)
            if answer and len(answer) > 1:
                # If answer is just a short entity, return it
                if len(answer.split()) <= 5 and not answer.endswith('.'):
                    result = answer
                    self.search_cache[cache_key] = {'data': result, 'timestamp': time.time()}
                    self.save_search_cache()
                    return result

        # Fallback: pick the best sentence overall
        best_text = ""
        best_score = -1
        q_words = set(self.tokenize(question))
        for source, text in candidates:
            # Score by keyword overlap, but heavily boost sentences that contain winner/answer indicators
            score = len(q_words.intersection(set(self.tokenize(text)))) * 2
            # Boost if contains winning words
            if re.search(r'\b(won|champion|victory|winner|awarded|defeated)\b', text, re.I):
                score += 20
            # Prefer shorter, more focused answers
            if len(text) < 300:
                score += 10
            if source in ("google_snippet", "ddg_direct"):
                score += 5
            if score > best_score:
                best_score = score
                best_text = text

        if best_text:
            sentences = re.split(r'(?<=[.!?])\s+', best_text)
            final = sentences[0] if sentences else best_text
            final = self.clean_text(final)
            if len(final) > 500:
                final = final[:500].rsplit(' ', 1)[0] + "..."
            self.search_cache[cache_key] = {'data': final, 'timestamp': time.time()}
            self.save_search_cache()
            return final
        return None

    def extract_google_snippet(self, html):
        patterns = [
            r'<div class="BNeawe\s+s3v9rd\s+AP7Wnd">(.*?)</div>',
            r'<span class="st">(.*?)</span>',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                text = re.sub(r'<.*?>', '', match.group(1))
                text = re.sub(r'\s+', ' ', text).strip()
                if 60 < len(text) < 2000:
                    return text
        return None

    def extract_google_knowledge_panel(self, html):
        patterns = [
            r'<div class="kno-rdesc"[^>]*>.*?<span[^>]*>(.*?)</span>',
            r'<div class="LGOjhe"[^>]*>.*?<span[^>]*>(.*?)</span>',
            r'<div class="kno-ecr-pt"[^>]*>(.*?)</div>',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                text = re.sub(r'<.*?>', '', match.group(1)).strip()
                if 20 < len(text) < 800:
                    return text
        return None

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
                return page.get('extract', '')[:800]
        except:
            pass
        return None

    # Local knowledge
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
            return self.grammar_checker(answer)
        return "I couldn't find a reliable answer. Try rephrasing."


# ----- Web Server (same clean UI) -----
class ChatHandler(BaseHTTPRequestHandler):
    bot = None

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = '''<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>KeyGen.ai</title>
                <style>
                    :root { --bg: #000; --surface: #0a0a0a; --surface2: #111; --border: #1a1a1a; --text: #fff; --text-secondary: #888; --glow: #fff; }
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 16px; }
                    .container { background: var(--surface); border-radius: 20px; max-width: 750px; width: 100%; overflow: hidden; border: 1px solid var(--border); box-shadow: 0 0 30px rgba(255,255,255,0.03), 0 0 60px rgba(255,255,255,0.01); }
                    .header { padding: 20px 24px; display: flex; align-items: center; gap: 14px; border-bottom: 1px solid var(--border); background: var(--surface2); }
                    .header-icon { width: 42px; height: 42px; background: var(--bg); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; border: 1px solid var(--border); box-shadow: 0 0 15px rgba(255,255,255,0.05); }
                    .header-text h1 { color: var(--text); font-size: 18px; font-weight: 600; }
                    .header-text p { color: var(--text-secondary); font-size: 12px; }
                    .status-dot { width: 6px; height: 6px; background: var(--glow); border-radius: 50%; display: inline-block; margin-right: 6px; box-shadow: 0 0 8px var(--glow); animation: glow 2s infinite; }
                    @keyframes glow { 0%, 100% { box-shadow: 0 0 8px var(--glow); } 50% { box-shadow: 0 0 16px var(--glow); } }
                    #chat-container { height: 420px; overflow-y: auto; padding: 20px; background: var(--surface); scroll-behavior: smooth; }
                    #chat-container::-webkit-scrollbar { width: 4px; } #chat-container::-webkit-scrollbar-track { background: transparent; } #chat-container::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
                    .message-wrapper { display: flex; margin-bottom: 16px; animation: slideIn 0.25s ease-out; }
                    @keyframes slideIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
                    .message-wrapper.user { justify-content: flex-end; }
                    .message { max-width: 78%; padding: 12px 16px; border-radius: 16px; position: relative; line-height: 1.45; font-size: 14px; word-wrap: break-word; white-space: pre-wrap; }
                    .message-wrapper.user .message { background: var(--text); color: var(--bg); border-bottom-right-radius: 4px; font-weight: 500; }
                    .message-wrapper.ai .message { background: var(--surface2); color: var(--text); border-bottom-left-radius: 4px; border: 1px solid var(--border); }
                    .message-avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; margin: 0 8px; }
                    .message-wrapper.ai .message-avatar { background: var(--surface2); border: 1px solid var(--border); } .message-wrapper.user .message-avatar { background: var(--text); color: var(--bg); }
                    .typing-indicator { display: flex; align-items: center; gap: 10px; padding: 12px 16px; background: var(--surface2); border-radius: 16px; border-bottom-left-radius: 4px; border: 1px solid var(--border); max-width: 80px; }
                    .typing-dot { width: 6px; height: 6px; background: var(--text-secondary); border-radius: 50%; animation: typing 1.4s infinite; }
                    .typing-dot:nth-child(2) { animation-delay: 0.2s; } .typing-dot:nth-child(3) { animation-delay: 0.4s; }
                    @keyframes typing { 0%, 60%, 100% { transform: translateY(0); opacity: 0.3; } 30% { transform: translateY(-6px); opacity: 1; } }
                    .input-container { padding: 16px 20px; background: var(--surface2); border-top: 1px solid var(--border); display: flex; gap: 10px; align-items: center; }
                    #input { flex: 1; padding: 12px 16px; background: var(--surface); border: 1px solid var(--border); border-radius: 14px; color: var(--text); font-size: 14px; outline: none; transition: all 0.2s; }
                    #input:focus { border-color: var(--text); box-shadow: 0 0 0 2px rgba(255,255,255,0.05); } #input::placeholder { color: #444; }
                    .btn { height: 42px; border: 1px solid var(--border); border-radius: 12px; color: var(--text); font-size: 14px; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; justify-content: center; flex-shrink: 0; background: var(--surface); }
                    .send-btn { width: 42px; font-size: 18px; } .send-btn:hover { background: var(--text); color: var(--bg); border-color: var(--text); }
                    .stop-btn { width: 42px; font-size: 16px; display: none; } .stop-btn:hover { background: #ff3333; border-color: #ff3333; color: white; } .stop-btn.active { display: flex; } .send-btn.hidden { display: none; }
                    .suggestions { display: flex; gap: 8px; padding: 12px 20px; flex-wrap: wrap; background: var(--surface); }
                    .suggestion-chip { padding: 7px 14px; background: var(--surface2); border: 1px solid var(--border); border-radius: 20px; color: var(--text-secondary); font-size: 12px; cursor: pointer; transition: all 0.2s; white-space: nowrap; }
                    .suggestion-chip:hover { background: var(--text); color: var(--bg); border-color: var(--text); }
                    .timestamp { font-size: 10px; color: #444; margin-top: 4px; padding: 0 8px; }
                    @media (max-width: 600px) { body { padding: 0; } .container { border-radius: 0; height: 100vh; display: flex; flex-direction: column; } #chat-container { flex: 1; height: auto; } .message { max-width: 85%; } }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="header-icon">🤖</div>
                        <div class="header-text">
                            <h1>KeyGen.ai</h1>
                            <p><span class="status-dot"></span>Online</p>
                        </div>
                    </div>
                    <div id="chat-container">
                        <div class="message-wrapper ai">
                            <div class="message-avatar">🤖</div>
                            <div>
                                <div class="message">Hello! 👋 I'm KeyGen.ai. Ask me anything!</div>
                                <div class="timestamp">Just now</div>
                            </div>
                        </div>
                    </div>
                    <div class="suggestions">
                        <span class="suggestion-chip" onclick="useSuggestion(this)">Who won F1 2025?</span>
                        <span class="suggestion-chip" onclick="useSuggestion(this)">What is AI?</span>
                        <span class="suggestion-chip" onclick="useSuggestion(this)">Define quantum computing</span>
                        <span class="suggestion-chip" onclick="useSuggestion(this)">Who is India's PM?</span>
                    </div>
                    <div class="input-container">
                        <input type="text" id="input" placeholder="Ask anything..." autofocus>
                        <button class="btn send-btn" id="sendBtn" onclick="sendMessage()">➤</button>
                        <button class="btn stop-btn" id="stopBtn" onclick="stopGeneration()">■</button>
                    </div>
                </div>
                <script>
                    const chatContainer = document.getElementById('chat-container');
                    const input = document.getElementById('input');
                    const sendBtn = document.getElementById('sendBtn');
                    const stopBtn = document.getElementById('stopBtn');
                    let isGenerating = false;
                    let abortController = null;

                    function getTime() { return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); }
                    function addMessage(text, isUser) {
                        const wrapper = document.createElement('div');
                        wrapper.className = 'message-wrapper ' + (isUser ? 'user' : 'ai');
                        const avatar = document.createElement('div'); avatar.className = 'message-avatar'; avatar.textContent = isUser ? '👤' : '🤖';
                        const container = document.createElement('div');
                        const message = document.createElement('div'); message.className = 'message'; message.textContent = text;
                        const timestamp = document.createElement('div'); timestamp.className = 'timestamp'; timestamp.textContent = getTime();
                        container.appendChild(message); container.appendChild(timestamp);
                        if (isUser) { wrapper.appendChild(container); wrapper.appendChild(avatar); }
                        else { wrapper.appendChild(avatar); wrapper.appendChild(container); }
                        chatContainer.appendChild(wrapper);
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                        return message;
                    }
                    function showTypingIndicator() {
                        const wrapper = document.createElement('div'); wrapper.className = 'message-wrapper ai'; wrapper.id = 'typing-wrapper';
                        const avatar = document.createElement('div'); avatar.className = 'message-avatar'; avatar.textContent = '🤖';
                        const indicator = document.createElement('div'); indicator.className = 'typing-indicator';
                        indicator.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
                        wrapper.appendChild(avatar); wrapper.appendChild(indicator);
                        chatContainer.appendChild(wrapper);
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    }
                    function removeTypingIndicator() { const typing = document.getElementById('typing-wrapper'); if (typing) typing.remove(); }
                    function setGeneratingState(generating) {
                        isGenerating = generating;
                        if (generating) { sendBtn.classList.add('hidden'); stopBtn.classList.add('active'); input.disabled = true; }
                        else { sendBtn.classList.remove('hidden'); stopBtn.classList.remove('active'); input.disabled = false; input.focus(); }
                    }
                    function stopGeneration() { if (abortController) { abortController.abort(); abortController = null; } isGenerating = false; removeTypingIndicator(); setGeneratingState(false); }
                    async function typeWriterEffect(element, text, speed = 12) {
                        element.textContent = '';
                        for (let i = 0; i < text.length; i++) {
                            if (!isGenerating) break;
                            element.textContent += text.charAt(i);
                            chatContainer.scrollTop = chatContainer.scrollHeight;
                            await new Promise(resolve => setTimeout(resolve, speed));
                        }
                    }
                    async function sendMessage() {
                        const message = input.value.trim();
                        if (!message || isGenerating) return;
                        addMessage(message, true); input.value = ''; showTypingIndicator(); setGeneratingState(true);
                        abortController = new AbortController();
                        try {
                            const response = await fetch('/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({message: message}), signal: abortController.signal });
                            const data = await response.json();
                            removeTypingIndicator();
                            if (isGenerating) { const aiMessage = addMessage('', false); await typeWriterEffect(aiMessage, data.response, 12); }
                        } catch (error) { if (error.name !== 'AbortError') { removeTypingIndicator(); addMessage('⚠️ Connection error. Try again.', false); } }
                        setGeneratingState(false); abortController = null;
                    }
                    function useSuggestion(chip) { input.value = chip.textContent; sendMessage(); }
                    input.addEventListener('keypress', function(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });
                    input.focus();
                </script>
            </body>
            </html>
            '''
            self.wfile.write(html.encode())
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'healthy'}).encode())

    def do_POST(self):
        if self.path == '/chat':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
                user_msg = data.get('message', '')
                response_text = self.bot.get_response(user_msg)
            except Exception as e:
                response_text = f"Error: {str(e)}"
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            self.wfile.write(json.dumps({'response': response_text}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_server():
    port = int(os.environ.get("PORT", 10000))
    bot = KeyGenAI()
    ChatHandler.bot = bot
    server_address = ('0.0.0.0', port)
    server = HTTPServer(server_address, ChatHandler)
    print(f"🤖 KeyGen.ai running on http://0.0.0.0:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()

if __name__ == "__main__":
    run_server()
