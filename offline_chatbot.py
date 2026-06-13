"""
KeyGen.ai - Neural Memory Mesh (NMM) Engine
Revolutionary self-organizing knowledge system
Auto-detects port for Render deployment
"""

import re
import random
import json
import os
import math
import time
import hashlib
import socket
from collections import defaultdict, Counter, deque
from http.server import HTTPServer, BaseHTTPRequestHandler
from difflib import SequenceMatcher
from datetime import datetime
from functools import lru_cache

# ========== PORT DETECTION ==========
def get_port():
    """Auto-detect available port - works on Render and locally."""
    # Check environment variable (Render sets this)
    port = os.environ.get("PORT")
    if port:
        return int(port)
    
    # Check for common ports
    for p in [10000, 8080, 5000, 3000, 8000]:
        if not is_port_in_use(p):
            return p
    
    # Find any free port
    return find_free_port()

def is_port_in_use(port):
    """Check if a port is in use."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', port))
            return False
    except:
        return True

def find_free_port():
    """Find a free port."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', 0))
            return s.getsockname()[1]
    except:
        return 10000


# ========== MEMORY NODE ==========
class MemoryNode:
    def __init__(self, content, node_type="concept"):
        self.id = hashlib.md5(content.encode()).hexdigest()[:12]
        self.content = content
        self.type = node_type
        self.connections = defaultdict(float)
        self.activation = 0.0
        self.resting_potential = 0.1
        self.fire_count = 0
        self.last_fired = 0
        self.created_at = time.time()
        self.decay_rate = 0.001
        self.tags = set()
        self.confidence = 0.5
        
    def activate(self, intensity=1.0):
        self.activation = min(1.0, self.resting_potential + intensity)
        self.fire_count += 1
        self.last_fired = time.time()
        if self.fire_count > 3:
            for conn_id in list(self.connections.keys()):
                self.connections[conn_id] *= 1.01
        return self.activation
    
    def connect(self, other_node, strength=0.1):
        current = self.connections.get(other_node.id, 0)
        self.connections[other_node.id] = min(1.0, current + strength)
    
    def decay(self):
        for conn_id in list(self.connections.keys()):
            self.connections[conn_id] *= (1 - self.decay_rate)
            if self.connections[conn_id] < 0.01:
                del self.connections[conn_id]
    
    def get_strongest_connections(self, n=5):
        sorted_conns = sorted(self.connections.items(), key=lambda x: x[1], reverse=True)
        return sorted_conns[:n]


class SynapticPathway:
    def __init__(self, source, target):
        self.source_id = source.id if hasattr(source, 'id') else source
        self.target_id = target.id if hasattr(target, 'id') else target
        self.strength = 0.1
        self.traversal_count = 0
        self.created_at = time.time()
        self.last_traversed = 0
        
    def traverse(self):
        self.traversal_count += 1
        self.last_traversed = time.time()
        self.strength = min(1.0, self.strength * 1.05 + 0.01)
        return self.strength


class TemporalMemory:
    def __init__(self, capacity=200):
        self.activation_history = deque(maxlen=capacity)
        self.sequence_patterns = defaultdict(list)
        
    def record(self, node_id, context=None):
        entry = {'node_id': node_id, 'timestamp': time.time(), 'context': context}
        self.activation_history.append(entry)
    
    def get_recent(self, n=10):
        return [r['node_id'] for r in list(self.activation_history)[-n:]]


