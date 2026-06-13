"""
KeyGen.ai - Neural Memory Mesh (NMM) Engine
Revolutionary self-organizing knowledge system
Fixed port detection for Render + Brain-like functions
"""

import re
import random
import json
import os
import math
import time
import hashlib
import socket
import sys
from collections import defaultdict, deque, OrderedDict
from http.server import HTTPServer, BaseHTTPRequestHandler
from difflib import SequenceMatcher
from datetime import datetime

# ========== FORCE PORT DETECTION ==========
def get_port():
    """Force port detection for Render."""
    port = os.environ.get("PORT")
    if port:
        print(f"Using Render PORT: {port}")
        return int(port)
    port = os.environ.get("RENDER_PORT")
    if port:
        print(f"Using RENDER_PORT: {port}")
        return int(port)
    for p in [10000, 8080, 5000, 3000, 8000]:
        if not is_port_in_use(p):
            print(f"Using available port: {p}")
            return p
    port = find_free_port()
    print(f"Using free port: {port}")
    return port

def is_port_in_use(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.bind(('0.0.0.0', port))
            return False
    except:
        return True

def find_free_port():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', 0))
            return s.getsockname()[1]
    except:
        return 10000


# ========== INVENTION 1: QUANTUM MEMORY CELL ==========
class QuantumMemoryCell:
    """
    INVENTION: Quantum-like superposition memory
    Each cell exists in multiple states simultaneously until queried.
    """
    def __init__(self, content):
        self.content = content
        self.states = defaultdict(float)  # Multiple possible meanings
        self.entangled_with = set()  # Connected cells
        self.collapse_count = 0
        self.superposition_strength = 1.0
        
    def superpose(self, meaning, weight=0.5):
        """Add a possible meaning to superposition."""
        self.states[meaning] = weight
        self.superposition_strength = sum(self.states.values())
        
    def collapse(self, context=None):
        """Collapse to most likely meaning based on context."""
        self.collapse_count += 1
        if not self.states:
            return self.content
        if context:
            for state, weight in self.states.items():
                if context in state:
                    self.states[state] *= 1.5
        best = max(self.states.items(), key=lambda x: x[1])
        return best[0] if best[1] > 0.3 else self.content


# ========== INVENTION 2: DREAM ENGINE ==========
class DreamEngine:
    """
    INVENTION: Simulates human-like dreaming
    During idle time, randomly connects memories to create new insights.
    """
    def __init__(self):
        self.dreams = deque(maxlen=50)
        self.insights = []
        self.is_dreaming = False
        
    def dream(self, mesh):
        """Generate random connections between memories."""
        if len(mesh.nodes) < 3:
            return None
            
        nodes = list(mesh.nodes.values())
        n1, n2, n3 = random.sample(nodes, min(3, len(nodes)))
        
        dream_content = f"{n1.content[:50]} + {n2.content[:50]} = ?"
        
        # Check if combination creates new insight
        words1 = set(re.findall(r'\b\w+\b', n1.content.lower()))
        words2 = set(re.findall(r'\b\w+\b', n2.content.lower()))
        words3 = set(re.findall(r'\b\w+\b', n3.content.lower()))
        
        common = words1 & words2 & words3
        if common:
            insight = f"Dream insight: {', '.join(list(common)[:3])} connect multiple concepts"
            self.insights.append(insight)
            return insight
            
        self.dreams.append(dream_content)
        return None


# ========== INVENTION 3: INTUITION GENERATOR ==========
class IntuitionGenerator:
    """
    INVENTION: Gut-feeling answer generator
    Makes educated guesses when exact knowledge is missing.
    """
    def __init__(self):
        self.intuition_score = 0
        self.successful_guesses = 0
        self.total_guesses = 0
        
    def intuit(self, question, mesh, qa_cache):
        """Generate an intuitive answer."""
        self.total_guesses += 1
        
        # Extract key concepts from question
        concepts = re.findall(r'\b\w{4,}\b', question.lower())
        candidates = []
        
        # Search for partial matches
        for cached_q, cached_a in qa_cache.items():
            score = 0
            for concept in concepts:
                if concept in cached_q:
                    score += 1
            if score > 0:
                candidates.append((score, cached_a))
        
        if candidates:
            candidates.sort(reverse=True, key=lambda x: x[0])
            guess = candidates[0][1]
            
            # Check if guess is reasonable
            if len(guess) > 20:
                self.successful_guesses += 1
                return f"I think... {guess}"
        
        # Pattern completion
        question_words = set(re.findall(r'\b\w+\b', question.lower()))
        for node_id, node in mesh.nodes.items():
            if node.type in ["fact", "answer"]:
                node_words = set(re.findall(r'\b\w+\b', node.content.lower()))
                overlap = len(question_words & node_words)
                if overlap >= 3:
                    return f"Possibly... {node.content[:300]}"
        
        return None


# ========== INVENTION 4: EMPATHY MODULE ==========
class EmpathyModule:
    """
    INVENTION: Emotional understanding without training data
    Detects 12 emotional states from text patterns.
    """
    def __init__(self):
        self.emotion_patterns = {
            'joy': [r'\b(happy|glad|wonderful|amazing|love|great|awesome|excited|yay)\b', r'!{2,}', r'😊|🎉|✨|💫'],
            'sadness': [r'\b(sad|unhappy|depressed|crying|upset|heartbroken|miserable)\b', r'😢|💔|😔'],
            'anger': [r'\b(angry|furious|mad|annoyed|frustrated|rage|hate)\b', r'[A-Z]{2,}', r'😠|😡|🤬'],
            'fear': [r'\b(scared|afraid|terrified|frightened|nervous|anxious|worried)\b', r'😨|😰|😱'],
            'surprise': [r'\b(wow|omg|unbelievable|incredible|surprising|shocking)\b', r'😮|😲|🤯'],
            'curiosity': [r'\b(curious|wondering|interesting|fascinating|tell me|explain)\b', r'\?{2,}'],
            'confusion': [r'\b(confused|puzzled|unclear|dont understand|what do you mean)\b', r'🤔|😕'],
            'gratitude': [r'\b(thanks|thank you|grateful|appreciate|thankful)\b', r'🙏'],
            'hope': [r'\b(hope|wish|dream|aspire|looking forward|someday)\b', r'🌟|🌈'],
            'determination': [r'\b(must|need to|have to|will do|going to|determined)\b', r'💪|🎯'],
            'loneliness': [r'\b(alone|lonely|nobody|no one|isolated|by myself)\b', r'😔|💭'],
            'love': [r'\b(love|adore|cherish|devotion|affection|care for)\b', r'❤️|💕|💗'],
        }
        self.emotion_memory = deque(maxlen=50)
        
    def detect(self, text):
        """Detect primary and secondary emotions."""
        text_lower = text.lower()
        detected = {}
        
        for emotion, patterns in self.emotion_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                score += len(matches)
            if score > 0:
                detected[emotion] = score
        
        if not detected:
            return 'neutral', 0
        
        primary = max(detected.items(), key=lambda x: x[1])
        self.emotion_memory.append(primary[0])
        
        return primary[0], primary[1]
    
    def get_emotional_state(self):
        """Get current emotional understanding."""
        if not self.emotion_memory:
            return 'neutral'
        states = list(self.emotion_memory)
        return max(set(states), key=states.count)
    
    def respond_with_empathy(self, emotion, base_response):
        """Add emotional intelligence to response."""
        empathy_prefixes = {
            'joy': "I'm happy to hear that! ",
            'sadness': "I understand that can be difficult. ",
            'anger': "I hear your frustration. ",
            'fear': "It's okay to feel that way. ",
            'surprise': "That is surprising! ",
            'curiosity': "Great question! ",
            'confusion': "Let me clarify. ",
            'gratitude': "You're welcome! ",
            'hope': "That's a wonderful aspiration! ",
            'determination': "I admire your determination! ",
            'loneliness': "I'm here with you. ",
            'love': "That's beautiful! ",
        }
        prefix = empathy_prefixes.get(emotion, "")
        return prefix + base_response


# ========== INVENTION 5: MEMORY PALACE ==========
class MemoryPalace:
    """
    INVENTION: Spatial memory organization
    Organizes memories in virtual rooms for better recall.
    """
    def __init__(self):
        self.rooms = {
            'science': defaultdict(list),
            'history': defaultdict(list),
            'technology': defaultdict(list),
            'philosophy': defaultdict(list),
            'daily': defaultdict(list),
            'personal': defaultdict(list),
            'misc': defaultdict(list),
        }
        
    def categorize(self, content):
        """Categorize content into appropriate room."""
        content_lower = content.lower()
        
        science_words = {'physics', 'chemistry', 'biology', 'math', 'science', 'quantum', 'atom', 'molecule', 'cell', 'dna', 'gene', 'evolution', 'gravity', 'energy', 'force'}
        history_words = {'war', 'king', 'queen', 'empire', 'ancient', 'century', 'revolution', 'civilization', 'dynasty', 'president', 'kingdom'}
        tech_words = {'computer', 'software', 'algorithm', 'ai', 'machine', 'code', 'program', 'data', 'network', 'internet', 'digital', 'robot'}
        philosophy_words = {'meaning', 'existence', 'ethics', 'moral', 'consciousness', 'reality', 'truth', 'knowledge', 'wisdom', 'soul', 'mind'}
        
        scores = {
            'science': sum(1 for w in science_words if w in content_lower),
            'history': sum(1 for w in history_words if w in content_lower),
            'technology': sum(1 for w in tech_words if w in content_lower),
            'philosophy': sum(1 for w in philosophy_words if w in content_lower),
        }
        
        best_room = max(scores.items(), key=lambda x: x[1])
        if best_room[1] > 0:
            return best_room[0]
        return 'misc'
    
    def store(self, content):
        """Store memory in appropriate room."""
        room = self.categorize(content)
        key = hashlib.md5(content.encode()).hexdigest()[:8]
        self.rooms[room][key] = {
            'content': content,
            'timestamp': time.time(),
            'access_count': 1
        }
        return room, key
    
    def recall(self, query, room=None):
        """Recall memories from specific or all rooms."""
        results = []
        rooms_to_search = [room] if room else self.rooms.keys()
        
        for r in rooms_to_search:
            for key, memory in self.rooms[r].items():
                similarity = SequenceMatcher(None, query.lower(), memory['content'].lower()).ratio()
                if similarity > 0.2:
                    memory['access_count'] += 1
                    results.append((similarity, memory['content'], r))
        
        results.sort(reverse=True, key=lambda x: x[0])
        return results[:10]


# ========== CORE MEMORY NODE ==========
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
        self.quantum_cell = QuantumMemoryCell(content)

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
                cluster_key = min(node.id, existing_node.id)
                self.concept_clusters[cluster_key].add(node.id)
                self.concept_clusters[cluster_key].add(existing_node.id)

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
                        self.temporal.append({'node_id': connected_id, 'timestamp': time.time()})
                    activated[connected_id] = spread_intensity
                    visited.add(connected_id)
        return activated

    def _global_decay(self):
        for node in list(self.nodes.values()):
            node.decay()
            if node.fire_count == 0 and time.time() - node.created_at > 3600:
                del self.nodes[node.id]

    def query(self, question):
        self.add_node(question, "question")
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
            'clusters': len(self.concept_clusters),
            'palace_rooms': {k: len(v) for k, v in self.memory_palace.rooms.items()},
            'dreams': len(self.dream_engine.dreams),
            'insights': len(self.dream_engine.insights),
        }


