import re
import random
import json
import os
import hashlib
import time
import math
from collections import defaultdict, Counter
from http.server import HTTPServer, BaseHTTPRequestHandler

class KeyGenAI:
    def __init__(self, knowledge_dir="knowledge", data_file="data.json", gk_file="gk_knowledge.json"):
        self.name = "KeyGen.ai"
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.knowledge_dir = os.path.join(self.script_dir, knowledge_dir)
        self.data_file = os.path.join(self.script_dir, data_file)
        self.gk_file = os.path.join(self.script_dir, gk_file)
        self.user_mem_file = os.path.join(self.knowledge_dir, "user_mem.txt")
        self.learned_file = os.path.join(self.knowledge_dir, "learned_knowledge.json")
        
        # Core knowledge storage
        self.knowledge_base = []
        self.gk_base = []
        self.learned_facts = {}
        self.raw_data_chunks = []
        self.sentence_bank = []
        self.entity_index = defaultdict(list)
        self.ngram_index = defaultdict(list)
        self.word_freq = Counter()
        self.entity_map = {}
        
        # Enhanced tokenization stopwords
        self.stopwords = {
            "a", "an", "the", "and", "or", "but", "is", "are", "was", "were",
            "to", "at", "by", "for", "of", "with", "in", "on", "that", "this",
            "it", "its", "be", "been", "being", "have", "has", "had", "do", "does",
            "did", "will", "would", "could", "should", "may", "might", "can", "shall",
            "i", "you", "he", "she", "we", "they", "me", "him", "her", "us", "them",
            "my", "your", "his", "our", "their", "mine", "yours", "hers", "ours", "theirs"
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
        
        os.makedirs(self.knowledge_dir, exist_ok=True)
        self.load_all_data()
        self.build_indexes()

    # ========== POWERFUL TOKENIZATION ENGINE ==========
    
    def tokenize(self, text):
        """Advanced tokenization with entity recognition."""
        if not text:
            return []
        tokens = re.findall(r'\b\w+\b', str(text).lower())
        return tokens
    
    def extract_entities(self, text):
        """Extract named entities from text."""
        entities = []
        # Capitalized multi-word phrases
        proper_nouns = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', text)
        entities.extend(proper_nouns)
        # Single capitalized words
        single_proper = re.findall(r'(?<=\s)([A-Z][a-z]+)\b', text)
        entities.extend([w for w in single_proper if w.lower() not in self.stopwords])
        # Numbers
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)
        entities.extend(numbers)
        # Years
        years = re.findall(r'\b(20\d{2})\b', text)
        entities.extend(years)
        return list(set(entities))
    
    def generate_ngrams(self, tokens, n_range=(1, 4)):
        """Generate n-grams from tokens."""
        ngrams = []
        for n in range(n_range[0], n_range[1] + 1):
            for i in range(len(tokens) - n + 1):
                ngram = ' '.join(tokens[i:i+n])
                ngrams.append(ngram)
        return ngrams
    
    def extract_keywords(self, text, top_n=10):
        """Extract important keywords using TF-IDF scoring."""
        tokens = self.tokenize(text)
        content_words = [t for t in tokens if t not in self.stopwords and len(t) > 1]
        word_scores = {}
        total_docs = max(len(self.sentence_bank), 1)
        
        for word in set(content_words):
            tf = content_words.count(word) / max(len(content_words), 1)
            doc_count = sum(1 for s in self.sentence_bank if word in s.lower())
            idf = math.log(total_docs / max(doc_count, 1))
            word_scores[word] = tf * idf
        
        sorted_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        return [word for word, score in sorted_words[:top_n]]
    
    def extract_question_focus(self, question):
        """Extract the core focus of a question."""
        q = question.lower().strip()
        focus = re.sub(r'^(who|what|when|where|why|how|which|is|are|do|does|did|can|could|will|would|shall|should)\s+', '', q)
        focus = focus.rstrip('?')
        entities = self.extract_entities(question)
        keywords = self.extract_keywords(focus, top_n=5)
        return focus, entities, keywords
    
    # ========== KNOWLEDGE INDEXING ==========
    
    def build_indexes(self):
        """Build powerful search indexes from all knowledge sources."""
        print("Building knowledge indexes...")
        
        all_sentences = []
        
        # From JSON knowledge base
        for module in self.knowledge_base:
            for response in module.get("responses", []):
                sentences = re.split(r'(?<=[.!?])\s+', response)
                all_sentences.extend([s.strip() for s in sentences if len(s) > 5])
        
        # From GK base
        for fact in self.gk_base:
            q = fact.get("q", "")
            a = fact.get("a", "")
            if q:
                all_sentences.append(q)
                self.entity_index[q.lower()].append(a)
            if a:
                sentences = re.split(r'(?<=[.!?])\s+', a)
                all_sentences.extend([s.strip() for s in sentences if len(s) > 5])
        
        # From raw text files
        for sentence in self.raw_data_chunks:
            if len(sentence) > 10:
                all_sentences.append(sentence)
        
        # From learned facts
        for question, answer in self.learned_facts.items():
            all_sentences.append(question)
            all_sentences.append(answer)
        
        self.sentence_bank = list(set(all_sentences))
        
        # Build entity index
        for sentence in self.sentence_bank:
            entities = self.extract_entities(sentence)
            for entity in entities:
                self.entity_index[entity.lower()].append(sentence)
        
        # Build n-gram index
        for sentence in self.sentence_bank:
            tokens = self.tokenize(sentence)
            ngrams = self.generate_ngrams(tokens, n_range=(2, 5))
            for ngram in ngrams:
                self.ngram_index[ngram].append(sentence)
        
        # Build word frequency
        for sentence in self.sentence_bank:
            tokens = self.tokenize(sentence)
            self.word_freq.update(tokens)
        
        self._build_entity_map()
        
        print(f"✓ Indexed {len(self.sentence_bank)} sentences")
        print(f"✓ Indexed {len(self.entity_index)} entities")
        print(f"✓ Indexed {len(self.ngram_index)} n-grams")
    
    def _build_entity_map(self):
        """Map entity variations to canonical forms."""
        for entity in self.entity_index:
            normalized = re.sub(r'[^\w\s]', '', entity.lower()).strip()
            if normalized not in self.entity_map:
                self.entity_map[normalized] = entity
            words = normalized.split()
            if len(words) > 1:
                for i in range(len(words)):
                    partial = ' '.join(words[i:])
                    if len(partial) > 3:
                        if partial not in self.entity_map:
                            self.entity_map[partial] = entity
    
    # ========== INTELLIGENT SEARCH ==========
    
    def calculate_similarity(self, text1, text2):
        """Calculate semantic similarity between two texts."""
        tokens1 = set(self.tokenize(text1))
        tokens2 = set(self.tokenize(text2))
        if not tokens1 or not tokens2:
            return 0
        
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        jaccard = intersection / union if union > 0 else 0
        
        entities1 = set(e.lower() for e in self.extract_entities(text1))
        entities2 = set(e.lower() for e in self.extract_entities(text2))
        entity_overlap = len(entities1.intersection(entities2)) / max(len(entities1.union(entities2)), 1)
        
        return jaccard * 0.6 + entity_overlap * 0.4
    
    def search_knowledge(self, question, top_k=5):
        """Multi-strategy search for the most relevant knowledge."""
        focus, entities, keywords = self.extract_question_focus(question)
        results = []
        
        # Strategy 1: Exact entity match
        for entity in entities:
            entity_lower = entity.lower()
            if entity_lower in self.entity_index:
                for sentence in self.entity_index[entity_lower]:
                    score = self.calculate_similarity(question, sentence)
                    results.append((score, sentence, "entity_match"))
        
        # Strategy 2: N-gram matching
        tokens = self.tokenize(focus)
        ngrams = self.generate_ngrams(tokens, n_range=(2, 4))
        for ngram in ngrams:
            if ngram in self.ngram_index:
                for sentence in self.ngram_index[ngram]:
                    score = self.calculate_similarity(question, sentence)
                    score += 0.1
                    results.append((score, sentence, "ngram_match"))
        
        # Strategy 3: Keyword matching
        for sentence in self.sentence_bank:
            keyword_matches = sum(1 for kw in keywords if kw in sentence.lower())
            if keyword_matches >= 2:
                score = keyword_matches / max(len(keywords), 1)
                score += self.calculate_similarity(question, sentence)
                results.append((score, sentence, "keyword_match"))
        
        # Strategy 4: Learned facts exact match
        for learned_q, learned_a in self.learned_facts.items():
            if self.calculate_similarity(question, learned_q) > 0.5:
                results.append((0.9, learned_a, "learned_fact"))
        
        # Remove duplicates and sort by score
        seen = set()
        unique_results = []
        for score, sentence, source in sorted(results, key=lambda x: x[0], reverse=True):
            normalized = sentence.lower().strip()
            if normalized not in seen:
                seen.add(normalized)
                unique_results.append((score, sentence, source))
        
        return unique_results[:top_k]
    
    # ========== ANSWER GENERATION ==========
    
    def detect_question_type(self, question):
        """Detect what type of answer is needed."""
        q = question.lower().strip()
        if q.startswith("who"):
            return "person"
        if q.startswith("which nation") or q.startswith("which country"):
            return "country"
        if q.startswith("which club") or q.startswith("which team"):
            return "club"
        if q.startswith("what is") or q.startswith("define"):
            return "definition"
        if q.startswith("when"):
            return "date"
        if q.startswith("where"):
            return "place"
        if q.startswith("why"):
            return "reason"
        if q.startswith("how"):
            return "method"
        if q.startswith("which"):
            return "choice"
        return "general"
    
    def extract_exact_answer(self, question, sentences):
        """Extract a precise, short answer from relevant sentences."""
        q_type = self.detect_question_type(question)
        combined = " ".join([s[1] for s in sentences[:3]])
        
        if q_type == "person":
            patterns = [
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s+(?:won|claimed|secured|became|crowned|named|selected|elected|is|was)',
                r'(?:won by|awarded to|champion[:\s]+|winner[:\s]+)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s+(?:is|was|became)\s+(?:the\s+)?(?:champion|winner|victor|first|youngest|oldest)',
            ]
            for pattern in patterns:
                match = re.search(pattern, combined)
                if match:
                    return match.group(1).strip()
        
        if q_type in ("club", "team"):
            patterns = [
                r'([A-Z][a-zA-Z]+(?:\s+(?:United|City|Town|Rovers|Rangers|Athletic|Albion|Villa|Forest|Palace|Hotspur|Wednesday|County|Wanderers|Alexandra|Stanley|Orient|Argyle|FC|Football Club|AFC)))\s+(?:won|defeated|beat|claimed|secured|lifted)',
                r'(?:defeated|beat)\s+([A-Z][a-zA-Z]+(?:\s+(?:United|City|Town|FC))?)',
                r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})\s+(?:won|claimed|secured|lifted|took)\s+the\s+(?:FA Cup|trophy|title|championship)',
            ]
            for pattern in patterns:
                match = re.search(pattern, combined)
                if match:
                    return match.group(1).strip()
        
        if q_type == "country":
            country_names = [
                "India", "Australia", "England", "South Africa", "New Zealand", "Pakistan",
                "Sri Lanka", "Bangladesh", "Afghanistan", "West Indies", "Zimbabwe", "Ireland",
                "United States", "China", "Russia", "Brazil", "Argentina", "Germany", "France",
                "Spain", "Italy", "Japan", "South Korea", "Canada", "Mexico"
            ]
            for country in country_names:
                if country.lower() in combined.lower():
                    return country
        
        if q_type == "date":
            match = re.search(r'(?:\d{1,2}\s+)?(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}', combined)
            if match:
                return match.group(0)
            match = re.search(r'\b(20\d{2})\b', combined)
            if match:
                return match.group(0)
        
        # Return the most relevant sentence
        if sentences:
            best = sentences[0][1]
            if len(best) > 300:
                best = best[:300].rsplit(' ', 1)[0] + "..."
            return best
        
        return None
    
    def generate_answer(self, question):
        """Generate a comprehensive answer from knowledge base."""
        results = self.search_knowledge(question, top_k=5)
        
        if not results:
            return None
        
        # Try to extract a precise answer
        exact = self.extract_exact_answer(question, results)
        if exact and len(exact) < 200:
            return exact
        
        # Combine relevant sentences
        answer_parts = []
        seen = set()
        for score, sentence, source in results[:3]:
            normalized = sentence.lower().strip()
            if normalized not in seen and len(sentence) > 10:
                seen.add(normalized)
                answer_parts.append(sentence)
        
        if answer_parts:
            return " ".join(answer_parts)
        
        return None
    
    # ========== LEARNING SYSTEM ==========
    
    def learn_fact(self, question, answer):
        """Learn a new fact and index it."""
        self.learned_facts[question] = answer
        
        if question not in self.sentence_bank:
            self.sentence_bank.append(question)
        if answer not in self.sentence_bank:
            self.sentence_bank.append(answer)
        
        for sentence in [question, answer]:
            entities = self.extract_entities(sentence)
            for entity in entities:
                self.entity_index[entity.lower()].append(sentence)
            tokens = self.tokenize(sentence)
            ngrams = self.generate_ngrams(tokens, n_range=(2, 5))
            for ngram in ngrams:
                self.ngram_index[ngram].append(sentence)
            self.word_freq.update(tokens)
        
        self.save_learned_facts()
        return True
    
    def learn_from_statement(self, text):
        """Learn from declarative statements."""
        if not text or len(text.split()) < 5:
            return False
        
        factual_patterns = [" is ", " was ", " are ", " were ", " has ", " have ", " will ", " can ", " does "]
        if any(pattern in text.lower() for pattern in factual_patterns):
            if text not in self.sentence_bank:
                self.sentence_bank.append(text)
                entities = self.extract_entities(text)
                for entity in entities:
                    self.entity_index[entity.lower()].append(text)
                tokens = self.tokenize(text)
                ngrams = self.generate_ngrams(tokens, n_range=(2, 5))
                for ngram in ngrams:
                    self.ngram_index[ngram].append(text)
                self.word_freq.update(tokens)
                
                try:
                    with open(self.user_mem_file, 'a', encoding='utf-8') as f:
                        f.write(text.strip() + "\n")
                except:
                    pass
                return True
        return False
    
    def save_learned_facts(self):
        """Save learned facts to disk."""
        try:
            with open(self.learned_file, 'w', encoding='utf-8') as f:
                json.dump(self.learned_facts, f, indent=2)
        except:
            pass
    
    # ========== DATA LOADING ==========
    
    def load_all_data(self):
        """Load all knowledge sources."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.knowledge_base = json.load(f)
            else:
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                self.knowledge_base = []
        except:
            self.knowledge_base = []
        
        try:
            if os.path.exists(self.gk_file):
                with open(self.gk_file, 'r', encoding='utf-8') as f:
                    self.gk_base = json.load(f)
            else:
                with open(self.gk_file, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                self.gk_base = []
        except:
            self.gk_base = []
        
        try:
            if os.path.exists(self.learned_file):
                with open(self.learned_file, 'r', encoding='utf-8') as f:
                    self.learned_facts = json.load(f)
        except:
            self.learned_facts = {}
        
        self.raw_data_chunks = []
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
        
        print(f"✓ Loaded {len(self.knowledge_base)} knowledge modules")
        print(f"✓ Loaded {len(self.gk_base)} GK facts")
        print(f"✓ Loaded {len(self.learned_facts)} learned facts")
        print(f"✓ Loaded {len(self.raw_data_chunks)} text sentences")
    
    # ========== RESPONSE HANDLER ==========
    
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
    
    def get_response(self, user_input):
        if not user_input or not user_input.strip():
            return "Please ask me something! 😊"
        
        raw = user_input.strip()
        low = raw.lower()
        
        # Greetings
        if self.is_greeting(raw):
            return self.get_greeting_response()
        
        # Learning commands
        if low.startswith("learn "):
            content = raw[6:].strip()
            if " : " in content or " = " in content or " -> " in content:
                separator = " : " if " : " in content else (" = " if " = " in content else " -> ")
                parts = content.split(separator, 1)
                if len(parts) == 2:
                    question, answer = parts[0].strip(), parts[1].strip()
                    self.learn_fact(question, answer)
                    return f"✅ Learned: '{question}' → '{answer}'"
            
            if self.learn_from_statement(content):
                return f"✅ Learned from: '{content[:100]}...'"
            return "Please use format: learn question : answer"
        
        # Reload command
        if low == "reload knowledge":
            self.load_all_data()
            self.build_indexes()
            return "✅ Knowledge base reloaded and re-indexed!"
        
        # Status command
        if low == "status":
            return f"📊 Knowledge Base Status:\n• Modules: {len(self.knowledge_base)}\n• GK Facts: {len(self.gk_base)}\n• Learned Facts: {len(self.learned_facts)}\n• Sentences: {len(self.sentence_bank)}\n• Entities: {len(self.entity_index)}\n• N-grams: {len(self.ngram_index)}"
        
        # Try to answer from knowledge
        answer = self.generate_answer(raw)
        if answer:
            if "?" not in raw:
                self.learn_from_statement(raw)
            return self.grammar_checker(answer)
        
        if "?" not in raw:
            self.learn_from_statement(raw)
            return "I've noted that. Feel free to ask me questions or teach me with 'learn question : answer'."
        
        return "I don't have enough knowledge to answer that yet. You can teach me using: learn your question : the answer"


# ========== WEB SERVER ==========
class ChatHandler(BaseHTTPRequestHandler):
    bot = None

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Read the HTML file
            html_path = os.path.join(os.path.dirname(__file__), 'index.html')
            try:
                with open(html_path, 'r', encoding='utf-8') as f:
                    html = f.read()
                self.wfile.write(html.encode())
            except FileNotFoundError:
                self.wfile.write(b"Error: index.html not found")
                
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
    
    print(f"""
╔══════════════════════════════════════════╗
║       🧠 KeyGen.ai ONLINE               ║
║   http://0.0.0.0:{port}                  ║
║   Pure Knowledge Engine                 ║
║   No external web - All local           ║
╚══════════════════════════════════════════╝
    """)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()

if __name__ == "__main__":
    run_server()