class NeuralMemoryMesh:
    def __init__(self):
        self.nodes = {}
        self.pathways = {}
        self.temporal = TemporalMemory()
        self.concept_clusters = defaultdict(set)
        self.activation_threshold = 0.2
        self.spread_factor = 0.7
        self.total_activations = 0
        
    def add_node(self, content, node_type="concept"):
        node = MemoryNode(content, node_type)
        for existing_id, existing_node in self.nodes.items():
            similarity = SequenceMatcher(None, node.content.lower(), existing_node.content.lower()).ratio()
            if similarity > 0.85:
                existing_node.fire_count += 1
                return existing_node
        self.nodes[node.id] = node
        self._auto_connect(node)
        return node
    
    def _auto_connect(self, node):
        words = set(re.findall(r'\b\w+\b', node.content.lower()))
        for existing_id, existing_node in self.nodes.items():
            if existing_id == node.id:
                continue
            existing_words = set(re.findall(r'\b\w+\b', existing_node.content.lower()))
            overlap = len(words & existing_words)
            total = len(words | existing_words)
            if total > 0:
                similarity = overlap / total
                if similarity > 0.1:
                    strength = similarity * 0.5
                    node.connect(existing_node, strength)
                    existing_node.connect(node, strength)
                    pathway = SynapticPathway(node, existing_node)
                    pathway.strength = strength
                    self.pathways[(node.id, existing_node.id)] = pathway
                    cluster_key = min(node.id, existing_node.id)
                    self.concept_clusters[cluster_key].add(node.id)
                    self.concept_clusters[cluster_key].add(existing_node.id)
    
    def activate(self, content, context=None, intensity=1.0):
        self.total_activations += 1
        node = self._find_or_create_node(content)
        node.activate(intensity)
        self.temporal.record(node.id, context)
        activated = self._spread_activation(node.id, intensity)
        if self.total_activations % 100 == 0:
            self._global_decay()
        return activated
    
    def _find_or_create_node(self, content):
        normalized = content.lower().strip()
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        for node in self.nodes.values():
            if node.content.lower().strip() == normalized:
                return node
        return self.add_node(content)
    
    def _spread_activation(self, source_id, intensity):
        activated = {source_id: intensity}
        queue = deque([(source_id, intensity)])
        visited = {source_id}
        while queue:
            current_id, current_intensity = queue.popleft()
            if current_id not in self.nodes:
                continue
            node = self.nodes[current_id]
            for connected_id, strength in node.get_strongest_connections(10):
                if connected_id in visited:
                    continue
                spread_intensity = current_intensity * self.spread_factor * strength
                if spread_intensity > self.activation_threshold:
                    if connected_id in self.nodes:
                        self.nodes[connected_id].activate(spread_intensity)
                        self.temporal.record(connected_id)
                    activated[connected_id] = spread_intensity
                    visited.add(connected_id)
        return activated
    
    def _global_decay(self):
        for node in self.nodes.values():
            node.decay()
    
    def query(self, question, depth=3):
        question_node = self.add_node(question, "question")
        activated = self.activate(question, context="query")
        candidates = []
        for node_id, activation in activated.items():
            if node_id in self.nodes:
                node = self.nodes[node_id]
                score = activation * (1.5 if node.type in ["answer", "fact", "definition"] else 1.0)
                score *= (1 + math.log(node.fire_count + 1) * 0.1)
                candidates.append((score, node))
        candidates.sort(reverse=True, key=lambda x: x[0])
        results = []
        for score, node in candidates[:10]:
            if node.content != question:
                results.append({'content': node.content, 'score': round(score, 3), 'type': node.type, 'activations': node.fire_count})
        return results
    
    def learn(self, question, answer):
        q_node = self.add_node(question, "question")
        a_node = self.add_node(answer, "answer")
        q_node.connect(a_node, 0.9)
        a_node.connect(q_node, 0.9)
        pathway = SynapticPathway(q_node, a_node)
        pathway.strength = 0.9
        pathway.traversal_count = 10
        self.pathways[(q_node.id, a_node.id)] = pathway
        self._auto_connect(a_node)
        return True
    
    def get_stats(self):
        return {'total_nodes': len(self.nodes), 'total_pathways': len(self.pathways), 'total_activations': self.total_activations, 'clusters': len(self.concept_clusters)}


