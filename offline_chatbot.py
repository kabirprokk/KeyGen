"""
KeyGen.ai - Production AI Engine
Guaranteed to work on Render
"""
import os
import sys
import json
import re
import random
import math
import time
import hashlib
import threading
from collections import defaultdict, deque
from http.server import HTTPServer, BaseHTTPRequestHandler
from difflib import SequenceMatcher
from datetime import datetime

# Force immediate output
print("STARTING", flush=True)
sys.stdout.flush()

# Get port from Render
PORT = int(os.environ.get("PORT", 10000))
print(f"PORT={PORT}", flush=True)
sys.stdout.flush()

# ========== CORE CLASSES ==========

class MemoryNode:
    def __init__(self, content, node_type="concept"):
        self.id = hashlib.md5(content.encode('utf-8')).hexdigest()[:12]
        self.content = content
        self.type = node_type
        self.connections = defaultdict(float)
        self.activation = 0.0
        self.fire_count = 0
        self.last_fired = 0
        self.created_at = time.time()

    def activate(self, intensity=1.0):
        self.activation = min(1.0, self.activation + intensity)
        self.fire_count += 1
        self.last_fired = time.time()
        return self.activation

    def connect(self, other_node, strength=0.1):
        self.connections[other_node.id] = min(1.0, self.connections.get(other_node.id, 0) + strength)

    def get_top_connections(self, n=10):
        if not self.connections:
            return []
        return sorted(self.connections.items(), key=lambda x: x[1], reverse=True)[:n]


class NeuralMemoryMesh:
    def __init__(self):
        self.nodes = {}
        self.total_activations = 0

    def add_node(self, content, node_type="concept"):
        node = MemoryNode(content, node_type)
        norm = re.sub(r'[^\w\s]', '', content.lower().strip())
        for existing in self.nodes.values():
            if SequenceMatcher(None, norm, re.sub(r'[^\w\s]', '', existing.content.lower().strip())).ratio() > 0.9:
                existing.fire_count += 1
                return existing
        self.nodes[node.id] = node
        words = set(re.findall(r'\b\w+\b', content.lower()))
        for existing in self.nodes.values():
            if existing.id != node.id:
                ew = set(re.findall(r'\b\w+\b', existing.content.lower()))
                overlap = len(words & ew)
                total = len(words | ew)
                if total > 0 and overlap / total > 0.08:
                    s = (overlap / total) * 0.5
                    node.connect(existing, s)
                    existing.connect(node, s)
        return node

    def activate(self, content, intensity=1.0):
        self.total_activations += 1
        node = self.add_node(content)
        node.activate(intensity)
        activated = {node.id: intensity}
        queue = deque([(node.id, intensity)])
        visited = {node.id}
        while queue:
            cid, ci = queue.popleft()
            if cid not in self.nodes:
                continue
            for conn_id, strength in self.nodes[cid].get_top_connections(8):
                if conn_id in visited:
                    continue
                spread = ci * 0.7 * strength
                if spread > 0.15:
                    if conn_id in self.nodes:
                        self.nodes[conn_id].activate(spread * 0.3)
                    activated[conn_id] = spread
                    visited.add(conn_id)
        return activated

    def query(self, question):
        activated = self.activate(question, 1.0)
        candidates = []
        for node_id, act in activated.items():
            if node_id in self.nodes:
                node = self.nodes[node_id]
                score = act * (2.0 if node.type in ["answer", "fact"] else 1.0)
                if node.fire_count > 0:
                    score *= (1 + math.log(node.fire_count + 1) * 0.15)
                if node.content != question:
                    candidates.append((score, node))
        candidates.sort(reverse=True, key=lambda x: x[0])
        return [{'content': n.content, 'score': round(s, 3)} for s, n in candidates[:10]]

    def learn(self, question, answer):
        qn = self.add_node(question, "question")
        an = self.add_node(answer, "answer")
        qn.connect(an, 0.95)
        an.connect(qn, 0.95)
        return True

    def stats(self):
        return {'nodes': len(self.nodes), 'activations': self.total_activations}


class MathSolver:
    @staticmethod
    def solve(text):
        text = text.lower().strip()
        for w, s in [('plus','+'),('minus','-'),('times','*'),('divided by','/'),('x','*')]:
            text = text.replace(w, s)
        match = re.search(r'(\d+(?:\.\d+)?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)', text)
        if match:
            a, op, b = float(match.group(1)), match.group(2), float(match.group(3))
            ops = {'+': a+b, '-': a-b, '*': a*b, '/': a/b if b!=0 else None}
            if op in ops and ops[op] is not None:
                r = ops[op]
                return int(r) if r == int(r) else round(r, 4)
        return None


