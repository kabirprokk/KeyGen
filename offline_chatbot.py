import re
import random
import json
import os
import hashlib
import time
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
        self.knowledge_base = []          # JSON modules
        self.gk_base = []                 # General knowledge facts
        self.learned_facts = {}           # Dynamically learned facts
        self.sentence_bank = []           # All sentences from all sources
        self.entity_index = defaultdict(list)  # Entity -> sentences mapping
        self.ngram_index = defaultdict(list)   # N-gram -> sentences mapping
        self.word_freq = Counter()        # Word frequency for importance scoring
        self.entity_map = {}              # Entity variations -> canonical form
        
        # Enhanced tokenization
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
        # Extract words, numbers, and special tokens
        tokens = re.findall(r'\b\w+\b', str(text).lower())
        return tokens
    
    def extract_entities(self, text):
        """Extract named entities (proper nouns, numbers, dates) from text."""
        entities = []
        # Capitalized multi-word phrases (proper nouns)
        proper_nouns = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', text)
        entities.extend(proper_nouns)
        # Single capitalized words (not at start of sentence)
        single_proper = re.findall(r'(?<=\s)([A-Z][a-z]+)\b', text)
        entities.extend([w for w in single_proper if w.lower() not in self.stopwords])
        # Numbers and dates
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)
        entities.extend(numbers)
        # Years
        years = re.findall(r'\b(20\d{2})\b', text)
        entities.extend(years)
        return list(set(entities))
    
    def generate_ngrams(self, tokens, n_range=(1, 4)):
        """Generate n-grams from tokens for flexible matching."""
        ngrams = []
        for n in range(n_range[0], n_range[1] + 1):
            for i in range(len(tokens) - n + 1):
                ngram = ' '.join(tokens[i:i+n])
                ngrams.append(ngram)
        return ngrams
    
    def extract_keywords(self, text, top_n=10):
        """Extract the most important keywords using TF-IDF-like scoring."""
        tokens = self.tokenize(text)
        # Remove stopwords
        content_words = [t for t in tokens if t not in self.stopwords and len(t) > 1]
        # Score by frequency and length
        word_scores = {}
        total_docs = max(len(self.sentence_bank), 1)
        for word in set(content_words):
            tf = content_words.count(word) / max(len(content_words), 1)
            doc_count = sum(1 for s in self.sentence_bank if word in s.lower())
            idf = __import__('math').log(total_docs / max(doc_count, 1))
            word_scores[word] = tf * idf
        # Sort and return top keywords
        sorted_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        return [word for word, score in sorted_words[:top_n]]
    
    def extract_question_focus(self, question):
        """Extract the core focus of a question."""
        q = question.lower().strip()
        # Remove question words
        focus = re.sub(r'^(who|what|when|where|why|how|which|is|are|do|does|did|can|could|will|would|shall|should)\s+', '', q)
        # Remove question mark
        focus = focus.rstrip('?')
        # Extract key entities and keywords
        entities = self.extract_entities(question)
        keywords = self.extract_keywords(focus, top_n=5)
        return focus, entities, keywords
    
    # ========== KNOWLEDGE INDEXING ==========
    
    def build_indexes(self):
        """Build powerful search indexes from all knowledge sources."""
        print("Building knowledge indexes...")
        
        # Collect all sentences
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
        
        # Build entity map (variations -> canonical)
        self._build_entity_map()
        
        print(f"✓ Indexed {len(self.sentence_bank)} sentences")
        print(f"✓ Indexed {len(self.entity_index)} entities")
        print(f"✓ Indexed {len(self.ngram_index)} n-grams")
    
    def _build_entity_map(self):
        """Map entity variations to canonical forms."""
        # Group similar entities
        for entity in self.entity_index:
            # Normalize: lowercase, remove punctuation
            normalized = re.sub(r'[^\w\s]', '', entity.lower()).strip()
            if normalized not in self.entity_map:
                self.entity_map[normalized] = entity
            # Also map partial matches
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
        # Jaccard similarity
        jaccard = intersection / union if union > 0 else 0
        # Bonus for shared entities
        entities1 = set(e.lower() for e in self.extract_entities(text1))
        entities2 = set(e.lower() for e in self.extract_entities(text2))
        entity_overlap = len(entities1.intersection(entities2)) / max(len(entities1.union(entities2)), 1)
        # Combined score
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
                    score += 0.1  # Bonus for n-gram match
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
            # Look for person names near winning/achievement words
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
        # Search for relevant knowledge
        results = self.search_knowledge(question, top_k=5)
        
        if not results:
            return None
        
        # Try to extract a precise answer
        exact = self.extract_exact_answer(question, results)
        if exact and len(exact) < 200:
            return exact
        
        # Combine relevant sentences into a coherent answer
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
        
        # Add to sentence bank
        if question not in self.sentence_bank:
            self.sentence_bank.append(question)
        if answer not in self.sentence_bank:
            self.sentence_bank.append(answer)
        
        # Index the new fact
        for sentence in [question, answer]:
            entities = self.extract_entities(sentence)
            for entity in entities:
                self.entity_index[entity.lower()].append(sentence)
            tokens = self.tokenize(sentence)
            ngrams = self.generate_ngrams(tokens, n_range=(2, 5))
            for ngram in ngrams:
                self.ngram_index[ngram].append(sentence)
            self.word_freq.update(tokens)
        
        # Save learned facts
        self.save_learned_facts()
        
        return True
    
    def learn_from_statement(self, text):
        """Learn from declarative statements."""
        if not text or len(text.split()) < 5:
            return False
        
        # Check if it's a factual statement
        factual_patterns = [" is ", " was ", " are ", " were ", " has ", " have ", " will ", " can ", " does "]
        if any(pattern in text.lower() for pattern in factual_patterns):
            # Add to sentence bank
            if text not in self.sentence_bank:
                self.sentence_bank.append(text)
                # Index it
                entities = self.extract_entities(text)
                for entity in entities:
                    self.entity_index[entity.lower()].append(text)
                tokens = self.tokenize(text)
                ngrams = self.generate_ngrams(tokens, n_range=(2, 5))
                for ngram in ngrams:
                    self.ngram_index[ngram].append(text)
                self.word_freq.update(tokens)
                
                # Save to file
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
        # Load JSON knowledge base
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
        
        # Load GK facts
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
        
        # Load learned facts
        try:
            if os.path.exists(self.learned_file):
                with open(self.learned_file, 'r', encoding='utf-8') as f:
                    self.learned_facts = json.load(f)
        except:
            self.learned_facts = {}
        
        # Load raw text files
        self.raw_data_chunks = []
        if os.path.exists(self.knowledge_dir):
            for filename in os.listdir(self.knowledge_dir):
                if filename.endswith(".txt"):
                    filepath = os.path.join(self.knowledge_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            text = f.read()
                            if text.strip():
                                # Split into sentences
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
            # Check if it's a Q&A format
            if " : " in content or " = " in content or " -> " in content:
                separator = " : " if " : " in content else (" = " if " = " in content else " -> ")
                parts = content.split(separator, 1)
                if len(parts) == 2:
                    question, answer = parts[0].strip(), parts[1].strip()
                    self.learn_fact(question, answer)
                    return f"✅ Learned: '{question}' → '{answer}'"
            
            # Learn from statement
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
            # Learn from statements (non-questions)
            if "?" not in raw:
                self.learn_from_statement(raw)
            return self.grammar_checker(answer)
        
        # Learn from statement if not a question
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
            html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KeyGen.ai - Knowledge Engine</title>
    <style>
        :root { --bg: #000; --surface: #0a0a0a; --surface2: #111; --border: #1a1a1a; --text: #fff; --text-secondary: #888; --glow: #fff; --accent: #6C63FF; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 16px; }
        .container { background: var(--surface); border-radius: 20px; max-width: 800px; width: 100%; overflow: hidden; border: 1px solid var(--border); box-shadow: 0 0 30px rgba(108,99,255,0.05); }
        .header { padding: 20px 24px; display: flex; align-items: center; gap: 14px; border-bottom: 1px solid var(--border); background: var(--surface2); }
        .header-icon { width: 42px; height: 42px; background: var(--bg); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; border: 1px solid var(--border); }
        .header-text h1 { color: var(--text); font-size: 18px; font-weight: 600; }
        .header-text p { color: var(--text-secondary); font-size: 12px; }
        .status-dot { width: 6px; height: 6px; background: #4CAF50; border-radius: 50%; display: inline-block; margin-right: 6px; box-shadow: 0 0 8px #4CAF50; animation: glow 2s infinite; }
        @keyframes glow { 0%, 100% { box-shadow: 0 0 8px #4CAF50; } 50% { box-shadow: 0 0 16px #4CAF50; } }
        #chat-container { height: 450px; overflow-y: auto; padding: 20px; background: var(--surface); scroll-behavior: smooth; }
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
        #input:focus { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(108,99,255,0.1); } #input::placeholder { color: #444; }
        .btn { height: 42px; border: 1px solid var(--border); border-radius: 12px; color: var(--text); font-size: 14px; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; justify-content: center; flex-shrink: 0; background: var(--surface); }
        .send-btn { width: 42px; font-size: 18px; } .send-btn:hover { background: var(--accent); color: white; border-color: var(--accent); }
        .stop-btn { width: 42px; font-size: 16px; display: none; } .stop-btn:hover { background: #ff3333; border-color: #ff3333; color: white; } .stop-btn.active { display: flex; } .send-btn.hidden { display: none; }
        .suggestions { display: flex; gap: 8px; padding: 12px 20px; flex-wrap: wrap; background: var(--surface); }
        .suggestion-chip { padding: 7px 14px; background: var(--surface2); border: 1px solid var(--border); border-radius: 20px; color: var(--text-secondary); font-size: 12px; cursor: pointer; transition: all 0.2s; white-space: nowrap; }
        .suggestion-chip:hover { background: var(--accent); color: white; border-color: var(--accent); }
        .timestamp { font-size: 10px; color: #444; margin-top: 4px; padding: 0 8px; }
        @media (max-width: 600px) { body { padding: 0; } .container { border-radius: 0; height: 100vh; display: flex; flex-direction: column; } #chat-container { flex: 1; height: auto; } .message { max-width: 85%; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-icon">🧠</div>
            <div class="header-text">
                <h1>KeyGen.ai</h1>
                <p><span class="status-dot"></span>Knowledge Engine</p>
            </div>
        </div>
        <div id="chat-container">
            <div class="message-wrapper ai">
                <div class="message-avatar">🧠</div>
                <div>
                    <div class="message">Hello! 👋 I'm KeyGen.ai, a pure knowledge engine. I learn from everything you feed me. Ask me anything or teach me with: <b>learn question : answer</b></div>
                    <div class="timestamp">Just now</div>
                </div>
            </div>
        </div>
        <div class="suggestions">
            <span class="suggestion-chip" onclick="useSuggestion(this)">What is artificial intelligence?</span>
            <span class="suggestion-chip" onclick="useSuggestion(this)">Who won the World Cup 2022?</span>
            <span class="suggestion-chip" onclick="useSuggestion(this)">status</span>
            <span class="suggestion-chip" onclick="useSuggestion(this)">reload knowledge</span>
        </div>
        <div class="input-container">
            <input type="text" id="input" placeholder="Ask or teach me something..." autofocus>
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
            const avatar = document.createElement('div'); avatar.className = 'message-avatar'; avatar.textContent = isUser ? '👤' : '🧠';
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
            const avatar = document.createElement('div'); avatar.className = 'message-avatar'; avatar.textContent = '🧠';
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
        async function typeWriterEffect(element, text, speed = 10) {
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
                if (isGenerating) { const aiMessage = addMessage('', false); await typeWriterEffect(aiMessage, data.response, 10); }
            } catch (error) { if (error.name !== 'AbortError') { removeTypingIndicator(); addMessage('⚠️ Connection error. Try again.', false); } }
            setGeneratingState(false); abortController = null;
        }
        function useSuggestion(chip) { input.value = chip.textContent; sendMessage(); }
        input.addEventListener('keypress', function(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });
        input.focus();
    </script>
</body>
</html>'''
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
