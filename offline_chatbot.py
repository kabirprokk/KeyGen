"""
KeyGen.ai - Neural Memory Mesh (NMM) Engine
All bugs fixed for Render deployment
"""

import re
import random
import json
import os
import math
import time
import hashlib
import threading
from collections import defaultdict, deque
from http.server import HTTPServer, BaseHTTPRequestHandler
from difflib import SequenceMatcher
from datetime import datetime


# ========== QUANTUM MEMORY CELL ==========
class QuantumMemoryCell:
    def __init__(self, content):
        self.content = content
        self.states = defaultdict(float)
        self.collapse_count = 0

    def superpose(self, meaning, weight=0.5):
        self.states[meaning] = weight

    def collapse(self, context=None):
        self.collapse_count += 1
        if not self.states:
            return self.content
        if context:
            for state in list(self.states.keys()):
                if context in state:
                    self.states[state] *= 1.5
        if not self.states:
            return self.content
        best = max(self.states.items(), key=lambda x: x[1])
        return best[0] if best[1] > 0.3 else self.content


# ========== DREAM ENGINE (FIXED) ==========
class DreamEngine:
    def __init__(self):
        self.dreams = deque(maxlen=50)
        self.insights = []

    def dream(self, mesh):
        if len(mesh.nodes) < 3:
            return None
        nodes = list(mesh.nodes.values())
        sample_size = min(3, len(nodes))
        if sample_size < 2:
            return None
        sampled = random.sample(nodes, sample_size)
        n1, n2 = sampled[0], sampled[1]
        n3 = sampled[2] if len(sampled) > 2 else sampled[0]
        words1 = set(re.findall(r'\b\w+\b', n1.content.lower()))
        words2 = set(re.findall(r'\b\w+\b', n2.content.lower()))
        words3 = set(re.findall(r'\b\w+\b', n3.content.lower()))
        common = words1 & words2 & words3
        if common:
            insight = f"Dream insight: {', '.join(list(common)[:3])}"
            self.insights.append(insight)
            return insight
        self.dreams.append(f"{n1.content[:50]} + {n2.content[:50]}")
        return None


# ========== INTUITION GENERATOR ==========
class IntuitionGenerator:
    def __init__(self):
        self.total_guesses = 0

    def intuit(self, question, mesh, qa_cache):
        self.total_guesses += 1
        concepts = re.findall(r'\b\w{4,}\b', question.lower())
        candidates = []
        for cached_q, cached_a in qa_cache.items():
            score = sum(1 for c in concepts if c in cached_q)
            if score > 0:
                candidates.append((score, cached_a))
        if candidates:
            candidates.sort(reverse=True, key=lambda x: x[0])
            return f"I think... {candidates[0][1]}"
        question_words = set(re.findall(r'\b\w+\b', question.lower()))
        for node in mesh.nodes.values():
            if node.type in ["fact", "answer"]:
                node_words = set(re.findall(r'\b\w+\b', node.content.lower()))
                if len(question_words & node_words) >= 3:
                    return f"Possibly... {node.content[:300]}"
        return None


# ========== EMPATHY MODULE ==========
class EmpathyModule:
    def __init__(self):
        self.emotion_patterns = {
            'joy': [r'\b(happy|glad|wonderful|amazing|great|awesome|excited)\b'],
            'sadness': [r'\b(sad|unhappy|depressed|upset|heartbroken|miserable)\b'],
            'anger': [r'\b(angry|furious|mad|annoyed|frustrated|rage|hate)\b'],
            'fear': [r'\b(scared|afraid|terrified|nervous|anxious|worried)\b'],
            'curiosity': [r'\b(curious|wondering|interesting|fascinating|explain)\b'],
            'confusion': [r'\b(confused|puzzled|unclear|what do you mean)\b'],
            'gratitude': [r'\b(thanks|thank you|grateful|appreciate)\b'],
            'determination': [r'\b(must|need to|have to|going to|determined)\b'],
        }
        self.emotion_memory = deque(maxlen=50)

    def detect(self, text):
        text_lower = text.lower()
        detected = {}
        for emotion, patterns in self.emotion_patterns.items():
            score = sum(len(re.findall(p, text_lower)) for p in patterns)
            if score > 0:
                detected[emotion] = score
        if not detected:
            return 'neutral', 0
        primary = max(detected.items(), key=lambda x: x[1])
        self.emotion_memory.append(primary[0])
        return primary[0], primary[1]

    def respond_with_empathy(self, emotion, base_response):
        prefixes = {
            'joy': "I'm happy to hear that! ",
            'sadness': "I understand. ",
            'anger': "I hear you. ",
            'fear': "It's okay. ",
            'curiosity': "Great question! ",
            'confusion': "Let me clarify. ",
            'gratitude': "You're welcome! ",
            'determination': "I admire that! ",
        }
        return prefixes.get(emotion, "") + base_response