# ========== ULTRA MATH SOLVER ==========
class UltraMathSolver:
    @staticmethod
    def solve(text):
        text = text.lower().strip()
        replacements = {'plus': '+', 'minus': '-', 'times': '*', 'multiplied by': '*', 'divided by': '/', 'into': '*', 'x': '*', '×': '*', '÷': '/', 'power': '**', 'raised to': '**', 'square root of': 'sqrt(', 'cube root of': 'cbrt(', 'mod': '%', 'modulo': '%', 'half of': '*0.5', 'double of': '*2', 'triple of': '*3'}
        for word, symbol in replacements.items():
            text = text.replace(word, symbol)
        sqrt_match = re.search(r'sqrt\((\d+(?:\.\d+)?)\)', text)
        if sqrt_match:
            return round(math.sqrt(float(sqrt_match.group(1))), 4)
        match = re.search(r'(\d+(?:\.\d+)?)\s*([+\-*/%])\s*(\d+(?:\.\d+)?)', text)
        if match:
            a, op, b = float(match.group(1)), match.group(2), float(match.group(3))
            ops = {'+': lambda x,y: x+y, '-': lambda x,y: x-y, '*': lambda x,y: x*y, '/': lambda x,y: x/y if y!=0 else None, '%': lambda x,y: x%y if y!=0 else None}
            if op in ops:
                result = ops[op](a, b)
                if result is not None:
                    return int(result) if result == int(result) else round(result, 4)
        try:
            safe = re.sub(r'[^0-9+\-*/.() ]', '', text)
            if safe and any(op in safe for op in '+-*/'):
                result = eval(safe)
                return int(result) if result == int(result) else round(result, 4)
        except:
            pass
        return None


# ========== CONTEXT TRACKER ==========
class ContextTracker:
    """Tracks conversation context for follow-up questions."""
    
    def __init__(self):
        self.current_topic = None
        self.recent_entities = []
        self.conversation_history = deque(maxlen=10)
        self.topic_stack = []
    
    def update(self, user_input, response):
        self.conversation_history.append({'user': user_input, 'response': response, 'time': time.time()})
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', user_input)
        self.recent_entities = entities[:5]
        if entities:
            self.current_topic = entities[0]
            self.topic_stack.append(self.current_topic)
    
    def get_context(self):
        if self.conversation_history:
            return self.conversation_history[-1]
        return None
    
    def get_topic(self):
        return self.current_topic


# ========== SENTIMENT ANALYZER ==========
class SentimentAnalyzer:
    """Analyzes sentiment of user input."""
    
    def __init__(self):
        self.positive_words = {'good', 'great', 'awesome', 'excellent', 'amazing', 'love', 'wonderful', 'fantastic', 'happy', 'glad', 'thanks', 'thank', 'nice', 'cool', 'brilliant'}
        self.negative_words = {'bad', 'terrible', 'awful', 'horrible', 'hate', 'sad', 'angry', 'upset', 'frustrated', 'poor', 'worst', 'ugly', 'stupid', 'dumb'}
        self.question_words = {'what', 'why', 'how', 'when', 'where', 'who', 'which', 'can', 'could', 'would', 'will', 'is', 'are', 'do', 'does', 'did'}
    
    def analyze(self, text):
        words = set(re.findall(r'\b\w+\b', text.lower()))
        pos = len(words & self.positive_words)
        neg = len(words & self.negative_words)
        is_question = any(text.lower().startswith(w) for w in self.question_words) or '?' in text
        if pos > neg:
            return 'positive'
        elif neg > pos:
            return 'negative'
        elif is_question:
            return 'question'
        return 'neutral'


# ========== RESPONSE GENERATOR ==========
class ResponseGenerator:
    """Generates varied responses based on context and sentiment."""
    
    def __init__(self):
        self.acknowledgments = ["I see!", "Got it!", "Understood!", "Makes sense!", "Noted!"]
        self.encouragements = ["Great question!", "Interesting!", "Let me think about that...", "Good one!"]
        self.positive_responses = ["I'm glad! 😊", "Wonderful! 🌟", "That's great to hear! ✨", "Awesome! 🎉"]
        self.negative_responses = ["I understand. 💙", "I'm here to help. 🤗", "Let's work through this together. 🤝", "That sounds tough. Let me help."]
    
    def generate(self, answer, sentiment, context=None):
        if not answer:
            return "I don't know that yet. Teach me: learn question : answer"
        
        if sentiment == 'positive':
            prefix = random.choice(self.positive_responses) + " "
        elif sentiment == 'negative':
            prefix = random.choice(self.negative_responses) + " "
        elif sentiment == 'question' and len(answer) > 100:
            prefix = random.choice(self.encouragements) + " "
        else:
            prefix = ""
        
        return prefix + answer