# ========== MAIN AI ==========
class KeyGenAI:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.knowledge_dir = os.path.join(self.base_dir, "knowledge")
        self.collected_dir = os.path.join(self.knowledge_dir, "collected")
        self.mesh = NeuralMemoryMesh()
        self.math = MathSolver()
        self.qa_cache = {}
        self.sentences = []
        self.greetings = {'hi','hello','hey','good morning','good afternoon','good evening',
                         'howdy','greetings','sup','yo','hola','heya','heyy','hii','helloo'}
        self.greet_responses = ["Hello! How can I help?","Hi there! Ask me anything!","Hey! Ready to help!","Greetings!","Welcome!","Hello!"]
        os.makedirs(self.knowledge_dir, exist_ok=True)
        os.makedirs(self.collected_dir, exist_ok=True)
        self._load()

    def _load(self):
        for directory in [self.knowledge_dir, self.collected_dir]:
            if os.path.exists(directory):
                for fn in os.listdir(directory):
                    if fn.endswith('.txt'):
                        try:
                            with open(os.path.join(directory, fn), 'r', encoding='utf-8', errors='ignore') as f:
                                text = f.read()
                                for sent in re.split(r'(?<=[.!?])\s+', text):
                                    sent = sent.strip()
                                    if len(sent) > 10:
                                        self.sentences.append(sent)
                                        self.mesh.add_node(sent)
                                for subj, obj in re.findall(r'([A-Za-z\s]{3,}?)\s+is\s+(?:a\s+|an\s+|the\s+)?([A-Za-z\s,]{3,}?)[.!]', text, re.IGNORECASE):
                                    self.qa_cache[f"what is {subj.strip().lower()}"] = f"{subj.strip()} is {obj.strip()}."
                        except: pass
        for jf in ['data.json', 'gk_knowledge.json']:
            try:
                fp = os.path.join(self.base_dir, jf)
                if os.path.exists(fp):
                    with open(fp, 'r') as f:
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
        print(f"AI Loaded: {len(self.qa_cache)} Q&A, {len(self.sentences)} sentences", flush=True)

    def _save(self):
        try:
            with open(os.path.join(self.knowledge_dir, "learned_knowledge.json"), 'w') as f:
                json.dump(self.qa_cache, f, indent=2)
        except: pass

    def get_response(self, user_input):
        if not user_input or not user_input.strip():
            return "Please ask me something!"
        raw = user_input.strip()
        low = raw.lower()

        # Greetings
        if low.rstrip('!.,? ') in self.greetings or (len(low.split()) <= 2 and any(g in low for g in ['hi','hey','hello','yo','sup'])):
            return random.choice(self.greet_responses)

        # Math
        if any(op in low for op in ['+','-','*','/','plus','minus','times','divided']):
            r = self.math.solve(raw)
            if r is not None: return str(r)

        # Learn
        if low.startswith("learn "):
            content = raw[6:].strip()
            for sep in [" : ", " = ", " -> "]:
                if sep in content:
                    q, a = content.split(sep, 1)
                    self.qa_cache[q.strip().lower()] = a.strip()
                    self.mesh.learn(q.strip(), a.strip())
                    self._save()
                    return "Learned!"
            return "Format: learn question : answer"

        # Commands
        if low == 'help': return "Commands: help | status | time | calculate expr | define term | search query | learn Q : A"
        if low == 'status': return f"Nodes: {self.mesh.stats()['nodes']} | Q&A: {len(self.qa_cache)} | Sentences: {len(self.sentences)}"
        if low == 'time': return datetime.now().strftime('%H:%M:%S')
        if low.startswith("calculate "):
            r = self.math.solve(raw[10:])
            return str(r) if r is not None else "Cannot solve"
        if low.startswith("define "):
            term = raw[7:].strip().lower()
            q = f"what is {term}"
            if q in self.qa_cache: return self.qa_cache[q]
            for cq, ca in self.qa_cache.items():
                if term in cq: return ca
            return f"No definition for '{term}'"
        if low.startswith("search "):
            query = raw[7:].strip().lower()
            results = [s[:300] for s in self.sentences if query in s.lower()][:5]
            return "\n".join([f"- {r}" for r in results]) if results else "No results"

        # Exact cache
        if low in self.qa_cache: return self.qa_cache[low]

        # Fuzzy cache
        best, bs = None, 0
        for q, a in self.qa_cache.items():
            s = SequenceMatcher(None, low, q).ratio()
            if s > bs and s > 0.6: best, bs = a, s
        if best: return best

        # Mesh query
        results = self.mesh.query(raw)
        if results and results[0]['score'] > 0.08:
            ans = results[0]['content']
            return ans[:500] if len(ans) > 500 else ans

        # Sentence search
        if self.sentences:
            qw = set(re.findall(r'\b\w+\b', low))
            scored = [(len(qw & set(re.findall(r'\b\w+\b', s.lower()))) / max(len(qw),1), s) for s in self.sentences]
            scored = [(s, t) for s, t in scored if s > 0.15]
            if scored:
                scored.sort(reverse=True, key=lambda x: x[0])
                return scored[0][1][:500]

        return "I don't know that yet. Teach me: learn question : answer"


# ========== CREATE AI INSTANCE ==========
print("Loading AI engine...", flush=True)
AI = KeyGenAI()
print("AI engine ready!", flush=True)

# ========== HTTP HANDLER ==========
class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == '/health':
            self._send_json({'status': 'healthy'})
        elif self.path == '/stats':
            self._send_json({'stats': AI.mesh.stats(), 'qa': len(AI.qa_cache)})
        else:
            html_path = os.path.join(os.path.dirname(__file__), 'index.html')
            if os.path.exists(html_path):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                with open(html_path, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode())
            else:
                self._send_json({'status': 'running', 'name': 'KeyGen.ai'})

    def do_POST(self):
        if self.path == '/chat':
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length))
            response = AI.get_response(data.get('message', ''))
            self._send_json({'response': response})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def _send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


# ========== START SERVER ==========
print(f"Starting server on 0.0.0.0:{PORT}...", flush=True)
server = HTTPServer(('0.0.0.0', PORT), Handler)
print(f"SERVER RUNNING ON PORT {PORT}", flush=True)
sys.stdout.flush()

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("Shutting down...", flush=True)
    server.shutdown()
