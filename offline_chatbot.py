"""
KeyGen.ai - Full Production AI Engine
Neural Memory Mesh + Quantum Memory + Dream Engine + Empathy + Intuition
Flask + Gunicorn for Render
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
from collections import defaultdict, deque, Counter
from difflib import SequenceMatcher
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory

# ========== QUANTUM MEMORY CELL ==========
class QuantumMemoryCell:
    """Memory exists in multiple states until queried."""
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


# ========== DREAM ENGINE ==========
class DreamEngine:
    """Creates new insights by randomly connecting memories during idle time."""
    def __init__(self):
        self.dreams = deque(maxlen=100)
        self.insights = deque(maxlen=50)
        self.dream_count = 0

    def dream(self, mesh):
        if len(mesh.nodes) < 3:
            return None
        nodes = list(mesh.nodes.values())
        n = min(3, len(nodes))
        sampled = random.sample(nodes, n)
        words_sets = [set(re.findall(r'\b\w+\b', node.content.lower())) for node in sampled]
        common = words_sets[0]
        for ws in words_sets[1:]:
            common = common & ws
        if common:
            insight = f"Connected concepts: {', '.join(list(common)[:5])}"
            self.insights.append({'insight': insight, 'time': time.time()})
            return insight
        self.dreams.append({'content': f"{sampled[0].content[:50]} <-> {sampled[1].content[:50]}", 'time': time.time()})
        self.dream_count += 1
        return None


# ========== EMPATHY MODULE ==========
class EmpathyModule:
    """Detects 8 emotional states and responds with emotional intelligence."""
    def __init__(self):
        self.emotions = {
            'joy': [r'\b(happy|glad|wonderful|amazing|great|awesome|excited|love|beautiful|fantastic)\b'],
            'sadness': [r'\b(sad|unhappy|depressed|upset|heartbroken|miserable|crying|hurt|alone)\b'],
            'anger': [r'\b(angry|furious|mad|annoyed|frustrated|rage|hate|stupid|worst)\b'],
            'fear': [r'\b(scared|afraid|terrified|nervous|anxious|worried|panic|frightened)\b'],
            'curiosity': [r'\b(curious|wondering|interesting|fascinating|explain|how|what|why|tell me)\b'],
            'confusion': [r'\b(confused|puzzled|unclear|dont understand|what do you mean|huh|wait)\b'],
            'gratitude': [r'\b(thanks|thank you|grateful|appreciate|thankful|blessed|thank)\b'],
            'hope': [r'\b(hope|wish|dream|aspire|looking forward|someday|future|goal)\b'],
        }
        self.emotion_memory = deque(maxlen=100)
        self.empathy_prefixes = {
            'joy': "That's wonderful! 😊 ",
            'sadness': "I understand. 💙 ",
            'anger': "I hear you. 🤝 ",
            'fear': "It's okay to feel that way. ",
            'curiosity': "Great question! ✨ ",
            'confusion': "Let me clarify. 💡 ",
            'gratitude': "You're welcome! 🙏 ",
            'hope': "That's beautiful! 🌟 ",
        }

    def detect(self, text):
        text_lower = text.lower()
        scores = {}
        for emotion, patterns in self.emotions.items():
            score = sum(len(re.findall(p, text_lower)) for p in patterns)
            if score > 0:
                scores[emotion] = score
        if not scores:
            return 'neutral', 0
        primary = max(scores.items(), key=lambda x: x[1])
        self.emotion_memory.append(primary[0])
        return primary[0], primary[1]

    def respond(self, emotion, response):
        prefix = self.empathy_prefixes.get(emotion, "")
        return prefix + response if prefix and len(response) > 40 else response


# ========== INTUITION ENGINE ==========
class IntuitionEngine:
    """Makes educated guesses when exact knowledge is missing."""
    def __init__(self):
        self.guesses = 0
        self.successes = 0

    def intuit(self, question, qa_cache, sentences):
        self.guesses += 1
        concepts = re.findall(r'\b\w{4,}\b', question.lower())
        
        # Method 1: Partial Q&A matching
        candidates = []
        for q, a in qa_cache.items():
            score = sum(1 for c in concepts if c in q)
            if score > 0:
                candidates.append((score, a))
        if candidates:
            candidates.sort(reverse=True, key=lambda x: x[0])
            self.successes += 1
            return f"I believe... {candidates[0][1]}"
        
        # Method 2: Sentence matching
        question_words = set(concepts)
        matches = []
        for sent in sentences:
            sent_words = set(re.findall(r'\b\w+\b', sent.lower()))
            overlap = len(question_words & sent_words)
            if overlap >= 3:
                matches.append((overlap, sent))
        if matches:
            matches.sort(reverse=True, key=lambda x: x[0])
            return f"Possibly... {matches[0][1][:400]}"
        
        return None


# ========== MEMORY NODE ==========
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
        self.quantum = QuantumMemoryCell(content)

    def activate(self, intensity=1.0):
        self.activation = min(1.0, self.activation + intensity)
        self.fire_count += 1
        self.last_fired = time.time()
        if self.fire_count > 5:
            for conn_id in list(self.connections.keys()):
                self.connections[conn_id] = min(1.0, self.connections[conn_id] * 1.02)
        return self.activation

    def connect(self, other_node, strength=0.1):
        self.connections[other_node.id] = min(1.0, self.connections.get(other_node.id, 0) + strength)

    def decay(self):
        for conn_id in list(self.connections.keys()):
            self.connections[conn_id] *= 0.998
            if self.connections[conn_id] < 0.01:
                del self.connections[conn_id]

    def get_top_connections(self, n=10):
        if not self.connections:
            return []
        return sorted(self.connections.items(), key=lambda x: x[1], reverse=True)[:n]


# ========== NEURAL MEMORY MESH ==========
class NeuralMemoryMesh:
    def __init__(self):
        self.nodes = {}
        self.total_activations = 0
        self.dream_engine = DreamEngine()

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
        node = self._find_or_create(content)
        node.activate(intensity)
        activated = {node.id: intensity}
        queue = deque([(node.id, intensity, 0)])
        visited = {node.id}
        while queue:
            cid, ci, depth = queue.popleft()
            if depth >= 3 or cid not in self.nodes:
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
                    if spread > 0.3:
                        queue.append((conn_id, spread, depth + 1))
        if self.total_activations % 100 == 0:
            self._decay()
            threading.Thread(target=self.dream_engine.dream, args=(self,), daemon=True).start()
        return activated

    def _find_or_create(self, content):
        norm = re.sub(r'[^\w\s]', '', content.lower().strip())
        for node in self.nodes.values():
            if re.sub(r'[^\w\s]', '', node.content.lower().strip()) == norm:
                return node
        return self.add_node(content)

    def _decay(self):
        for node in list(self.nodes.values()):
            node.decay()

    def query(self, question):
        activated = self.activate(question, 1.0)
        candidates = []
        for node_id, act in activated.items():
            if node_id in self.nodes:
                node = self.nodes[node_id]
                score = act * (2.0 if node.type in ["answer", "fact", "definition"] else 1.0)
                if node.fire_count > 0:
                    score *= (1 + math.log(node.fire_count + 1) * 0.15)
                if node.content != question:
                    candidates.append((score, node))
        candidates.sort(reverse=True, key=lambda x: x[0])
        return [{'content': n.content, 'score': round(s, 3), 'type': n.type, 'fires': n.fire_count} for s, n in candidates[:10]]

    def learn(self, question, answer):
        qn = self.add_node(question, "question")
        an = self.add_node(answer, "answer")
        qn.connect(an, 0.95)
        an.connect(qn, 0.95)
        return True

    def stats(self):
        return {'nodes': len(self.nodes), 'activations': self.total_activations, 'dreams': self.dream_engine.dream_count, 'insights': len(self.dream_engine.insights)}


# ========== MATH SOLVER ==========
class MathSolver:
    @staticmethod
    def solve(text):
        text = text.lower().strip()
        for w, s in [('plus','+'),('minus','-'),('times','*'),('multiplied by','*'),('divided by','/'),('power','**'),('squared','**2'),('cubed','**3'),('square root of','sqrt')]:
            text = text.replace(w, s)
        if 'sqrt' in text:
            match = re.search(r'sqrt\(?(\d+(?:\.\d+)?)\)?', text)
            if match:
                return round(math.sqrt(float(match.group(1))), 4)
        match = re.search(r'(\d+(?:\.\d+)?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)', text)
        if match:
            a, op, b = float(match.group(1)), match.group(2), float(match.group(3))
            ops = {'+': a+b, '-': a-b, '*': a*b, '/': a/b if b!=0 else None}
            if op in ops and ops[op] is not None:
                r = ops[op]
                return int(r) if r == int(r) else round(r, 4)
        return None


# ========== MAIN AI ENGINE ==========
class KeyGenAI:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.knowledge_dir = os.path.join(self.base_dir, "knowledge")
        self.collected_dir = os.path.join(self.knowledge_dir, "collected")
        self.mesh = NeuralMemoryMesh()
        self.math = MathSolver()
        self.empathy = EmpathyModule()
        self.intuition = IntuitionEngine()
        self.qa_cache = {}
        self.sentences = []
        self.history = deque(maxlen=50)
        self.greetings = {'hi','hello','hey','good morning','good afternoon','good evening','howdy','greetings','sup','yo','hola','heya','heyy','hii','helloo','morning','evening'}
        self.greet_responses = ["Hello! How can I help you?","Hi there! What would you like to know?","Hey! I'm ready to help!","Greetings! What can I do for you?","Welcome! Ask me anything!","Hello! I'm listening!","Hi! What's on your mind?"]
        os.makedirs(self.knowledge_dir, exist_ok=True)
        os.makedirs(self.collected_dir, exist_ok=True)
        self._load_all()

    def _load_all(self):
        print("Loading knowledge base...", flush=True)
        count = 0
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
                                        ntype = "fact" if re.search(r'\b(is|are|was|were|has|have)\b', sent, re.I) else "concept"
                                        self.mesh.add_node(sent, ntype)
                                        count += 1
                                for subj, obj in re.findall(r'([A-Za-z\s]{3,}?)\s+is\s+(?:a\s+|an\s+|the\s+)?([A-Za-z\s,]{3,}?)[.!]', text, re.IGNORECASE):
                                    q = f"what is {subj.strip().lower()}"
                                    a = f"{subj.strip()} is {obj.strip()}."
                                    self.qa_cache[q] = a
                        except: pass
        for jf in ['data.json', 'gk_knowledge.json']:
            try:
                fp = os.path.join(self.base_dir, jf)
                if os.path.exists(fp):
                    with open(fp, 'r') as f:
                        for item in json.load(f):
                            if 'q' in item and 'a' in item:
                                self.qa_cache[item['q'].lower()] = item['a']
                                self.mesh.learn(item['q'], item['a'])
            except: pass
        try:
            lf = os.path.join(self.knowledge_dir, "learned_knowledge.json")
            if os.path.exists(lf):
                with open(lf, 'r') as f:
                    for q, a in json.load(f).items():
                        self.qa_cache[q.lower()] = a
        except: pass
        print(f"Loaded: {len(self.qa_cache)} Q&A, {count} nodes, {len(self.sentences)} sentences", flush=True)

    def _save_learned(self):
        try:
            with open(os.path.join(self.knowledge_dir, "learned_knowledge.json"), 'w') as f:
                json.dump(self.qa_cache, f, indent=2)
        except: pass

    def get_response(self, user_input):
        if not user_input or not user_input.strip():
            return "Please ask me something!"
        raw = user_input.strip()
        low = raw.lower()
        emotion, intensity = self.empathy.detect(raw)
        
        # Greetings
        cleaned = low.rstrip('!.,? ')
        if cleaned in self.greetings or (len(low.split()) <= 2 and any(g in low for g in ['hi','hey','hello','yo','sup'])):
            return self.empathy.respond(emotion, random.choice(self.greet_responses))
        
        # Math
        if any(op in low for op in ['+','-','*','/','plus','minus','times','divided','square root','squared']):
            result = self.math.solve(raw)
            if result is not None:
                return str(result)
        
        # Learn
        if low.startswith("learn "):
            content = raw[6:].strip()
            for sep in [" : ", " = ", " -> ", " | "]:
                if sep in content:
                    parts = content.split(sep, 1)
                    if len(parts) == 2:
                        q, a = parts[0].strip(), parts[1].strip()
                        self.qa_cache[q.lower()] = a
                        self.mesh.learn(q, a)
                        self._save_learned()
                        return "✅ Learned successfully!"
            return "📝 Format: learn question : answer"
        
        # Commands
        if low == 'help':
            return "📋 Commands: help | status | time | date | calculate 5+3 | define <term> | search <query> | learn Q : A | dream | clear"
        if low == 'status':
            s = self.mesh.stats()
            return f"📊 Nodes: {s['nodes']} | Q&A: {len(self.qa_cache)} | Sentences: {len(self.sentences)} | Dreams: {s['dreams']} | Insights: {s['insights']}"
        if low == 'time':
            return f"🕐 {datetime.now().strftime('%H:%M:%S')}"
        if low == 'date':
            return f"📅 {datetime.now().strftime('%A, %B %d, %Y')}"
        if low == 'dream':
            insight = self.mesh.dream_engine.dream(self.mesh)
            return f"💭 {insight}" if insight else "💤 Dreaming... connections being processed."
        if low == 'clear':
            self.history.clear()
            return "🧹 Conversation cleared."
        if low.startswith("calculate "):
            result = self.math.solve(raw[10:])
            return f"🧮 {result}" if result is not None else "❌ Could not solve."
        if low.startswith("define "):
            term = raw[7:].strip().lower()
            q = f"what is {term}"
            if q in self.qa_cache:
                return self.qa_cache[q]
            for cq, ca in self.qa_cache.items():
                if term in cq:
                    return ca
            return f"❌ No definition for '{term}'."
        if low.startswith("search "):
            query = raw[7:].strip().lower()
            results = [s[:400] for s in self.sentences if query in s.lower()][:5]
            return "\n\n".join([f"📌 {r}" for r in results]) if results else "🔍 No results found."
        
        # Exact Q&A match
        if low in self.qa_cache:
            return self.qa_cache[low]
        
        # Fuzzy Q&A match
        best, best_score = None, 0
        for q, a in self.qa_cache.items():
            s = SequenceMatcher(None, low, q).ratio()
            if s > best_score and s > 0.6:
                best_score, best = s, a
        if best:
            return best
        
        # Neural mesh query
        results = self.mesh.query(raw)
        if results and results[0]['score'] > 0.08:
            ans = results[0]['content']
            if len(ans) > 600:
                ans = ans[:600].rsplit(' ', 1)[0] + "..."
            return self.empathy.respond(emotion, ans)
        
        # Sentence search
        if self.sentences:
            qw = set(re.findall(r'\b\w+\b', low))
            scored = [(len(qw & set(re.findall(r'\b\w+\b', s.lower()))) / max(len(qw),1), s) for s in self.sentences]
            scored = [(s, t) for s, t in scored if s > 0.15]
            if scored:
                scored.sort(reverse=True, key=lambda x: x[0])
                return scored[0][1][:500]
        
        # Intuition
        intuitive = self.intuition.intuit(raw, self.qa_cache, self.sentences)
        if intuitive:
            return intuitive
        
        return "🤔 I don't know that yet. You can teach me: learn question : answer"


# ========== FLASK APP ==========
app = Flask(__name__)
ai = KeyGenAI()

@app.route('/')
def index():
    try:
        return send_from_directory('.', 'index.html')
    except:
        return jsonify({'status': 'running', 'name': 'KeyGen.ai NMM', 'endpoints': ['/health', '/chat', '/stats']})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'nodes': ai.mesh.stats()['nodes']})

@app.route('/stats')
def stats():
    s = ai.mesh.stats()
    return jsonify({'qa_cache': len(ai.qa_cache), 'sentences': len(ai.sentences), 'nodes': s['nodes'], 'activations': s['activations'], 'dreams': s['dreams'], 'insights': s['insights']})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '')
    response = ai.get_response(message)
    return jsonify({'response': response})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