# ========== MAIN AI ==========
class KeyGenAI:
    def __init__(self, knowledge_dir="knowledge"):
        self.name = "KeyGen.ai"
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.knowledge_dir = os.path.join(self.script_dir, knowledge_dir)
        self.collected_dir = os.path.join(self.knowledge_dir, "collected")
        
        self.mesh = NeuralMemoryMesh()
        self.math_solver = UltraMathSolver()
        self.context_tracker = ContextTracker()
        self.sentiment = SentimentAnalyzer()
        self.response_gen = ResponseGenerator()
        
        self.qa_cache = {}
        self.commands = {}
        
        self.greeting_responses = [
            "Hello! 👋 How can I help?",
            "Hi there! 😊 Ask me anything!",
            "Hey! ✨ Ready to answer!",
            "Greetings! 🌟 What can I do for you?",
            "Hello! 🚀 I'm listening!",
            "Hi! 💫 What's on your mind?",
            "Welcome! 🤖 How can I assist?",
        ]
        
        # Register commands
        self._register_commands()
        
        os.makedirs(self.knowledge_dir, exist_ok=True)
        os.makedirs(self.collected_dir, exist_ok=True)
        self.load_knowledge()
    
    def _register_commands(self):
        """Register special commands."""
        self.commands = {
            'help': self._cmd_help,
            'status': self._cmd_status,
            'time': self._cmd_time,
            'date': self._cmd_date,
            'calculate': self._cmd_calculate,
            'define': self._cmd_define,
            'search': self._cmd_search,
            'summarize': self._cmd_summarize,
            'translate': self._cmd_translate,
            'remember': self._cmd_remember,
            'forget': self._cmd_forget,
            'clear': self._cmd_clear,
        }
    
    def load_knowledge(self):
        print("🧠 Loading knowledge into Neural Memory Mesh...")
        for directory in [self.knowledge_dir, self.collected_dir]:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    if filename.endswith('.txt'):
                        filepath = os.path.join(directory, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                text = f.read()
                                if text.strip():
                                    sentences = re.split(r'(?<=[.!?])\s+', text)
                                    for sent in sentences:
                                        sent = sent.strip()
                                        if len(sent) > 10:
                                            node_type = "fact" if re.search(r'\b(is|are|was|were|has|have)\b', sent, re.I) else "concept"
                                            self.mesh.add_node(sent, node_type)
                                    defs = re.findall(r'([A-Za-z\s]+?)\s+is\s+(?:a\s+|an\s+|the\s+)?([A-Za-z\s,]+?)[.!]', text, re.IGNORECASE)
                                    for subj, obj in defs:
                                        if len(subj.strip()) > 3 and len(obj.strip()) > 3:
                                            q = f"what is {subj.strip()}"
                                            a = f"{subj.strip()} is {obj.strip()}."
                                            self.mesh.learn(q, a)
                                            self.qa_cache[q.lower()] = a
                        except:
                            pass
        for json_file in ['data.json', 'gk_knowledge.json']:
            filepath = os.path.join(self.script_dir, json_file)
            try:
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for item in data if isinstance(data, list) else []:
                            if 'q' in item and 'a' in item:
                                self.mesh.learn(item['q'], item['a'])
                                self.qa_cache[item['q'].lower()] = item['a']
            except:
                pass
        learned_file = os.path.join(self.knowledge_dir, "learned_knowledge.json")
        try:
            if os.path.exists(learned_file):
                with open(learned_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for q, a in data.items() if isinstance(data, dict) else []:
                        self.mesh.learn(q, a)
                        self.qa_cache[q.lower()] = a
        except:
            pass
        stats = self.mesh.get_stats()
        print(f"✓ Neural Mesh: {stats['total_nodes']} nodes, {stats['total_pathways']} pathways")
    
    # ========== COMMAND HANDLERS ==========
    
    def _cmd_help(self, args=None):
        return """📋 Available commands:
• help - Show this message
• status - Show mesh statistics
• time - Show current time
• date - Show today's date
• calculate <expression> - Solve math
• define <term> - Define a term
• search <query> - Search knowledge
• remember <fact> - Store a fact
• clear - Clear conversation context
• learn Q : A - Teach me something"""
    
    def _cmd_status(self, args=None):
        stats = self.mesh.get_stats()
        return f"🧠 Neural Mesh: {stats['total_nodes']} nodes | {stats['total_pathways']} pathways | {stats['total_activations']} activations | {len(self.qa_cache)} cached Q&As"
    
    def _cmd_time(self, args=None):
        return f"🕐 Current time: {datetime.now().strftime('%H:%M:%S')}"
    
    def _cmd_date(self, args=None):
        return f"📅 Today's date: {datetime.now().strftime('%A, %B %d, %Y')}"
    
    def _cmd_calculate(self, args=None):
        if not args:
            return "Usage: calculate <expression>"
        result = self.math_solver.solve(args)
        return f"🧮 Result: {result}" if result is not None else "Could not solve that expression."
    
    def _cmd_define(self, args=None):
        if not args:
            return "Usage: define <term>"
        results = self.mesh.query(f"what is {args}")
        if results:
            return results[0]['content']
        return f"No definition found for '{args}'."
    
    def _cmd_search(self, args=None):
        if not args:
            return "Usage: search <query>"
        results = self.mesh.query(args)
        if results:
            return "\n".join([f"• {r['content'][:200]}" for r in results[:5]])
        return "No results found."
    
    def _cmd_summarize(self, args=None):
        if not args:
            return "Usage: summarize <text>"
        sentences = re.split(r'(?<=[.!?])\s+', args)
        if len(sentences) <= 2:
            return args
        # Return first and last sentence as summary
        return f"{sentences[0]} ... {sentences[-1]}"
    
    def _cmd_translate(self, args=None):
        return "Translation feature requires internet. Use offline mode for now."
    
    def _cmd_remember(self, args=None):
        if not args:
            return "Usage: remember <fact>"
        self.mesh.add_node(args, "fact")
        return f"✅ Remembered: '{args[:100]}'"
    
    def _cmd_forget(self, args=None):
        return "Memory nodes decay naturally over time. Unused knowledge fades automatically."
    
    def _cmd_clear(self, args=None):
        self.context_tracker = ContextTracker()
        return "🧹 Conversation context cleared."
    
    # ========== MAIN METHODS ==========
    
    def is_greeting(self, text):
        text = text.lower().strip().rstrip('!.,? ')
        greetings = {'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'howdy', 'greetings', 'sup', 'yo', 'hola', 'bonjour', 'heya', 'heyy', 'hii', 'helloo', 'morning', 'evening'}
        if text in greetings:
            return True
        if len(text.split()) <= 2 and any(g in text for g in ['hi', 'hey', 'hello', 'yo', 'sup']):
            return True
        return False
    
    def is_math(self, text):
        return any(op in text.lower() for op in ['+', '-', '*', '/', '×', '÷', 'plus', 'minus', 'times', 'divided', 'square root', 'power'])
    
    def is_command(self, text):
        first_word = text.lower().split()[0] if text.split() else ""
        return first_word in self.commands
    
    def get_response(self, user_input):
        if not user_input or not user_input.strip():
            return "Please ask me something! 😊"
        
        raw = user_input.strip()
        low = raw.lower()
        
        # Sentiment analysis
        sentiment = self.sentiment.analyze(raw)
        
        # Handle commands
        if self.is_command(raw):
            parts = raw.split(maxsplit=1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else None
            if cmd in self.commands:
                result = self.commands[cmd](args)
                self.context_tracker.update(raw, result)
                return result
        
        # Greetings
        if self.is_greeting(raw):
            response = random.choice(self.greeting_responses)
            self.context_tracker.update(raw, response)
            return response
        
        # Math
        if self.is_math(raw):
            result = self.math_solver.solve(raw)
            if result is not None:
                response = f"{result}"
                self.context_tracker.update(raw, response)
                return response
        
        # Learn command
        if low.startswith("learn "):
            content = raw[6:].strip()
            for sep in [" : ", " = ", " -> ", " | "]:
                if sep in content:
                    parts = content.split(sep, 1)
                    if len(parts) == 2:
                        q, a = parts[0].strip(), parts[1].strip()
                        self.mesh.learn(q, a)
                        self.qa_cache[q.lower()] = a
                        try:
                            with open(os.path.join(self.knowledge_dir, "learned_knowledge.json"), 'w', encoding='utf-8') as f:
                                json.dump(self.qa_cache, f, indent=2)
                        except:
                            pass
                        response = "✅ Knowledge absorbed into Neural Memory Mesh!"
                        self.context_tracker.update(raw, response)
                        return response
            return "Format: learn question : answer"
        
        # Quick cache lookup
        if low in self.qa_cache:
            response = self.qa_cache[low]
            self.context_tracker.update(raw, response)
            return response
        
        # Fuzzy cache lookup
        best_match = None
        best_score = 0
        for cached_q, cached_a in self.qa_cache.items():
            score = SequenceMatcher(None, low, cached_q).ratio()
            if score > best_score and score > 0.7:
                best_score = score
                best_match = cached_a
        if best_match:
            self.context_tracker.update(raw, best_match)
            return best_match
        
        # Query Neural Memory Mesh
        results = self.mesh.query(raw)
        if results:
            best = results[0]
            if best['score'] > 0.1:
                answer = best['content']
                if len(answer) > 500:
                    answer = answer[:500].rsplit(' ', 1)[0] + "..."
                if answer and answer[0].islower():
                    answer = answer[0].upper() + answer[1:]
                if answer and answer[-1] not in '.!?':
                    answer += '.'
                response = self.response_gen.generate(answer, sentiment)
                self.context_tracker.update(raw, response)
                return response
        
        response = "I don't know that yet. Teach me: learn question : answer"
        self.context_tracker.update(raw, response)
        return response


# ========== WEB SERVER ==========
class ChatHandler(BaseHTTPRequestHandler):
    bot = None
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass
    
    def do_GET(self):
        if self.path in ['/', '/index.html']:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html_path = os.path.join(os.path.dirname(__file__), 'index.html')
            try:
                with open(html_path, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode())
            except:
                self.wfile.write(b"""<!DOCTYPE html>
<html>
<head><title>KeyGen.ai</title>
<style>
:root{--bg:#000;--surface:#0a0a0a;--text:#fff;--border:#1a1a1a;--accent:#6C63FF}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:var(--bg);color:var(--text);display:flex;justify-content:center;align-items:center;min-height:100vh;padding:16px}
.container{background:var(--surface);border-radius:20px;max-width:750px;width:100%;border:1px solid var(--border);padding:20px}
h1{text-align:center;margin-bottom:20px;color:var(--accent)}
#chat{height:400px;overflow-y:auto;padding:10px;margin-bottom:10px}
.msg{margin:8px 0;padding:10px 14px;border-radius:14px;max-width:80%;word-wrap:break-word}
.user{background:var(--text);color:var(--bg);margin-left:auto}
.ai{background:var(--surface);border:1px solid var(--border)}
#input{width:100%;padding:12px;background:var(--surface);border:1px solid var(--border);border-radius:12px;color:var(--text);font-size:14px;outline:none}
#input:focus{border-color:var(--accent)}
</style>
</head>
<body>
<div class="container">
<h1>🧠 KeyGen.ai</h1>
<div id="chat"></div>
<input id="input" placeholder="Ask anything..." autofocus>
</div>
<script>
const chat=document.getElementById('chat');
const input=document.getElementById('input');
async function send(){
const msg=input.value.trim();
if(!msg)return;
chat.innerHTML+=`<div class="msg user">${msg}</div>`;
input.value='';
chat.innerHTML+='<div class="msg ai">...</div>';
const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})});
const d=await r.json();
chat.lastChild.textContent=d.response;
chat.scrollTop=chat.scrollHeight;
}
input.addEventListener('keypress',e=>{if(e.key==='Enter')send()});
</script>
</body>
</html>""")
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'healthy', 'mesh': self.bot.mesh.get_stats()}).encode())
    
    def do_POST(self):
        if self.path == '/chat':
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length))
            response = self.bot.get_response(data.get('message', ''))
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'response': response}).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_server():
    port = get_port()
    ChatHandler.bot = KeyGenAI()
    server = HTTPServer(('0.0.0.0', port), ChatHandler)
    print(f"""
╔══════════════════════════════════════════╗
║   🧠 KeyGen.ai NMM Engine               ║
║   Port: {port}                            ║
║   Neural Memory Mesh Active             ║
╚══════════════════════════════════════════╝
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == "__main__":
    run_server()