# ========== MATH SOLVER ==========
class UltraMathSolver:
    @staticmethod
    def solve(text):
        text = text.lower().strip()
        replacements = {
            'plus': '+', 'minus': '-', 'times': '*', 'multiplied by': '*',
            'divided by': '/', 'into': '*', 'power': '**', 'raised to': '**',
            'square root of': 'sqrt(', 'mod': '%', 'half of': '*0.5',
            'double of': '*2', 'triple of': '*3', 'squared': '**2', 'cubed': '**3'
        }
        for word, symbol in replacements.items():
            text = text.replace(word, symbol)

        sqrt_match = re.search(r'sqrt\((\d+(?:\.\d+)?)\)', text)
        if sqrt_match:
            return round(math.sqrt(float(sqrt_match.group(1))), 4)

        match = re.search(r'(\d+(?:\.\d+)?)\s*([+\-*/%])\s*(\d+(?:\.\d+)?)', text)
        if match:
            a, op, b = float(match.group(1)), match.group(2), float(match.group(3))
            ops = {
                '+': lambda x, y: x + y, '-': lambda x, y: x - y,
                '*': lambda x, y: x * y,
                '/': lambda x, y: x / y if y != 0 else None,
                '%': lambda x, y: x % y if y != 0 else None
            }
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


