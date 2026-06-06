"""
KeyGen.ai - Neural Memory Mesh (NMM) Engine
Revolutionary self-organizing knowledge system
Invention: Dynamic Synaptic Knowledge Web with Temporal Reinforcement
"""

import re
import random
import json
import os
import math
import time
import hashlib
from collections import defaultdict, Counter, deque
from http.server import HTTPServer, BaseHTTPRequestHandler
from difflib import SequenceMatcher
from datetime import datetime

# ========== NEURAL MEMORY MESH - THE INVENTION ==========

class MemoryNode:
    """A single node in the neural memory mesh - like a neuron."""
    
    def __init__(self, content, node_type="concept"):
        self.id = hashlib.md5(content.encode()).hexdigest()[:12]
        self.content = content
        self.type = node_type  # concept, fact, question, answer, definition
        self.connections = defaultdict(float)  # node_id -> strength
        self.activation = 0.0  # Current activation level
        self.resting_potential = 0.1  # Base activation
        self.fire_count = 0  # How many times activated
        self.last_fired = 0  # Last activation time
        self.created_at = time.time()
        self.decay_rate = 0.001  # How fast connections decay
        self.reinforcement_threshold = 0.3  # When to strengthen connections
        
    def activate(self, intensity=1.0):
        """Activate this node - like a neuron firing."""
        self.activation = min(1.0, self.resting_potential + intensity)
        self.fire_count += 1
        self.last_fired = time.time()
        
        # Strengthen connections on repeated firing
        if self.fire_count > 3:
            for conn_id in list(self.connections.keys()):
                self.connections[conn_id] *= 1.01  # 1% reinforcement
        
        return self.activation
    
    def connect(self, other_node, strength=0.1):
        """Create or strengthen connection to another node."""
        current = self.connections.get(other_node.id, 0)
        self.connections[other_node.id] = min(1.0, current + strength)
    
    def decay(self):
        """Natural decay of unused connections."""
        for conn_id in list(self.connections.keys()):
            self.connections[conn_id] *= (1 - self.decay_rate)
            # Remove very weak connections
            if self.connections[conn_id] < 0.01:
                del self.connections[conn_id]
    
    def get_strongest_connections(self, n=5):
        """Get the strongest connected nodes."""
        sorted_conns = sorted(self.connections.items(), key=lambda x: x[1], reverse=True)
        return sorted_conns[:n]


class SynapticPathway:
    """A pathway between concepts - like a neural synapse."""
    
    def __init__(self, source, target):
        self.source_id = source.id if hasattr(source, 'id') else source
        self.target_id = target.id if hasattr(target, 'id') else target
        self.strength = 0.1
        self.traversal_count = 0
        self.created_at = time.time()
        self.last_traversed = 0
        
    def traverse(self):
        """Strengthen this pathway when used."""
        self.traversal_count += 1
        self.last_traversed = time.time()
        self.strength = min(1.0, self.strength * 1.05 + 0.01)
        return self.strength


class TemporalMemory:
    """Remembers the sequence and timing of activations."""
    
    def __init__(self, capacity=100):
        self.activation_history = deque(maxlen=capacity)
        self.sequence_patterns = defaultdict(list)
        
    def record(self, node_id, context=None):
        """Record a node activation with timestamp."""
        entry = {
            'node_id': node_id,
            'timestamp': time.time(),
            'context': context
        }
        self.activation_history.append(entry)
    
    def get_recent_activations(self, n=10):
        """Get the most recently activated nodes."""
        recent = list(self.activation_history)[-n:]
        return [r['node_id'] for r in recent]
    
    def find_pattern(self, node_sequence):
        """Find if a sequence pattern exists in memory."""
        seq_key = tuple(node_sequence)
        if seq_key in self.sequence_patterns:
            return self.sequence_patterns[seq_key]
        return None