# ========== MEMORY PALACE ==========
class MemoryPalace:
    def __init__(self):
        self.rooms = defaultdict(dict)

    def categorize(self, content):
        content_lower = content.lower()
        categories = {
            'science': {'physics', 'chemistry', 'biology', 'math', 'science', 'quantum', 'atom', 'cell', 'dna', 'energy'},
            'history': {'war', 'king', 'queen', 'empire', 'ancient', 'revolution', 'president'},
            'technology': {'computer', 'software', 'algorithm', 'ai', 'code', 'data', 'internet', 'robot'},
            'philosophy': {'meaning', 'ethics', 'moral', 'consciousness', 'truth', 'wisdom', 'mind'},
        }
        scores = {cat: sum(1 for w in words if w in content_lower) for cat, words in categories.items()}
        best = max(scores.items(), key=lambda x: x[1]) if scores else ('misc', 0)
        return best[0] if best[1] > 0 else 'misc'

    def store(self, content):
        room = self.categorize(content)
        key = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
        self.rooms[room][key] = {'content': content, 'timestamp': time.time()}
        return room, key

    def recall(self, query, room=None):
        results = []
        rooms_to_search = [room] if room else list(self.rooms.keys())
        for r in rooms_to_search:
            for memory in self.rooms[r].values():
                sim = SequenceMatcher(None, query.lower(), memory['content'].lower()).ratio()
                if sim > 0.2:
                    results.append((sim, memory['content'], r))
        results.sort(reverse=True, key=lambda x: x[0])
        return results[:10]


# ========== MEMORY NODE (FIXED) ==========
class MemoryNode:
    def __init__(self, content, node_type="concept"):
        self.id = hashlib.md5(content.encode('utf-8')).hexdigest()[:12]
        self.content = content
        self.type = node_type
        self.connections = defaultdict(float)
        self.activation = 0.0
        self.resting_potential = 0.1
        self.fire_count = 0
        self.last_fired = 0
        self.created_at = time.time()
        self.decay_rate = 0.001

    def activate(self, intensity=1.0):
        self.activation = min(1.0, self.resting_potential + intensity)
        self.fire_count += 1
        self.last_fired = time.time()
        if self.fire_count > 3:
            for conn_id in list(self.connections.keys()):
                self.connections[conn_id] = min(1.0, self.connections[conn_id] * 1.01)
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
        if not self.connections:
            return []
        return sorted(self.connections.items(), key=lambda x: x[1], reverse=True)[:n]


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