# ========== MAIN AI ==========
class KeyGenAI:
    def __init__(self, knowledge_dir="knowledge"):
        self.name = "KeyGen.ai"
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.knowledge_dir = os.path.join(self.script_dir, knowledge_dir)
        self.collected_dir = os.path.join(self.knowledge_dir, "collected")

        self.mesh = NeuralMemoryMesh()
        self.math_solver = UltraMathSolver()
        self.empathy = EmpathyModule()
        self.intuition = IntuitionGenerator()
        self.qa_cache = {}
        self.commands = {}
        self.conversation_history = deque(maxlen=30)

        self.greeting_responses = [
            "Hello! How can I help?",
            "Hi there! Ask me anything!",
            "Hey! Ready to answer!",
            "Greetings! What can I do for you?",
            "Hello! I'm listening!",
            "Hi! What's on your mind?",
            "Welcome! How can I assist?",
        ]

        self._register_commands()
        os.makedirs(self.knowledge_dir, exist_ok=True)
        os.makedirs(self.collected_dir, exist_ok=True)
        self.load_knowledge()

    def _register_commands(self):
        self.commands = {
            'help': self._cmd_help,
            'status': self._cmd_status,
            'dream': self._cmd_dream,
            'intuit': self._cmd_intuit,
            'time': self._cmd_time,
            'date': self._cmd_date,
            'calculate': self._cmd_calculate,
            'define': self._cmd_define,
            'search': self._cmd_search,
            'remember': self._cmd_remember,
            'clear': self._cmd_clear,
            'palace': self._cmd_palace,
        }

    def load_knowledge(self):
        print("Loading knowledge...")
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
        print(f"Mesh: {stats['total_nodes']} nodes loaded")

    # Commands
    def _cmd_help(self, args=None):
        return "Commands: help | status | dream | intuit | time | date | calculate <expr> | define <term> | search <query> | remember <fact> | palace | clear"

    def _cmd_status(self, args=None):
        stats = self.mesh.get_stats()
        return f"Nodes: {stats['total_nodes']} | Pathways: {stats['total_pathways']} | Dreams: {stats['dreams']} | Insights: {stats['insights']} | Cache: {len(self.qa_cache)}"

    def _cmd_dream(self, args=None):
        insight = self.mesh.dream_engine.dream(self.mesh)
        if insight:
            return f"Dream insight: {insight}"
        return "Dreaming... connections being made."

    def _cmd_intuit(self, args=None):
        if not args:
            return "Usage: intuit <question>"
        result = self.intuition.intuit(args, self.mesh, self.qa_cache)
        return result if result else "My intuition fails me on this one."

    def _cmd_time(self, args=None):
        return datetime.now().strftime('%H:%M:%S')

    def _cmd_date(self, args=None):
        return datetime.now().strftime('%A, %B %d, %Y')

    def _cmd_calculate(self, args=None):
        if not args:
            return "Usage: calculate <expression>"
        result = self.math_solver.solve(args)
        return str(result) if result is not None else "Could not solve."

    def _cmd_define(self, args=None):
        if not args:
            return "Usage: define <term>"
        results = self.mesh.query(f"what is {args}")
        return results[0]['content'] if results else f"No definition for '{args}'."

    def _cmd_search(self, args=None):
        if not args:
            return "Usage: search <query>"
        results = self.mesh.query(args)
        return "\n".join([f"- {r['content'][:200]}" for r in results[:5]]) if results else "No results."

    def _cmd_remember(self, args=None):
        if not args:
            return "Usage: remember <fact>"
        self.mesh.add_node(args, "fact")
        return f"Remembered."

    def _cmd_clear(self, args=None):
        self.conversation_history.clear()
        return "Context cleared."

    def _cmd_palace(self, args=None):
        stats = self.mesh.get_stats()
        rooms = stats.get('palace_rooms', {})
        return "\n".join([f"{k}: {v} memories" for k, v in rooms.items()])

    # Helpers
    def is_greeting(self, text):
        text = text.lower().strip().rstrip('!.,? ')
        greetings = {'hi', 'hello', 'hey', 'good morning', 'good afternoon',
                     'good evening', 'howdy', 'greetings', 'sup', 'yo', 'hola',
                     'bonjour', 'heya', 'heyy', 'hii', 'helloo', 'morning', 'evening'}
        return text in greetings or (len(text.split()) <= 2 and any(g in text for g in ['hi', 'hey', 'hello', 'yo', 'sup']))

    def is_math(self, text):
        return any(op in text.lower() for op in ['+', '-', '*', '/', 'plus', 'minus', 'times', 'divided', 'square root'])

    def is_command(self, text):
        first_word = text.lower().split()[0] if text.split() else ""
        return first_word in self.commands

    def clean_answer(self, text):
        if len(text) > 600:
            text = text[:600].rsplit(' ', 1)[0] + "..."
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        if text and text[-1] not in '.!?':
            text += '.'
        return text

    def get_response(self, user_input):
        if not user_input or not user_input.strip():
            return "Please ask me something!"

        raw = user_input.strip()
        low = raw.lower()

        # Detect emotion
        emotion, intensity = self.empathy.detect(raw)

        # Commands
        if self.is_command(raw):
            parts = raw.split(maxsplit=1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else None
            if cmd in self.commands:
                result = self.commands[cmd](args)
                self.conversation_history.append({'user': raw, 'ai': result})
                return result

        # Greetings
        if self.is_greeting(raw):
            response = random.choice(self.greeting_responses)
            self.conversation_history.append({'user': raw, 'ai': response})
            return self.empathy.respond_with_empathy(emotion, response)

        # Math
        if self.is_math(raw):
            result = self.math_solver.solve(raw)
            if result is not None:
                response = str(result)
                self.conversation_history.append({'user': raw, 'ai': response})
                return response

        # Learn
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
                            with open(os.path.join(self.knowledge_dir, "learned_knowledge.json"), 'w') as f:
                                json.dump(self.qa_cache, f, indent=2)
                        except:
                            pass
                        return "Learned!"
            return "Format: learn question : answer"

        # Exact cache
        if low in self.qa_cache:
            response = self.qa_cache[low]
            self.conversation_history.append({'user': raw, 'ai': response})
            return response

        # Fuzzy cache
        best_match = None
        best_score = 0
        for cached_q, cached_a in self.qa_cache.items():
            score = SequenceMatcher(None, low, cached_q).ratio()
            if score > best_score and score > 0.65:
                best_score = score
                best_match = cached_a
        if best_match:
            self.conversation_history.append({'user': raw, 'ai': best_match})
            return best_match

        # Mesh query
        results = self.mesh.query(raw)
        if results and results[0]['score'] > 0.1:
            answer = self.clean_answer(results[0]['content'])
            self.conversation_history.append({'user': raw, 'ai': answer})
            return self.empathy.respond_with_empathy(emotion, answer)

        # Intuition as last resort
        intuitive = self.intuition.intuit(raw, self.mesh, self.qa_cache)
        if intuitive:
            self.conversation_history.append({'user': raw, 'ai': intuitive})
            return intuitive

        response = "I don't know that yet. Teach me: learn question : answer"
        self.conversation_history.append({'user': raw, 'ai': response})
        return response


# ========== WEB SERVER ==========
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
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"KeyGen.ai NMM Engine - Running")
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            stats = self.bot.mesh.get_stats() if self.bot else {}
            self.wfile.write(json.dumps({'status': 'healthy', 'mesh': stats}).encode())

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
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting on port: {port}")
    ChatHandler.bot = KeyGenAI()
    server = HTTPServer(('0.0.0.0', port), ChatHandler)
    print(f"KeyGen.ai NMM Engine - Port {port}")
    sys.stdout.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == "__main__":
    run_server()