class NeuralMemoryMesh:
    """
    THE INVENTION: Neural Memory Mesh (NMM)
    
    A self-organizing knowledge network that:
    1. Creates dynamic connections between concepts
    2. Strengthens pathways based on usage frequency
    3. Decays unused connections naturally
    4. Builds temporal sequences of thought patterns
    5. Activates related concepts through spreading activation
    6. Self-heals by reinforcing successful pathways
    """
    
    def __init__(self):
        self.nodes = {}  # id -> MemoryNode
        self.pathways = {}  # (source_id, target_id) -> SynapticPathway
        self.temporal = TemporalMemory()
        self.concept_clusters = defaultdict(set)  # Groups of related concepts
        self.activation_threshold = 0.2
        self.spread_factor = 0.7  # How much activation spreads
        self.total_activations = 0
        
    def add_node(self, content, node_type="concept"):
        """Add a new node to the mesh."""
        node = MemoryNode(content, node_type)
        
        # Check if similar node exists
        for existing_id, existing_node in self.nodes.items():
            similarity = SequenceMatcher(None, 
                node.content.lower(), 
                existing_node.content.lower()
            ).ratio()
            
            if similarity > 0.8:
                # Merge with existing node
                existing_node.fire_count += 1
                return existing_node
        
        self.nodes[node.id] = node
        
        # Auto-connect to related concepts
        self._auto_connect(node)
        
        return node
    
    def _auto_connect(self, node):
        """Automatically create connections to related concepts."""
        words = set(re.findall(r'\b\w+\b', node.content.lower()))
        
        for existing_id, existing_node in self.nodes.items():
            if existing_id == node.id:
                continue
            
            existing_words = set(re.findall(r'\b\w+\b', existing_node.content.lower()))
            
            # Calculate word overlap
            overlap = len(words & existing_words)
            total = len(words | existing_words)
            
            if total > 0:
                similarity = overlap / total
                if similarity > 0.1:
                    # Create bidirectional connection
                    strength = similarity * 0.5
                    node.connect(existing_node, strength)
                    existing_node.connect(node, strength)
                    
                    # Create pathway
                    pathway = SynapticPathway(node, existing_node)
                    pathway.strength = strength
                    self.pathways[(node.id, existing_node.id)] = pathway
                    
                    # Group into clusters
                    cluster_key = min(node.id, existing_node.id)
                    self.concept_clusters[cluster_key].add(node.id)
                    self.concept_clusters[cluster_key].add(existing_node.id)
    
    def activate(self, content, context=None, intensity=1.0):
        """
        Activate the mesh with content - MAIN ENTRY POINT.
        Returns activated nodes and their strengths.
        """
        self.total_activations += 1
        
        # Find or create node
        node = self._find_or_create_node(content)
        
        # Activate the primary node
        node.activate(intensity)
        self.temporal.record(node.id, context)
        
        # Spread activation to connected nodes
        activated = self._spread_activation(node.id, intensity)
        
        # Apply temporal decay to unused nodes
        if self.total_activations % 100 == 0:
            self._global_decay()
        
        # Reinforce pathways
        self._reinforce_pathways()
        
        return activated
    
    def _find_or_create_node(self, content):
        """Find existing node or create new one."""
        # Normalize content
        normalized = content.lower().strip()
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Search for exact match
        for node in self.nodes.values():
            if node.content.lower().strip() == normalized:
                return node
        
        # Create new node
        return self.add_node(content)
    
    def _spread_activation(self, source_id, intensity):
        """
        Spread activation through the network - like neural propagation.
        This is the core innovation: activation cascades through the mesh.
        """
        activated = {source_id: intensity}
        queue = deque([(source_id, intensity)])
        visited = {source_id}
        
        while queue:
            current_id, current_intensity = queue.popleft()
            
            # Get the current node
            if current_id not in self.nodes:
                continue
            
            node = self.nodes[current_id]
            
            # Get connections sorted by strength
            for connected_id, strength in node.get_strongest_connections(10):
                if connected_id in visited:
                    continue
                
                # Calculate spread intensity
                spread_intensity = current_intensity * self.spread_factor * strength
                
                if spread_intensity > self.activation_threshold:
                    # Activate connected node
                    if connected_id in self.nodes:
                        self.nodes[connected_id].activate(spread_intensity)
                        self.temporal.record(connected_id)
                        
                    activated[connected_id] = spread_intensity
                    visited.add(connected_id)
                    
                    # Continue spreading if intensity is high enough
                    if spread_intensity > self.activation_threshold * 2:
                        queue.append((connected_id, spread_intensity))
        
        return activated
    
    def _reinforce_pathways(self):
        """Strengthen pathways between frequently co-activated nodes."""
        recent = self.temporal.get_recent_activations(20)
        
        for i in range(len(recent)):
            for j in range(i+1, len(recent)):
                pathway_key = (recent[i], recent[j])
                reverse_key = (recent[j], recent[i])
                
                if pathway_key in self.pathways:
                    self.pathways[pathway_key].traverse()
                elif reverse_key in self.pathways:
                    self.pathways[reverse_key].traverse()
    
    def _global_decay(self):
        """Apply global decay to all unused connections."""
        for node in self.nodes.values():
            node.decay()
    
    def query(self, question, depth=3):
        """
        Query the mesh for an answer.
        Uses spreading activation to find the most relevant knowledge.
        """
        # Activate the question in the mesh
        question_node = self.add_node(question, "question")
        activated = self.activate(question, context="query")
        
        # Collect activated nodes
        candidates = []
        for node_id, activation in activated.items():
            if node_id in self.nodes:
                node = self.nodes[node_id]
                # Prefer answer-type nodes and highly activated nodes
                score = activation * (1.5 if node.type in ["answer", "fact", "definition"] else 1.0)
                score *= (1 + math.log(node.fire_count + 1) * 0.1)  # Bonus for frequently used
                candidates.append((score, node))
        
        # Sort by score
        candidates.sort(reverse=True, key=lambda x: x[0])
        
        # Return top results
        results = []
        for score, node in candidates[:10]:
            if node.content != question:  # Don't return the question itself
                results.append({
                    'content': node.content,
                    'score': round(score, 3),
                    'type': node.type,
                    'activations': node.fire_count
                })
        
        return results
    
    def learn(self, question, answer):
        """Learn a question-answer pair by creating strong connections."""
        q_node = self.add_node(question, "question")
        a_node = self.add_node(answer, "answer")
        
        # Create very strong connection
        q_node.connect(a_node, 0.9)
        a_node.connect(q_node, 0.9)
        
        # Create pathway
        pathway = SynapticPathway(q_node, a_node)
        pathway.strength = 0.9
        pathway.traversal_count = 10  # Pre-strengthened
        self.pathways[(q_node.id, a_node.id)] = pathway
        
        # Also connect related concepts
        self._auto_connect(a_node)
        
        return True
    
    def get_stats(self):
        """Get mesh statistics."""
        return {
            'total_nodes': len(self.nodes),
            'total_pathways': len(self.pathways),
            'total_activations': self.total_activations,
            'clusters': len(self.concept_clusters),
            'avg_connections': sum(len(n.connections) for n in self.nodes.values()) / max(len(self.nodes), 1)
        }