class NeuralMemoryMesh:
    def __init__(self):
        self.nodes = {}
        self.pathways = {}
        self.temporal = deque(maxlen=200)
        self.concept_clusters = defaultdict(set)
        self.activation_threshold = 0.2
        self.spread_factor = 0.7
        self.total_activations = 0
        self.memory_palace = MemoryPalace()
        self.dream_engine = DreamEngine()
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        """Periodically clean up dead nodes and pathways."""
        def cleanup():
            while True:
                time.sleep(300)  # Every 5 minutes
                self._cleanup()
        t = threading.Thread(target=cleanup, daemon=True)
        t.start()

    def _cleanup(self):
        """Remove dead nodes and weak pathways."""
        dead_nodes = []
        for node_id, node in self.nodes.items():
            if node.fire_count == 0 and time.time() - node.created_at > 3600:
                dead_nodes.append(node_id)
        for node_id in dead_nodes:
            del self.nodes[node_id]
        dead_pathways = []
        for key, pathway in self.pathways.items():
            if time.time() - pathway.last_traversed > 7200 and pathway.traversal_count < 2:
                dead_pathways.append(key)
        for key in dead_pathways:
            del self.pathways[key]

    def add_node(self, content, node_type="concept"):
        node = MemoryNode(content, node_type)
        for existing_id, existing_node in self.nodes.items():
            similarity = SequenceMatcher(None, node.content.lower(), existing_node.content.lower()).ratio()
            if similarity > 0.85:
                existing_node.fire_count += 1
                return existing_node
        self.nodes[node.id] = node
        self._auto_connect(node)
        self.memory_palace.store(content)
        return node

    def _auto_connect(self, node):
        words = set(re.findall(r'\b\w+\b', node.content.lower()))
        for existing_id, existing_node in self.nodes.items():
            if existing_id == node.id:
                continue
            existing_words = set(re.findall(r'\b\w+\b', existing_node.content.lower()))
            overlap = len(words & existing_words)
            total = len(words | existing_words)
            if total > 0 and overlap / total > 0.1:
                strength = (overlap / total) * 0.5
                node.connect(existing_node, strength)
                existing_node.connect(node, strength)
                pathway = SynapticPathway(node, existing_node)
                pathway.strength = strength
                self.pathways[(node.id, existing_node.id)] = pathway

    def activate(self, content, context=None, intensity=1.0):
        self.total_activations += 1
        node = self._find_or_create_node(content)
        node.activate(intensity)
        self.temporal.append({'node_id': node.id, 'timestamp': time.time(), 'context': context})
        activated = self._spread_activation(node.id, intensity)
        if self.total_activations % 50 == 0:
            self._global_decay()
            self.dream_engine.dream(self)
        return activated

    def _find_or_create_node(self, content):
        normalized = re.sub(r'[^\w\s]', '', content.lower().strip())
        normalized = re.sub(r'\s+', ' ', normalized)
        for node in self.nodes.values():
            if re.sub(r'[^\w\s]', '', node.content.lower().strip()) == normalized:
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
                    activated[connected_id] = spread_intensity
                    visited.add(connected_id)
        return activated

    def _global_decay(self):
        for node in list(self.nodes.values()):
            node.decay()

    def query(self, question):
        self.add_node(question, "question")
        activated = self.activate(question, context="query")
        candidates = []
        for node_id, activation in activated.items():
            if node_id in self.nodes:
                node = self.nodes[node_id]
                score = activation * (1.5 if node.type in ["answer", "fact", "definition"] else 1.0)
                if node.fire_count > 0:
                    score *= (1 + math.log(node.fire_count + 1) * 0.1)
                candidates.append((score, node))
        candidates.sort(reverse=True, key=lambda x: x[0])
        results = []
        for score, node in candidates[:10]:
            if node.content != question:
                results.append({
                    'content': node.content,
                    'score': round(score, 3),
                    'type': node.type,
                    'activations': node.fire_count
                })
        return results

    def learn(self, question, answer):
        q_node = self.add_node(question, "question")
        a_node = self.add_node(answer, "answer")
        q_node.connect(a_node, 0.9)
        a_node.connect(q_node, 0.9)
        self.memory_palace.store(answer)
        return True

    def get_stats(self):
        return {
            'total_nodes': len(self.nodes),
            'total_pathways': len(self.pathways),
            'total_activations': self.total_activations,
        }


# ========== MATH SOLVER ==========
class UltraMathSolver:
    @staticmethod
    def solve(text):
        text = text.lower().strip()
        reps = {'plus': '+', 'minus': '-', 'times': '*', 'divided by': '/',
                'power': '**', 'half of': '*0.5', 'double of': '*2'}
        for w, s in reps.items():
            text = text.replace(w, s)
        match = re.search(r'(\d+(?:\.\d+)?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)', text)
        if match:
            a, op, b = float(match.group(1)), match.group(2), float(match.group(3))
            ops = {'+': lambda x, y: x + y, '-': lambda x, y: x - y,
                   '*': lambda x, y: x * y, '/': lambda x, y: x / y if y != 0 else None}
            if op in ops:
                result = ops[op](a, b)
                if result is not None:
                    return int(result) if result == int(result) else round(result, 4)
        return None


