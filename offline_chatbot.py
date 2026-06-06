import re
import random
import json
import os
import hashlib
import time
import math
import threading
from collections import defaultdict, Counter, OrderedDict
from http.server import HTTPServer, BaseHTTPRequestHandler
from difflib import SequenceMatcher
from itertools import combinations

class AdvancedTokenizer:
    """Multi-strategy tokenization engine with linguistic understanding."""
    
    def __init__(self):
        self.cache = {}
        
    def tokenize(self, text, method="hybrid"):
        """Tokenize using multiple strategies."""
        if not text:
            return []
        
        cache_key = hash(text + method)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        if method == "hybrid":
            tokens = self._hybrid_tokenize(text)
        elif method == "linguistic":
            tokens = self._linguistic_tokenize(text)
        elif method == "semantic":
            tokens = self._semantic_tokenize(text)
        else:
            tokens = self._basic_tokenize(text)
        
        self.cache[cache_key] = tokens
        return tokens
    
    def _basic_tokenize(self, text):
        """Basic word extraction."""
        return re.findall(r'\b\w+\b', str(text).lower())
    
    def _hybrid_tokenize(self, text):
        """Hybrid tokenization combining multiple approaches."""
        text = str(text).lower()
        
        # Extract multi-word expressions
        multi_word = re.findall(r'\b\w+(?:\s+\w+){1,3}\b', text)
        
        # Extract single words
        single_words = re.findall(r'\b\w+\b', text)
        
        # Extract numbers and units
        numbers = re.findall(r'\b\d+(?:\.\d+)?\s*(?:%|kg|km|m|cm|mm|°C|°F|mph|kWh|GB|MB|TB)?\b', text)
        
        # Extract dates
        dates = re.findall(r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b', text)
        
        # Combine all tokens
        all_tokens = multi_word + single_words + numbers + dates
        
        return list(set(all_tokens))
    
    def _linguistic_tokenize(self, text):
        """Linguistic tokenization with stemming and lemmatization."""
        tokens = self._basic_tokenize(text)
        
        # Simple stemming (remove common suffixes)
        stemmed = []
        for token in tokens:
            # Remove common suffixes
            for suffix in ['ing', 'tion', 'ment', 'ness', 'ity', 'able', 'ible', 'ful', 'less', 'ous', 'ive', 'al', 'er', 'est']:
                if token.endswith(suffix) and len(token) > len(suffix) + 2:
                    token = token[:-len(suffix)]
                    break
            stemmed.append(token)
        
        return list(set(stemmed + tokens))
    
    def _semantic_tokenize(self, text):
        """Semantic tokenization with entity recognition."""
        tokens = self._basic_tokenize(text)
        
        # Extract proper nouns (capitalized sequences)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Extract acronyms
        acronyms = re.findall(r'\b[A-Z]{2,}\b', text)
        
        # Extract quoted phrases
        quoted = re.findall(r'"([^"]*)"', text)
        quoted += re.findall(r"'([^']*)'", text)
        
        all_tokens = tokens + proper_nouns + acronyms + quoted
        return list(set(all_tokens))
    
    def ngrams(self, tokens, n=2):
        """Generate n-grams."""
        return [' '.join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]
    
    def skipgrams(self, tokens, n=2, k=1):
        """Generate skip-grams for flexible matching."""
        skipgrams = []
        for i in range(len(tokens) - n + 1):
            for j in range(1, k + 1):
                if i + n + j <= len(tokens):
                    skipgram = tokens[i:i+n-1] + [tokens[i+n+j-1]]
                    skipgrams.append(' '.join(skipgram))
        return skipgrams


class SemanticVectorizer:
    """Creates semantic vectors for text understanding."""
    
    def __init__(self):
        self.word_vectors = {}
        self.document_vectors = {}
        
    def build_cooccurrence_matrix(self, sentences, window_size=5):
        """Build word co-occurrence matrix."""
        cooccurrence = defaultdict(Counter)
        
        for sentence in sentences:
            tokens = re.findall(r'\b\w+\b', sentence.lower())
            for i, word in enumerate(tokens):
                start = max(0, i - window_size)
                end = min(len(tokens), i + window_size + 1)
                for j in range(start, end):
                    if i != j:
                        cooccurrence[word][tokens[j]] += 1
        
        return cooccurrence
    
    def build_word_vector(self, word, cooccurrence, dimensions=100):
        """Create a vector representation for a word."""
        if word not in cooccurrence:
            return [0] * dimensions
        
        # Get top co-occurring words
        related = cooccurrence[word].most_common(dimensions)
        
        # Create vector
        vector = [0] * dimensions
        for i, (_, count) in enumerate(related[:dimensions]):
            vector[i] = math.log(count + 1)
        
        # Normalize
        magnitude = math.sqrt(sum(v**2 for v in vector))
        if magnitude > 0:
            vector = [v / magnitude for v in vector]
        
        return vector
    
    def cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between vectors."""
        if not vec1 or not vec2:
            return 0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(a**2 for a in vec1))
        mag2 = math.sqrt(sum(b**2 for b in vec2))
        
        if mag1 == 0 or mag2 == 0:
            return 0
        
        return dot_product / (mag1 * mag2)


class KnowledgeGraph:
    """Knowledge graph for relationship-based reasoning."""
    
    def __init__(self):
        self.nodes = defaultdict(dict)
        self.edges = defaultdict(list)
        self.relations = defaultdict(set)
        
    def add_fact(self, subject, predicate, obj):
        """Add a fact triple to the graph."""
        self.nodes[subject][predicate] = obj
        self.edges[subject].append((predicate, obj))
        self.edges[obj].append((f"inverse_{predicate}", subject))
        self.relations[predicate].add((subject, obj))
    
    def query(self, subject=None, predicate=None, obj=None):
        """Query the knowledge graph."""
        results = []
        
        if subject and predicate:
            if subject in self.nodes and predicate in self.nodes[subject]:
                results.append(self.nodes[subject][predicate])
        
        elif subject and not predicate:
            if subject in self.nodes:
                results.extend(self.nodes[subject].items())
        
        elif predicate and obj:
            for sub, ob in self.relations.get(predicate, set()):
                if ob == obj:
                    results.append(sub)
        
        return results
    
    def find_path(self, start, end, max_depth=3):
        """Find relationship path between two nodes."""
        if start == end:
            return [start]
        
        visited = {start}
        queue = [(start, [start])]
        
        while queue:
            node, path = queue.pop(0)
            if len(path) > max_depth:
                continue
            
            for predicate, neighbor in self.edges.get(node, []):
                if neighbor == end:
                    return path + [predicate, neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [predicate, neighbor]))
        
        return None


class PredictiveEngine:
    """Advanced prediction and reasoning engine."""
    
    def __init__(self):
        self.patterns = defaultdict(list)
        self.sequences = defaultdict(Counter)
        self.predictions = {}
        
    def learn_pattern(self, context, result):
        """Learn a pattern for prediction."""
        self.patterns[context].append(result)
        self.predictions[context] = Counter(self.patterns[context]).most_common(1)[0][0]
    
    def learn_sequence(self, sequence):
        """Learn sequential patterns."""
        for i in range(len(sequence) - 1):
            self.sequences[sequence[i]][sequence[i+1]] += 1
    
    def predict_next(self, current, top_n=3):
        """Predict the next item in a sequence."""
        if current in self.sequences:
            return self.sequences[current].most_common(top_n)
        return []
    
    def predict_answer(self, question_context):
        """Predict answer based on learned patterns."""
        best_match = None
        best_score = 0
        
        for context, result in self.predictions.items():
            similarity = SequenceMatcher(None, question_context, context).ratio()
            if similarity > best_score:
                best_score = similarity
                best_match = result
        
        return best_match if best_score > 0.4 else None


class KeyGenAI:
    """Ultimate offline AI with advanced tokenization and prediction."""
    
    def __init__(self, knowledge_dir="knowledge", data_file="data.json", gk_file="gk_knowledge.json"):
        self.name = "KeyGen.ai"
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.knowledge_dir = os.path.join(self.script_dir, knowledge_dir)
        self.collected_dir = os.path.join(self.knowledge_dir, "collected")
        self.data_file = os.path.join(self.script_dir, data_file)
        self.gk_file = os.path.join(self.script_dir, gk_file)
        self.user_mem_file = os.path.join(self.knowledge_dir, "user_mem.txt")
        self.learned_file = os.path.join(self.knowledge_dir, "learned_knowledge.json")
        
        # Advanced engines
        self.tokenizer = AdvancedTokenizer()
        self.vectorizer = SemanticVectorizer()
        self.knowledge_graph = KnowledgeGraph()
        self.predictor = PredictiveEngine()
        
        # Core storage
        self.knowledge_base = []
        self.gk_base = []
        self.learned_facts = {}
        self.raw_data_chunks = []
        self.sentence_bank = []
        
        # Advanced indexes
        self.inverted_index = defaultdict(set)
        self.ngram_index = defaultdict(list)
        self.semantic_index = defaultdict(list)
        self.cooccurrence_matrix = None
        self.document_vectors = {}
        self.word_vectors = {}
        
        # Statistics
        self.word_freq = Counter()
        self.doc_freq = Counter()
        self.total_docs = 0
        
        # Question patterns
        self.question_patterns = {
            "what is": self._answer_definition,
            "who is": self._answer_person,
            "who was": self._answer_person,
            "when did": self._answer_time,
            "when was": self._answer_time,
            "where is": self._answer_location,
            "where was": self._answer_location,
            "why is": self._answer_reason,
            "why did": self._answer_reason,
            "how does": self._answer_method,
            "how is": self._answer_method,
            "how many": self._answer_quantity,
            "how much": self._answer_quantity,
            "which is": self._answer_choice,
            "define": self._answer_definition,
            "explain": self._answer_definition,
            "describe": self._answer_definition,
        }
        
        # Stopwords
        self.stopwords = {
            "a", "an", "the", "and", "or", "but", "is", "are", "was", "were",
            "to", "at", "by", "for", "of", "with", "in", "on", "that", "this",
            "it", "its", "be", "been", "being", "have", "has", "had", "do", "does",
            "did", "will", "would", "could", "should", "may", "might", "can", "shall",
            "i", "you", "he", "she", "we", "they", "me", "him", "her", "us", "them",
            "my", "your", "his", "our", "their", "mine", "yours", "hers", "ours", "theirs"
        }
        
        # Greetings
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
        os.makedirs(self.collected_dir, exist_ok=True)
        self.load_all_data()
        self.build_all_indexes()
    
    # ========== DATA LOADING ==========
    
    def load_all_data(self):
        """Load all knowledge sources."""
        # Load JSON modules
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.knowledge_base = json.load(f)
            else:
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump([], f)
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
        except:
            self.gk_base = []
        
        # Load learned facts
        try:
            if os.path.exists(self.learned_file):
                with open(self.learned_file, 'r', encoding='utf-8') as f:
                    self.learned_facts = json.load(f)
        except:
            self.learned_facts = {}
        
        # Load text files
        self.raw_data_chunks = []
        for directory in [self.knowledge_dir, self.collected_dir]:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    if filename.endswith(".txt"):
                        filepath = os.path.join(directory, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                text = f.read()
                                if text.strip():
                                    sentences = re.split(r'(?<=[.!?])\s+', text)
                                    self.raw_data_chunks.extend([s.strip() for s in sentences if len(s) > 10])
                        except:
                            pass
        
        print(f"✓ Loaded {len(self.knowledge_base)} modules")
        print(f"✓ Loaded {len(self.gk_base)} GK facts")
        print(f"✓ Loaded {len(self.learned_facts)} learned facts")
        print(f"✓ Loaded {len(self.raw_data_chunks)} text sentences")
    
    # ========== INDEX BUILDING ==========
    
    def build_all_indexes(self):
        """Build all search indexes."""
        print("\n🔧 Building advanced indexes...")
        
        # Collect all sentences
        self.sentence_bank = []
        
        for module in self.knowledge_base:
            for response in module.get("responses", []):
                sentences = re.split(r'(?<=[.!?])\s+', response)
                self.sentence_bank.extend([s.strip() for s in sentences if len(s) > 5])
        
        for fact in self.gk_base:
            q = fact.get("q", "")
            a = fact.get("a", "")
            if a:
                sentences = re.split(r'(?<=[.!?])\s+', a)
                self.sentence_bank.extend([s.strip() for s in sentences if len(s) > 5])
        
        self.sentence_bank.extend(self.raw_data_chunks)
        
        for q, a in self.learned_facts.items():
            self.sentence_bank.append(q)
            self.sentence_bank.append(a)
        
        self.sentence_bank = list(set(self.sentence_bank))
        self.total_docs = len(self.sentence_bank)
        
        # Build inverted index
        print("  📇 Building inverted index...")
        for i, sentence in enumerate(self.sentence_bank):
            tokens = self.tokenizer.tokenize(sentence, "hybrid")
            for token in tokens:
                self.inverted_index[token].add(i)
                self.doc_freq[token] += 1
        
        # Build n-gram index
        print("  📊 Building n-gram index...")
        for sentence in self.sentence_bank:
            tokens = self.tokenizer.tokenize(sentence, "basic")
            for n in [2, 3, 4]:
                for ngram in self.tokenizer.ngrams(tokens, n):
                    self.ngram_index[ngram].append(sentence)
        
        # Build co-occurrence matrix
        print("  🧠 Building co-occurrence matrix...")
        self.cooccurrence_matrix = self.vectorizer.build_cooccurrence_matrix(self.sentence_bank)
        
        # Build word vectors
        print("  📐 Building word vectors...")
        for word in list(self.cooccurrence_matrix.keys())[:5000]:
            self.word_vectors[word] = self.vectorizer.build_word_vector(word, self.cooccurrence_matrix)
        
        # Build document vectors
        print("  📄 Building document vectors...")
        for i, sentence in enumerate(self.sentence_bank[:5000]):
            tokens = self.tokenizer.tokenize(sentence, "basic")
            vec = [0] * 100
            count = 0
            for token in tokens:
                if token in self.word_vectors:
                    for j, v in enumerate(self.word_vectors[token]):
                        vec[j] += v
                    count += 1
            if count > 0:
                vec = [v / count for v in vec]
            self.document_vectors[i] = vec
        
        # Build knowledge graph
        print("  🕸️ Building knowledge graph...")
        self._build_knowledge_graph()
        
        # Learn patterns
        print("  🎯 Learning patterns...")
        self._learn_patterns()
        
        print(f"✓ Indexed {len(self.sentence_bank)} sentences")
        print(f"✓ Indexed {len(self.inverted_index)} unique tokens")
        print(f"✓ Indexed {len(self.ngram_index)} n-grams")
        print(f"✓ Built {len(self.word_vectors)} word vectors")
        print(f"✓ Built {len(self.document_vectors)} document vectors")
    
    def _build_knowledge_graph(self):
        """Build knowledge graph from sentences."""
        for sentence in self.sentence_bank:
            # Extract subject-predicate-object patterns
            patterns = [
                r'(\w+(?:\s+\w+){0,3})\s+is\s+(?:a\s+|an\s+|the\s+)?(\w+(?:\s+\w+){0,5})',
                r'(\w+(?:\s+\w+){0,3})\s+was\s+(?:a\s+|an\s+|the\s+)?(\w+(?:\s+\w+){0,5})',
                r'(\w+(?:\s+\w+){0,3})\s+has\s+(\w+(?:\s+\w+){0,5})',
                r'(\w+(?:\s+\w+){0,3})\s+have\s+(\w+(?:\s+\w+){0,5})',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, sentence, re.IGNORECASE)
                for subject, obj in matches:
                    if len(subject) > 2 and len(obj) > 2:
                        self.knowledge_graph.add_fact(subject.lower(), "is", obj.lower())
    
    def _learn_patterns(self):
        """Learn question-answer patterns."""
        for module in self.knowledge_base:
            for pattern in module.get("patterns", []):
                for response in module.get("responses", []):
                    self.predictor.learn_pattern(pattern, response)
        
        for q, a in self.learned_facts.items():
            self.predictor.learn_pattern(q, a)
    
    # ========== SEMANTIC SEARCH ==========
    
    def calculate_tfidf(self, term, doc_idx):
        """Calculate TF-IDF score."""
        tokens = self.tokenizer.tokenize(self.sentence_bank[doc_idx], "basic")
        tf = tokens.count(term) / max(len(tokens), 1)
        idf = math.log(self.total_docs / max(self.doc_freq.get(term, 1), 1))
        return tf * idf
    
    def calculate_bm25(self, query, doc_idx, k1=1.5, b=0.75):
        """Calculate BM25 score (better than TF-IDF)."""
        doc = self.sentence_bank[doc_idx]
        doc_tokens = self.tokenizer.tokenize(doc, "basic")
        query_tokens = self.tokenizer.tokenize(query, "basic")
        
        doc_len = len(doc_tokens)
        avg_doc_len = sum(len(self.tokenizer.tokenize(s, "basic")) for s in self.sentence_bank[:1000]) / min(1000, self.total_docs)
        
        score = 0
        for term in query_tokens:
            if term in doc_tokens:
                tf = doc_tokens.count(term)
                idf = math.log((self.total_docs - self.doc_freq.get(term, 0) + 0.5) / 
                              (self.doc_freq.get(term, 0) + 0.5) + 1)
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * doc_len / avg_doc_len)
                score += idf * numerator / denominator
        
        return score
    
    def search(self, query, top_k=10):
        """Advanced multi-strategy search."""
        results = []
        query_tokens = self.tokenizer.tokenize(query, "hybrid")
        query_basic = self.tokenizer.tokenize(query, "basic")
        
        # Strategy 1: BM25 scoring
        candidate_docs = set()
        for token in query_tokens:
            if token in self.inverted_index:
                candidate_docs.update(self.inverted_index[token])
        
        for doc_idx in candidate_docs:
            score = self.calculate_bm25(query, doc_idx)
            if score > 0:
                results.append((score, self.sentence_bank[doc_idx], "bm25"))
        
        # Strategy 2: Vector similarity
        if query in self.word_vectors:
            query_vec = self.word_vectors[query]
        else:
            query_vec = [0] * 100
            count = 0
            for token in query_basic:
                if token in self.word_vectors:
                    for j, v in enumerate(self.word_vectors[token]):
                        query_vec[j] += v
                    count += 1
            if count > 0:
                query_vec = [v / count for v in query_vec]
        
        for doc_idx, doc_vec in list(self.document_vectors.items())[:1000]:
            sim = self.vectorizer.cosine_similarity(query_vec, doc_vec)
            if sim > 0.1:
                results.append((sim * 0.5, self.sentence_bank[doc_idx], "vector"))
        
        # Strategy 3: N-gram matching
        for n in [2, 3]:
            for ngram in self.tokenizer.ngrams(query_basic, n):
                if ngram in self.ngram_index:
                    for sentence in self.ngram_index[ngram][:5]:
                        results.append((0.6, sentence, "ngram"))
        
        # Strategy 4: Learned facts
        for learned_q, learned_a in self.learned_facts.items():
            similarity = SequenceMatcher(None, query.lower(), learned_q.lower()).ratio()
            if similarity > 0.5:
                results.append((similarity * 0.9, learned_a, "learned"))
        
        # Strategy 5: Knowledge graph
        kg_results = self._search_knowledge_graph(query)
        for result in kg_results:
            results.append((0.7, result, "kg"))
        
        # Deduplicate and sort
        seen = set()
        unique_results = []
        for score, sentence, source in sorted(results, key=lambda x: x[0], reverse=True):
            normalized = sentence.lower().strip()
            if normalized not in seen and len(sentence) > 10:
                seen.add(normalized)
                unique_results.append((score, sentence, source))
        
        return unique_results[:top_k]
    
    def _search_knowledge_graph(self, query):
        """Search the knowledge graph for answers."""
        results = []
        query_lower = query.lower()
        
        # Extract potential subjects
        for word in self.tokenizer.tokenize(query, "basic"):
            kg_results = self.knowledge_graph.query(subject=word)
            for predicate, obj in kg_results:
                results.append(f"{word} {predicate} {obj}")
        
        return results
    
    # ========== ANSWER GENERATION ==========
    
    def _detect_question_type(self, question):
        """Detect question type."""
        q = question.lower().strip()
        for pattern, handler in self.question_patterns.items():
            if q.startswith(pattern):
                return handler
        return self._answer_general
    
    def _answer_definition(self, question, results):
        """Generate definition-style answer."""
        if results and results[0][0] > 0.3:
            return results[0][1]
        return None
    
    def _answer_person(self, question, results):
        """Extract person-related answer."""
        combined = " ".join([s[1] for s in results[:3]])
        match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s+(?:is|was|became)', combined)
        if match:
            return match.group(1)
        return results[0][1] if results else None
    
    def _answer_time(self, question, results):
        """Extract time-related answer."""
        combined = " ".join([s[1] for s in results[:3]])
        match = re.search(r'(?:\d{4}|\d{1,2}\s+\w+\s+\d{4})', combined)
        if match:
            return match.group(0)
        return results[0][1] if results else None
    
    def _answer_location(self, question, results):
        """Extract location-related answer."""
        combined = " ".join([s[1] for s in results[:3]])
        match = re.search(r'(?:in|at|near|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', combined)
        if match:
            return match.group(1)
        return results[0][1] if results else None
    
    def _answer_reason(self, question, results):
        """Extract reason-related answer."""
        combined = " ".join([s[1] for s in results[:3]])
        match = re.search(r'because\s+(.*?)[.!]', combined, re.IGNORECASE)
        if match:
            return match.group(1)
        return results[0][1] if results else None
    
    def _answer_method(self, question, results):
        """Extract method-related answer."""
        return results[0][1] if results else None
    
    def _answer_quantity(self, question, results):
        """Extract quantity-related answer."""
        combined = " ".join([s[1] for s in results[:3]])
        match = re.search(r'\b\d+(?:\.\d+)?\s*(?:million|billion|thousand|hundred|percent|%)?', combined, re.IGNORECASE)
        if match:
            return match.group(0)
        return results[0][1] if results else None
    
    def _answer_choice(self, question, results):
        """Extract choice-related answer."""
        return results[0][1] if results else None
    
    def _answer_general(self, question, results):
        """General answer."""
        if results and results[0][0] > 0.2:
            return results[0][1]
        return None
    
    def generate_answer(self, question):
        """Generate the best answer for a question."""
        # Search
        results = self.search(question, top_k=15)
        
        if not results:
            # Try prediction
            predicted = self.predictor.predict_answer(question)
            if predicted:
                return predicted
            return None
        
        # Get best score
        best_score = results[0][0] if results else 0
        
        if best_score < 0.1:
            return None
        
        # Use appropriate answer handler
        handler = self._detect_question_type(question)
        answer = handler(question, results)
        
        if answer:
            # Trim long answers
            if len(answer) > 500:
                answer = answer[:500].rsplit(' ', 1)[0] + "..."
            return answer
        
        return results[0][1] if results else None
    
    # ========== LEARNING ==========
    
    def learn_fact(self, question, answer):
        """Learn a new fact."""
        self.learned_facts[question] = answer
        
        # Add to indexes
        for text in [question, answer]:
            if text not in self.sentence_bank:
                self.sentence_bank.append(text)
                tokens = self.tokenizer.tokenize(text, "hybrid")
                for token in tokens:
                    self.inverted_index[token].add(len(self.sentence_bank) - 1)
                    self.doc_freq[token] += 1
        
        # Learn pattern
        self.predictor.learn_pattern(question, answer)
        
        self._save_learned_facts()
        return True
    
    def _save_learned_facts(self):
        """Save learned facts."""
        try:
            with open(self.learned_file, 'w', encoding='utf-8') as f:
                json.dump(self.learned_facts, f, indent=2)
        except:
            pass
    
    # ========== RESPONSE ==========
    
    def is_greeting(self, text):
        text_lower = text.lower().strip().rstrip('!.,? ')
        for pattern in self.greetings["patterns"]:
            if re.fullmatch(pattern, text_lower):
                return True
        if len(text_lower.split()) == 1:
            if text_lower in {"hi", "hello", "hey", "yo", "sup", "hola", "bonjour", "heya", "heyy", "hii", "helloo"}:
                return True
        return False
    
    def get_response(self, user_input):
        if not user_input or not user_input.strip():
            return "Please ask me something! 😊"
        
        raw = user_input.strip()
        low = raw.lower()
        
        # Greetings
        if self.is_greeting(raw):
            return random.choice(self.greetings["responses"])
        
        # Learn command
        if low.startswith("learn "):
            content = raw[6:].strip()
            if " : " in content or " = " in content or " -> " in content:
                sep = " : " if " : " in content else (" = " if " = " in content else " -> ")
                parts = content.split(sep, 1)
                if len(parts) == 2:
                    self.learn_fact(parts[0].strip(), parts[1].strip())
                    return f"✅ Learned!"
            return "Use format: learn question : answer"
        
        # Commands
        if low == "reload":
            self.load_all_data()
            self.build_all_indexes()
            return "✅ Reloaded!"
        
        if low == "status":
            return f"📊 Sentences: {len(self.sentence_bank)}\n📊 Tokens: {len(self.inverted_index)}\n📊 Vectors: {len(self.word_vectors)}"
        
        # Generate answer
        answer = self.generate_answer(raw)
        if answer:
            return answer[0].upper() + answer[1:] if len(answer) > 1 else answer
        
        return "I don't know that yet. Teach me with: learn question : answer"


# ========== WEB SERVER ==========
class ChatHandler(BaseHTTPRequestHandler):
    bot = None

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html_path = os.path.join(os.path.dirname(__file__), 'index.html')
            try:
                with open(html_path, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode())
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
                response_text = self.bot.get_response(data.get('message', ''))
            except:
                response_text = "Error processing request"
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
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
║   Advanced Offline AI Engine            ║
╚══════════════════════════════════════════╝
    """)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()

if __name__ == "__main__":
    run_server()