# ========== ULTRA MATH SOLVER ==========
class UltraMathSolver:
    """Solves any math expression."""
    
    @staticmethod
    def solve(text):
        text = text.lower().strip()
        
        # Replace words
        replacements = {
            'plus': '+', 'minus': '-', 'times': '*', 'multiplied by': '*',
            'divided by': '/', 'into': '*', 'x': '*', '×': '*', '÷': '/',
            'power': '**', 'raised to': '**', 'square root of': 'sqrt(',
            'cube root of': 'cbrt(', 'mod': '%', 'modulo': '%',
            'half of': '*0.5', 'double of': '*2', 'triple of': '*3',
        }
        for word, symbol in replacements.items():
            text = text.replace(word, symbol)
        
        # Handle square root
        sqrt_match = re.search(r'sqrt\((\d+(?:\.\d+)?)\)', text)
        if sqrt_match:
            return round(math.sqrt(float(sqrt_match.group(1))), 4)
        
        # Handle basic operations
        match = re.search(r'(\d+(?:\.\d+)?)\s*([+\-*/%])\s*(\d+(?:\.\d+)?)', text)
        if match:
            a, op, b = float(match.group(1)), match.group(2), float(match.group(3))
            ops = {'+': lambda x,y: x+y, '-': lambda x,y: x-y, 
                   '*': lambda x,y: x*y, '/': lambda x,y: x/y if y!=0 else None,
                   '%': lambda x,y: x%y if y!=0 else None}
            if op in ops:
                result = ops[op](a, b)
                if result is not None:
                    return int(result) if result == int(result) else round(result, 4)
        
        # Try evaluating expression
        try:
            safe = re.sub(r'[^0-9+\-*/.() ]', '', text)
            if safe and any(op in safe for op in '+-*/'):
                result = eval(safe)
                return int(result) if result == int(result) else round(result, 4)
        except:
            pass
        
        return None