# ========== MAIN AI ==========
class KeyGenAI:
    def __init__(self, knowledge_dir="knowledge"):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.knowledge_dir = os.path.join(self.script_dir, knowledge_dir)
        self.collected_dir = os.path.join(self.knowledge_dir, "collected")
        self.mesh = NeuralMemoryMesh()
        self.math_solver = UltraMathSolver()
        self.empathy = EmpathyModule()
        self.intuition = IntuitionGenerator()
        self.qa_cache = {}
        self.commands = {}
        self.greetings = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening", "howdy", "greetings", "sup", "yo", "hola", "heya", "heyy", "hii", "helloo"}
        self.greeting_responses = ["Hello! How can I help?", "Hi there! Ask me anything!", "Hey! Ready to answer!", "Greetings! What can I do?", "Hello! I'm listening!", "Welcome! How can I assist?"]
        self._register_commands()
        os.makedirs(self.knowledge_dir, exist_ok=True)
        os.makedirs(self.collected_dir, exist_ok=True)
        self.load_knowledge()

    def _register_commands(self):
        self.commands = {
            'help': lambda a: "Commands: help | status | time | date | calculate <expr> | define <term> | search <query> | remember <fact> | clear",
            'status': lambda a: f"Nodes: {self.mesh.get_stats()['total_nodes']} | Cache: {len(self.qa_cache)}",
            'time': lambda a: datetime.now().strftime('%H:%M:%S'),
            'date': lambda a: datetime.now().strftime('%A, %B %d, %Y'),
            'calculate': lambda a: str(self.math_solver.solve(a)) if a and self.math_solver.solve(a) is not None else "Usage: calculate 5+3",
            'define': self._cmd_define,
            'search': self._cmd_search,
            'remember': lambda a: (self.mesh.add_node(a, "fact"), "Remembered.")[1] if a else "Usage: remember <fact>",
            'clear': lambda a: "Context cleared.",
            'dream': lambda a: self.mesh.dream_engine.dream(self.mesh) or "Dreaming...",
            'intuit': self._cmd_intuit,
        }

    def _cmd_define(self, args):
        if not args: return "Usage: define <term>"
        results = self.mesh.query(f"what is {args}")
        return results[0]['content'] if results else f"No definition for '{args}'."

    def _cmd_search(self, args):
        if not args: return "Usage: search <query>"
        results = self.mesh.query(args)
        return "\n".join([f"- {r['content'][:200]}" for r in results[:5]]) if results else "No results."

    def _cmd_intuit(self, args):
        if not args: return "Usage: intuit <question>"
        return self.intuition.intuit(args, self.mesh, self.qa_cache) or "Intuition fails."

    def load_knowledge(self):
        print("Loading knowledge...")
        for directory in [self.knowledge_dir, self.collected_dir]:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    if filename.endswith('.txt'):
                        try:
                            with open(os.path.join(directory, filename), 'r', encoding='utf-8', errors='ignore') as f:
                                text = f.read()
                                for sent in re.split(r'(?<=[.!?])\s+', text):
                                    sent = sent.strip()
                                    if len(sent) > 10:
                                        self.mesh.add_node(sent, "fact" if re.search(r'\b(is|are|was|were)\b', sent, re.I) else "concept")
                                for subj, obj in re.findall(r'([A-Za-z\s]+?)\s+is\s+(?:a\s+|an\s+|the\s+)?([A-Za-z\s,]+?)[.!]', text, re.IGNORECASE):
                                    if len(subj.strip()) > 3 and len(obj.strip()) > 3:
                                        q = f"what is {subj.strip()}"
                                        a = f"{subj.strip()} is {obj.strip()}."
                                        self.qa_cache[q.lower()] = a
                        except: pass
        for jf in ['data.json', 'gk_knowledge.json']:
            try:
                if os.path.exists(os.path.join(self.script_dir, jf)):
                    with open(os.path.join(self.script_dir, jf), 'r') as f:
                        for item in json.load(f):
                            if 'q' in item and 'a' in item:
                                self.qa_cache[item['q'].lower()] = item['a']
            except: pass
        try:
            lf = os.path.join(self.knowledge_dir, "learned_knowledge.json")
            if os.path.exists(lf):
                with open(lf, 'r') as f:
                    for q, a in json.load(f).items():
                        self.qa_cache[q.lower()] = a
        except: pass
        print(f"Loaded: {len(self.qa_cache)} Q&A pairs, {self.mesh.get_stats()['total_nodes']} nodes")

    def get_response(self, user_input):
        if not user_input or not user_input.strip():
            return "Please ask me something!"
        raw = user_input.strip()
        low = raw.lower()
        emotion, _ = self.empathy.detect(raw)
        # Commands
        first_word = low.split()[0] if low.split() else ""
        if first_word in self.commands:
            args = raw.split(maxsplit=1)[1] if len(raw.split()) > 1 else None
            return self.commands[first_word](args)
        # Greetings
        if low.rstrip('!.,? ') in self.greetings or (len(low.split()) <= 2 and any(g in low for g in ['hi','hey','hello','yo','sup'])):
            return self.empathy.respond_with_empathy(emotion, random.choice(self.greeting_responses))
        # Math
        if any(op in low for op in ['+','-','*','/','plus','minus','times','divided']):
            result = self.math_solver.solve(raw)
            if result is not None:
                return str(result)
        # Learn
        if low.startswith("learn "):
            content = raw[6:].strip()
            for sep in [" : ", " = ", " -> "]:
                if sep in content:
                    q, a = content.split(sep, 1)
                    self.qa_cache[q.strip().lower()] = a.strip()
                    self.mesh.learn(q.strip(), a.strip())
                    try:
                        with open(os.path.join(self.knowledge_dir, "learned_knowledge.json"), 'w') as f:
                            json.dump(self.qa_cache, f, indent=2)
                    except: pass
                    return "Learned!"
            return "Format: learn question : answer"
        # Cache lookup
        if low in self.qa_cache:
            return self.qa_cache[low]
        best, best_score = None, 0
        for q, a in self.qa_cache.items():
            s = SequenceMatcher(None, low, q).ratio()
            if s > best_score and s > 0.65:
                best_score, best = s, a
        if best:
            return best
        # Mesh query
        results = self.mesh.query(raw)
        if map and results and results[0]['score'] > 0.1:
            ans = results[0]['content']
            if len(ans) > 600:
                ans = ans[:600].rsplit(' ', 1)[0] + "..."
            return self.empathy.respond_with_empathy(emotion, ans)
        # Intuition
        intuitive = self.intuition.intuit(raw, self.mesh, self.qa_cache)
        if intuitive:
            return intuitive
        return "I don't know that yet. Teach me: learn question : answer"


# ========== WEB SERVER (FIXED) ==========
class ChatHandler(BaseHTTPRequestHandler):
    bot = None

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path in ['/', '/index.html']:
            html_path = os.path.join(os.path.dirname(__file__), 'index.html')
            if os.path.exists(html_path):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                with open(html_path, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode())
            else:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'running', 'name': 'KeyGen.ai NMM'}).encode())
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'healthy'}).encode())

    def do_POST(self):
        if self.path == '/chat':
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length))
            response = self.bot.get_response(data.get('message', ''))
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            self.wfile.write(json.dumps({'response': response}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def run_server():
    # Render binds dynamic ports here automatically
    port = int(os.environ.get("PORT", 10000))
    print(f"PORT={port}", flush=True)
    ChatHandler.bot = KeyGenAI()
    server = HTTPServer(('0.0.0.0', port), ChatHandler)
    print(f"KeyGen.ai running on port {port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == "__main__":
    run_server()
