import re
import random
import json
import os
import hashlib
import time
import math
import threading
from collections import defaultdict, Counter
from http.server import HTTPServer, BaseHTTPRequestHandler
from web_handler import WebSearchHandler

class KeyGenAI:
    def __init__(self, knowledge_dir="knowledge", data_file="data.json", gk_file="gk_knowledge.json"):
        self.name = "KeyGen.ai"
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.knowledge_dir = os.path.join(self.script_dir, knowledge_dir)
        self.collected_dir = os.path.join(self.knowledge_dir, "collected")
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
        self.concept_index = defaultdict(set)
        self.word_cooccurrence = defaultdict(Counter)
        self.word_vectors = {}
        self.word_freq = Counter()
        self.doc_freq = Counter()
        self.entity_map = {}
        self.total_docs = 0
        
        # Web search handler
        self.web_handler = WebSearchHandler()
        self.use_web_search = True
        
        # Stopwords
        self.stopwords = {
            "a", "an", "the", "and", "or", "but", "is", "are", "was", "were",
            "to", "at", "by", "for", "of", "with", "in", "on", "that", "this",
            "it", "its", "be", "been", "being", "have", "has", "had", "do", "does",
            "did", "will", "would", "could", "should", "may", "might", "can", "shall",
            "i", "you", "he", "she", "we", "they", "me", "him", "her", "us", "them",
            "my", "your", "his", "our", "their", "mine", "yours", "hers", "ours", "theirs",
            "about", "above", "after", "again", "all", "also", "any", "because",
            "before", "between", "both", "come", "could", "did", "does",
            "doing", "down", "during", "each", "few", "from", "further", "get",
            "got", "had", "has", "just", "know", "like", "make", "more",
            "most", "much", "must", "now", "off", "only", "other",
            "out", "over", "own", "part", "put", "same", "say", "see",
            "seem", "since", "some", "still", "such", "take", "than", "then",
            "think", "through", "too", "under", "until", "way", "well",
            "when", "where", "which", "while", "who", "why", "would"
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
        os.makedirs(self.collected_dir, exist_ok=True)
        self.load_all_data()
        self.build_indexes()
        self.build_semantic_network()

    # ========== TOKENIZATION ==========
    
    def tokenize(self, text):
        if not text:
            return []
        return re.findall(r'\b\w+\b', str(text).lower())
    
    def tokenize_no_stopwords(self, text):
        tokens = self.tokenize(text)
        return [t for t in tokens if t not in self.stopwords and len(t) > 1]
    
    def normalize_text(self, text):
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_entities(self, text):
        entities = []
        proper_nouns = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', text)
        entities.extend(proper_nouns)
        single_proper = re.findall(r'(?<=\s)([A-Z][a-z]+)\b', text)
        entities.extend([w for w in single_proper if w.lower() not in self.stopwords])
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)
        entities.extend(numbers)
        years = re.findall(r'\b(20\d{2})\b', text)
        entities.extend(years)
        return list(set(entities))
    
    def generate_ngrams(self, tokens, n_range=(1, 5)):
        ngrams = []
        for n in range(n_range[0], n_range[1] + 1):
            for i in range(len(tokens) - n + 1):
                ngram = ' '.join(tokens[i:i+n])
                ngrams.append(ngram)
        return ngrams
    
    # ========== KNOWLEDGE INDEXING ==========
    
    def build_indexes(self):
        print("📚 Building knowledge indexes...")
        
        all_sentences = []
        
        for module in self.knowledge_base:
            for response in module.get("responses", []):
                sentences = re.split(r'(?<=[.!?])\s+', response)
                all_sentences.extend([s.strip() for s in sentences if len(s) > 5])
        
        for fact in self.gk_base:
            q = fact.get("q", "")
            a = fact.get("a", "")
            if q:
                all_sentences.append(q)
                self.entity_index[q.lower()].append(a)
            if a:
                sentences = re.split(r'(?<=[.!?])\s+', a)
                all_sentences.extend([s.strip() for s in sentences if len(s) > 5])
        
        for sentence in self.raw_data_chunks:
            if len(sentence) > 10:
                all_sentences.append(sentence)
        
        for question, answer in self.learned_facts.items():
            all_sentences.append(question)
            all_sentences.append(answer)
        
        self.sentence_bank = list(set(all_sentences))
        self.total_docs = len(self.sentence_bank)
        
        self.entity_index.clear()
        self.ngram_index.clear()
        self.word_freq.clear()
        self.doc_freq.clear()
        
        for sentence in self.sentence_bank:
            tokens = self.tokenize_no_stopwords(sentence)
            self.word_freq.update(tokens)
            
            for token in set(tokens):
                self.doc_freq[token] += 1
            
            entities = self.extract_entities(sentence)
            for entity in entities:
                self.entity_index[entity.lower()].append(sentence)
            
            ngrams = self.generate_ngrams(tokens, n_range=(2, 5))
            for ngram in ngrams:
                self.ngram_index[ngram].append(sentence)
        
        self._build_entity_map()
        
        print(f"✓ Indexed {len(self.sentence_bank)} sentences")
        print(f"✓ Indexed {len(self.entity_index)} entities")
        print(f"✓ Indexed {len(self.ngram_index)} n-grams")
    
    def _build_entity_map(self):
        self.entity_map.clear()
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
    
    def build_semantic_network(self):
        print("🧠 Building semantic network...")
        
        self.word_cooccurrence.clear()
        self.concept_index.clear()
        
        for sentence in self.sentence_bank:
            tokens = self.tokenize_no_stopwords(sentence)
            unique_tokens = set(tokens)
            
            for t1 in unique_tokens:
                for t2 in unique_tokens:
                    if t1 != t2:
                        self.word_cooccurrence[t1][t2] += 1
            
            ngrams = self.generate_ngrams(tokens, n_range=(2, 4))
            for ngram in ngrams:
                for token in unique_tokens:
                    if token not in ngram:
                        self.concept_index[ngram].add(token)
                        self.concept_index[token].add(ngram)
        
        self._build_word_vectors()
        
        print(f"✓ Built semantic network with {len(self.word_cooccurrence)} words")
        print(f"✓ Built {len(self.concept_index)} concept associations")
    
    def _build_word_vectors(self):
        self.word_vectors.clear()
        vocab = list(self.word_cooccurrence.keys())
        
        for word in vocab:
            vector = {}
            for context_word in vocab[:200]:
                if context_word in self.word_cooccurrence[word]:
                    vector[context_word] = self.word_cooccurrence[word][context_word]
            if vector:
                self.word_vectors[word] = vector
    
    # ========== SEMANTIC SIMILARITY ==========
    
    def get_synonyms(self, word, top_n=5):
        if word not in self.word_cooccurrence:
            return []
        similar = self.word_cooccurrence[word].most_common(top_n)
        return [w for w, _ in similar]
    
    def expand_query(self, question):
        tokens = self.tokenize_no_stopwords(question)
        expanded = set(tokens)
        
        for token in tokens:
            for ngram, related in self.concept_index.items():
                if token in ngram.split():
                    expanded.update(related)
            
            synonyms = self.get_synonyms(token, top_n=3)
            expanded.update(synonyms)
        
        return list(expanded)
    
    def generate_question_variations(self, question):
        normalized = self.normalize_text(question)
        tokens = self.tokenize_no_stopwords(question)
        variations = [normalized]
        
        clean = re.sub(r'\b(who|what|when|where|why|how|which|is|are|do|does|did|can|could|will|would|tell|explain|describe|define)\b', '', normalized, flags=re.I)
        clean = re.sub(r'\s+', ' ', clean).strip()
        if clean:
            variations.append(clean)
        
        if normalized.endswith('?'):
            variations.append(normalized[:-1])
        
        for token in tokens:
            if token in ["1st", "first"]:
                variations.extend([
                    normalized.replace("1st", "first"),
                    normalized.replace("first", "1st"),
                    normalized.replace("first", "one")
                ])
            if token in ["2nd", "second"]:
                variations.extend([
                    normalized.replace("2nd", "second"),
                    normalized.replace("second", "2nd"),
                    normalized.replace("second", "two")
                ])
            if token in ["3rd", "third"]:
                variations.extend([
                    normalized.replace("3rd", "third"),
                    normalized.replace("third", "3rd"),
                    normalized.replace("third", "three")
                ])
        
        for token in tokens:
            if token.endswith("s") and token[:-1] + "'s" not in tokens:
                variations.append(normalized.replace(token, token[:-1] + "'s"))
            if token.endswith("'s") and token[:-2] + "s" not in tokens:
                variations.append(normalized.replace(token, token[:-2] + "s"))
        
        return list(set(variations))
    
    def calculate_semantic_similarity(self, text1, text2):
        tokens1 = set(self.tokenize_no_stopwords(text1))
        tokens2 = set(self.tokenize_no_stopwords(text2))
        
        if not tokens1 or not tokens2:
            return 0
        
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        direct_similarity = intersection / union if union > 0 else 0
        
        semantic_overlap = 0
        total_pairs = 0
        for t1 in tokens1:
            for t2 in tokens2:
                if t1 != t2:
                    total_pairs += 1
                    if t2 in self.word_cooccurrence[t1]:
                        semantic_overlap += 1
                    elif t1 in self.word_cooccurrence[t2]:
                        semantic_overlap += 1
        
        semantic_similarity = semantic_overlap / total_pairs if total_pairs > 0 else 0
        
        ngrams1 = set(self.generate_ngrams(list(tokens1), n_range=(2, 3)))
        ngrams2 = set(self.generate_ngrams(list(tokens2), n_range=(2, 3)))
        ngram_overlap = len(ngrams1.intersection(ngrams2)) / max(len(ngrams1.union(ngrams2)), 1)
        
        entities1 = set(e.lower() for e in self.extract_entities(text1))
        entities2 = set(e.lower() for e in self.extract_entities(text2))
        entity_overlap = len(entities1.intersection(entities2)) / max(len(entities1.union(entities2)), 1)
        
        final_score = (
            direct_similarity * 0.35 +
            semantic_similarity * 0.25 +
            ngram_overlap * 0.25 +
            entity_overlap * 0.15
        )
        
        return final_score
    
    def calculate_tfidf_score(self, query, sentence):
        query_tokens = self.tokenize_no_stopwords(query)
        sentence_tokens = self.tokenize_no_stopwords(sentence)
        
        if not query_tokens or not sentence_tokens:
            return 0
        
        score = 0
        for token in query_tokens:
            if token in sentence_tokens:
                tf = sentence_tokens.count(token) / max(len(sentence_tokens), 1)
                idf = math.log(self.total_docs / max(self.doc_freq.get(token, 1), 1))
                score += tf * idf
        
        return score
    
    # ========== SEARCH ENGINE ==========
    
    def search_knowledge(self, question, top_k=10):
        results = []
        variations = self.generate_question_variations(question)
        expanded_terms = self.expand_query(question)
        
        for sentence in self.sentence_bank:
            best_sim = 0
            for var in variations:
                sim = self.calculate_semantic_similarity(var, sentence)
                best_sim = max(best_sim, sim)
            
            if best_sim > 0.1:
                tfidf = self.calculate_tfidf_score(question, sentence)
                score = best_sim * 0.7 + tfidf * 0.3
                results.append((score, sentence, "semantic_match"))
        
        entities = self.extract_entities(question)
        for entity in entities:
            entity_lower = entity.lower()
            if entity_lower in self.entity_index:
                for sentence in self.entity_index[entity_lower]:
                    score = self.calculate_semantic_similarity(question, sentence) + 0.1
                    results.append((score, sentence, "entity_match"))
        
        for var in variations:
            tokens = self.tokenize_no_stopwords(var)
            ngrams = self.generate_ngrams(tokens, n_range=(2, 4))
            for ngram in ngrams:
                if ngram in self.ngram_index:
                    for sentence in self.ngram_index[ngram]:
                        score = self.calculate_semantic_similarity(question, sentence) + 0.15
                        results.append((score, sentence, "ngram_match"))
        
        for sentence in self.sentence_bank:
            sent_tokens = set(self.tokenize_no_stopwords(sentence))
            expanded_matches = len(set(expanded_terms).intersection(sent_tokens))
            if expanded_matches >= 3:
                score = expanded_matches / max(len(expanded_terms), 1)
                score += self.calculate_semantic_similarity(question, sentence)
                results.append((score, sentence, "expanded_match"))
        
        for learned_q, learned_a in self.learned_facts.items():
            if self.calculate_semantic_similarity(question, learned_q) > 0.4:
                results.append((0.95, learned_a, "learned_fact"))
        
        seen = set()
        unique_results = []
        for score, sentence, source in sorted(results, key=lambda x: x[0], reverse=True):
            normalized = self.normalize_text(sentence)
            if normalized not in seen:
                seen.add(normalized)
                unique_results.append((score, sentence, source))
        
        return unique_results[:top_k]
    
    # ========== ANSWER GENERATION ==========
    
    def detect_question_type(self, question):
        q = question.lower().strip()
        if q.startswith("who"):
            return "person"
        if q.startswith("which nation") or q.startswith("which country"):
            return "country"
        if q.startswith("which club") or q.startswith("which team"):
            return "club"
        if q.startswith("what is") or q.startswith("define") or q.startswith("explain"):
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
    
    def extract_best_answer(self, question, results):
        if not results:
            return None
        
        q_type = self.detect_question_type(question)
        combined = " ".join([s[1] for s in results[:5]])
        
        if q_type in ("definition", "general", "reason", "method"):
            if results and results[0][0] > 0.3:
                answer = results[0][1]
                if len(answer) > 300:
                    answer = answer[:300].rsplit(' ', 1)[0] + "..."
                return answer
        
        best_sentence = results[0][1] if results else None
        
        question_tokens = set(self.tokenize_no_stopwords(question))
        for _, sentence, _ in results[:3]:
            sent_tokens = set(self.tokenize_no_stopwords(sentence))
            overlap = len(question_tokens.intersection(sent_tokens))
            if overlap >= 2 and len(sentence) < 500:
                return sentence
        
        return best_sentence
    
    def generate_answer(self, question):
        results = self.search_knowledge(question, top_k=10)
        
        if not results:
            return None
        
        if results[0][0] < 0.15:
            return None
        
        answer = self.extract_best_answer(question, results)
        return answer
    
    # ========== LEARNING SYSTEM ==========
    
    def learn_fact(self, question, answer):
        self.learned_facts[question] = answer
        
        if question not in self.sentence_bank:
            self.sentence_bank.append(question)
        if answer not in self.sentence_bank:
            self.sentence_bank.append(answer)
        
        self.total_docs = len(self.sentence_bank)
        
        for sentence in [question, answer]:
            tokens = self.tokenize_no_stopwords(sentence)
            self.word_freq.update(tokens)
            for token in set(tokens):
                self.doc_freq[token] += 1
            
            entities = self.extract_entities(sentence)
            for entity in entities:
                self.entity_index[entity.lower()].append(sentence)
            
            ngrams = self.generate_ngrams(tokens, n_range=(2, 5))
            for ngram in ngrams:
                self.ngram_index[ngram].append(sentence)
            
            unique_tokens = set(tokens)
            for t1 in unique_tokens:
                for t2 in unique_tokens:
                    if t1 != t2:
                        self.word_cooccurrence[t1][t2] += 1
        
        self.save_learned_facts()
        return True
    
    def learn_from_statement(self, text):
        if not text or len(text.split()) < 5:
            return False
        
        factual_patterns = [" is ", " was ", " are ", " were ", " has ", " have ", " will ", " can ", " does "]
        if any(pattern in text.lower() for pattern in factual_patterns):
            if text not in self.sentence_bank:
                self.sentence_bank.append(text)
                self.total_docs = len(self.sentence_bank)
                
                tokens = self.tokenize_no_stopwords(text)
                self.word_freq.update(tokens)
                for token in set(tokens):
                    self.doc_freq[token] += 1
                
                entities = self.extract_entities(text)
                for entity in entities:
                    self.entity_index[entity.lower()].append(text)
                
                ngrams = self.generate_ngrams(tokens, n_range=(2, 5))
                for ngram in ngrams:
                    self.ngram_index[ngram].append(text)
                
                unique_tokens = set(tokens)
                for t1 in unique_tokens:
                    for t2 in unique_tokens:
                        if t1 != t2:
                            self.word_cooccurrence[t1][t2] += 1
                
                try:
                    with open(self.user_mem_file, 'a', encoding='utf-8') as f:
                        f.write(text.strip() + "\n")
                except:
                    pass
                return True
        return False
    
    def save_learned_facts(self):
        try:
            with open(self.learned_file, 'w', encoding='utf-8') as f:
                json.dump(self.learned_facts, f, indent=2)
        except:
            pass
    
    # ========== DATA LOADING ==========
    
    def load_all_data(self):
        collected_dir = os.path.join(self.knowledge_dir, "collected")
        
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
        
        if os.path.exists(collected_dir):
            for filename in os.listdir(collected_dir):
                if filename.endswith(".txt"):
                    filepath = os.path.join(collected_dir, filename)
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
        
        if self.is_greeting(raw):
            return self.get_greeting_response()
        
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
        
        if low == "reload knowledge":
            self.load_all_data()
            self.build_indexes()
            self.build_semantic_network()
            return "✅ Knowledge base reloaded and re-indexed!"
        
        if low == "status":
            return f"📊 Knowledge Base Status:\n• Modules: {len(self.knowledge_base)}\n• GK Facts: {len(self.gk_base)}\n• Learned Facts: {len(self.learned_facts)}\n• Sentences: {len(self.sentence_bank)}\n• Entities: {len(self.entity_index)}\n• N-grams: {len(self.ngram_index)}\n• Semantic Words: {len(self.word_cooccurrence)}"
        
        if low == "rebuild semantic":
            self.build_semantic_network()
            return "✅ Semantic network rebuilt!"
        
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
            
            html_path = os.path.join(os.path.dirname(__file__), 'index.html')
            try:
                with open(html_path, 'r', encoding='utf-8') as f:
                    html = f.read()
                self.wfile.write(html.encode())
            except FileNotFoundError:
                self.wfile.write(b"Error: index.html not found")
        
        elif self.path == '/collect-now':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            try:
                print("📥 Manual collection triggered via endpoint...")
                self.bot.web_handler.collect_data_auto()
                stats = self.bot.web_handler.get_collection_stats()
                self.wfile.write(json.dumps({
                    'status': 'success',
                    'files_created': stats.get('total_files', 0),
                    'total_hashes': stats.get('total_hashes', 0),
                    'github_enabled': self.bot.web_handler.use_github,
                    'message': 'Collection complete! Check GitHub for new files.'
                }).encode())
            except Exception as e:
                self.wfile.write(json.dumps({
                    'status': 'error',
                    'message': str(e)
                }).encode())
        
        elif self.path == '/collection-status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            stats = self.bot.web_handler.get_collection_stats()
            self.wfile.write(json.dumps({
                'status': 'active' if self.bot.web_handler.is_collecting else 'idle',
                'next_collection': 'Every 2.5 minutes',
                'total_files': stats.get('total_files', 0),
                'total_hashes': stats.get('total_hashes', 0),
                'github_enabled': self.bot.web_handler.use_github,
                'collection_counter': stats.get('counter', 0)
            }).encode())
                
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
    
    # Start auto-collection in background
    def start_collection():
        time.sleep(5)
        print("\n🚀 Starting auto data collection...")
        try:
            bot.web_handler.collect_data_auto()
            bot.web_handler.start_auto_collection()
        except Exception as e:
            print(f"Collection error: {e}")
    
    collection_thread = threading.Thread(target=start_collection, daemon=True)
    collection_thread.start()
    
    server_address = ('0.0.0.0', port)
    server = HTTPServer(server_address, ChatHandler)
    
    print(f"""
╔══════════════════════════════════════════╗
║       🧠 KeyGen.ai ONLINE               ║
║   http://0.0.0.0:{port}                  ║
║   Semantic Knowledge Engine             ║
║   Auto-collection: ACTIVE               ║
╚══════════════════════════════════════════╝
    """)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()

if __name__ == "__main__":
    run_server()