# ========== MAIN AI WITH NEURAL MEMORY MESH ==========
class KeyGenAI:
    def __init__(self, knowledge_dir="knowledge"):
        self.name = "KeyGen.ai"
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.knowledge_dir = os.path.join(self.script_dir, knowledge_dir)
        self.collected_dir = os.path.join(self.knowledge_dir, "collected")
        
        # THE INVENTION
        self.mesh = NeuralMemoryMesh()
        self.math_solver = UltraMathSolver()
        
        # Quick lookup
        self.qa_cache = {}
        
        # Greetings
        self.greeting_responses = [
            "Hello! 👋 How can I help?",
            "Hi there! 😊 Ask me anything!",
            "Hey! ✨ Ready to answer!",
            "Greetings! 🌟 What can I do for you?",
            "Hello! 🚀 I'm listening!",
            "Hi! 💫 What's on your mind?",
            "Welcome! 🤖 How can I assist?",
        ]
        
        os.makedirs(self.knowledge_dir, exist_ok=True)
        os.makedirs(self.collected_dir, exist_ok=True)
        
        self.load_knowledge()
    
    def load_knowledge(self):
        """Load all knowledge into the Neural Memory Mesh."""
        print("🧠 Loading knowledge into Neural Memory Mesh...")
        
        # Load text files
        for directory in [self.knowledge_dir, self.collected_dir]:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    if filename.endswith('.txt'):
                        filepath = os.path.join(directory, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                text = f.read()
                                if text.strip():
                                    # Add sentences as nodes
                                    sentences = re.split(r'(?<=[.!?])\s+', text)
                                    for sent in sentences:
                                        sent = sent.strip()
                                        if len(sent) > 10:
                                            # Detect type
                                            node_type = "fact" if re.search(r'\b(is|are|was|were|has|have)\b', sent, re.I) else "concept"
                                            self.mesh.add_node(sent, node_type)
                                    
                                    # Extract definitions
                                    defs = re.findall(r'([A-Za-z\s]+?)\s+is\s+(?:a\s+|an\s+|the\s+)?([A-Za-z\s,]+?)[.!]', text, re.IGNORECASE)
                                    for subj, obj in defs:
                                        if len(subj.strip()) > 3 and len(obj.strip()) > 3:
                                            q = f"what is {subj.strip()}"
                                            a = f"{subj.strip()} is {obj.strip()}."
                                            self.mesh.learn(q, a)
                                            self.qa_cache[q.lower()] = a
                        except:
                            pass
        
        # Load JSON files
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
        
        # Load learned knowledge
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
    
    def is_greeting(self, text):
        """Check for greetings."""
        text = text.lower().strip().rstrip('!.,? ')
        greetings = {'hi', 'hello', 'hey', 'good morning', 'good afternoon', 
                    'good evening', 'howdy', 'greetings', 'sup', 'yo', 'hola',
                    'bonjour', 'heya', 'heyy', 'hii', 'helloo', 'morning', 'evening'}
        if text in greetings:
            return True
        if len(text.split()) <= 2 and any(g in text for g in ['hi', 'hey', 'hello', 'yo', 'sup']):
            return True
        return False
    
    def is_math(self, text):
        """Check for math expressions."""
        return any(op in text.lower() for op in ['+', '-', '*', '/', '×', '÷', 'plus', 'minus', 
                                                  'times', 'divided', 'square root', 'power'])
    
    def get_response(self, user_input):
        if not user_input or not user_input.strip():
            return "Please ask me something! 😊"
        
        raw = user_input.strip()
        low = raw.lower()
        
        # Greetings
        if self.is_greeting(raw):
            return random.choice(self.greeting_responses)
        
        # Math
        if self.is_math(raw):
            result = self.math_solver.solve(raw)
            if result is not None:
                return f"{result}"
        
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
                        # Save
                        try:
                            with open(os.path.join(self.knowledge_dir, "learned_knowledge.json"), 'w') as f:
                                json.dump(self.qa_cache, f, indent=2)
                        except:
                            pass
                        return "✅ Knowledge absorbed into Neural Memory Mesh!"
            return "Format: learn question : answer"
        
        # Status
        if low == "mesh status":
            stats = self.mesh.get_stats()
            return f"🧠 Neural Mesh: {stats['total_nodes']} nodes | {stats['total_pathways']} pathways | {stats['total_activations']} activations"
        
        # Quick cache lookup
        if low in self.qa_cache:
            return self.qa_cache[low]
        
        # Cache lookup with fuzzy matching
        best_match = None
        best_score = 0
        for cached_q, cached_a in self.qa_cache.items():
            score = SequenceMatcher(None, low, cached_q).ratio()
            if score > best_score and score > 0.7:
                best_score = score
                best_match = cached_a
        
        if best_match:
            return best_match
        
        # Query the Neural Memory Mesh
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
                return answer
        
        return "I don't know that yet. Teach me: learn question : answer"


# ========== WEB SERVER ==========
class ChatHandler(BaseHTTPRequestHandler):
    bot = None
    
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
                self.wfile.write(b"<h1>KeyGen.ai NMM</h1>")
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'healthy', 'engine': 'Neural Memory Mesh'}).encode())
        elif self.path == '/mesh-stats':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(self.bot.mesh.get_stats()).encode())
    
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
    port = int(os.environ.get("PORT", 10000))
    ChatHandler.bot = KeyGenAI()
    server = HTTPServer(('0.0.0.0', port), ChatHandler)
    print(f"""
╔══════════════════════════════════════════╗
║   🧠 KeyGen.ai - Neural Memory Mesh     ║
║   Revolutionary Self-Organizing AI      ║
║   http://0.0.0.0:{port}                  ║
╚══════════════════════════════════════════╝
    """)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == "__main__":
    run_server()
