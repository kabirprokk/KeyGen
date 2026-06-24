"""
KeyGen.ai - Minimal working script for Render deployment
"""
import os
import sys
import json
import re
import random
import math
import time
import hashlib
from collections import defaultdict, deque
from http.server import HTTPServer, BaseHTTPRequestHandler
from difflib import SequenceMatcher
from datetime import datetime

# Print immediately so Render sees output
print("Starting KeyGen.ai...", flush=True)

# Get port - MUST be from environment
PORT = int(os.environ.get("PORT", 10000))
print(f"PORT={PORT}", flush=True)

class KeyGenAI:
    def __init__(self):
        self.qa_cache = {}
        self.sentences = []
        self.load_data()
    
    def load_data(self):
        knowledge_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge")
        collected_dir = os.path.join(knowledge_dir, "collected")
        
        for directory in [knowledge_dir, collected_dir]:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    if filename.endswith('.txt'):
                        try:
                            with open(os.path.join(directory, filename), 'r', encoding='utf-8', errors='ignore') as f:
                                text = f.read()
                                for sent in re.split(r'(?<=[.!?])\s+', text):
                                    sent = sent.strip()
                                    if len(sent) > 10:
                                        self.sentences.append(sent)
                                for subj, obj in re.findall(r'([A-Za-z\s]+?)\s+is\s+(?:a\s+|an\s+|the\s+)?([A-Za-z\s,]+?)[.!]', text, re.IGNORECASE):
                                    if len(subj.strip()) > 3 and len(obj.strip()) > 3:
                                        self.qa_cache[f"what is {subj.strip().lower()}"] = f"{subj.strip()} is {obj.strip()}."
                        except:
                            pass
        
        for jf in ['data.json', 'gk_knowledge.json']:
            fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), jf)
            try:
                if os.path.exists(fp):
                    with open(fp, 'r') as f:
                        for item in json.load(f):
                            if 'q' in item and 'a' in item:
                                self.qa_cache[item['q'].lower()] = item['a']
            except:
                pass
        
        lf = os.path.join(knowledge_dir, "learned_knowledge.json")
        try:
            if os.path.exists(lf):
                with open(lf, 'r') as f:
                    for q, a in json.load(f).items():
                        self.qa_cache[q.lower()] = a
        except:
            pass
        
        print(f"Loaded: {len(self.qa_cache)} Q&A, {len(self.sentences)} sentences", flush=True)
    
    def get_response(self, user_input):
        if not user_input or not user_input.strip():
            return "Please ask me something!"
        
        raw = user_input.strip()
        low = raw.lower()
        
        # Greetings
        greetings = {'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'howdy', 'sup', 'yo', 'hola', 'heya', 'heyy', 'hii'}
        if low.rstrip('!.,? ') in greetings or (len(low.split()) <= 2 and any(g in low for g in ['hi','hey','hello','yo','sup'])):
            return random.choice(["Hello! How can I help?", "Hi there! Ask me anything!", "Hey! Ready to answer!", "Greetings! What can I do?", "Welcome! How can I assist?"])
        
        # Math
        if any(op in low for op in ['+','-','*','/','plus','minus','times','divided']):
            try:
                text = low.replace('plus','+').replace('minus','-').replace('times','*').replace('divided by','/')
                match = re.search(r'(\d+)\s*([+\-*/])\s*(\d+)', text)
                if match:
                    a, op, b = int(match.group(1)), match.group(2), int(match.group(3))
                    ops = {'+': a+b, '-': a-b, '*': a*b, '/': a//b if b!=0 else None}
                    if op in ops and ops[op] is not None:
                        return str(ops[op])
            except:
                pass
        
        # Learn
        if low.startswith("learn "):
            content = raw[6:].strip()
            for sep in [" : ", " = ", " -> "]:
                if sep in content:
                    q, a = content.split(sep, 1)
                    self.qa_cache[q.strip().lower()] = a.strip()
                    try:
                        knowledge_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge")
                        os.makedirs(knowledge_dir, exist_ok=True)
                        with open(os.path.join(knowledge_dir, "learned_knowledge.json"), 'w') as f:
                            json.dump(self.qa_cache, f, indent=2)
                    except:
                        pass
                    return "Learned!"
            return "Format: learn question : answer"
        
        # Commands
        if low == 'help':
            return "Commands: help | status | time | calculate <expr> | define <term> | search <query> | learn Q : A"
        if low == 'status':
            return f"Q&A pairs: {len(self.qa_cache)} | Sentences: {len(self.sentences)}"
        if low == 'time':
            return datetime.now().strftime('%H:%M:%S')
        
        # Define command
        if low.startswith("define "):
            term = raw[7:].strip()
            q = f"what is {term.lower()}"
            if q in self.qa_cache:
                return self.qa_cache[q]
            for cached_q, cached_a in self.qa_cache.items():
                if term.lower() in cached_q:
                    return cached_a
            return f"No definition for '{term}'."
        
        # Search command
        if low.startswith("search "):
            query = raw[7:].strip().lower()
            results = []
            for sent in self.sentences:
                if query in sent.lower():
                    results.append(sent)
            if results:
                return "\n".join([f"- {r[:200]}" for r in results[:5]])
            return "No results found."
        
        # Exact cache match
        if low in self.qa_cache:
            return self.qa_cache[low]
        
        # Fuzzy cache match
        best, best_score = None, 0
        for q, a in self.qa_cache.items():
            s = SequenceMatcher(None, low, q).ratio()
            if s > best_score and s > 0.6:
                best_score, best = s, a
        if best:
            return best
        
        # Sentence search
        if self.sentences:
            scored = []
            q_words = set(re.findall(r'\b\w+\b', low))
            for sent in self.sentences:
                s_words = set(re.findall(r'\b\w+\b', sent.lower()))
                overlap = len(q_words & s_words) / max(len(q_words), 1)
                if overlap > 0.2:
                    scored.append((overlap, sent))
            if scored:
                scored.sort(reverse=True, key=lambda x: x[0])
                ans = scored[0][1]
                if len(ans) > 500:
                    ans = ans[:500].rsplit(' ', 1)[0] + "..."
                return ans
        
        return "I don't know that yet. Teach me: learn question : answer"


class Handler(BaseHTTPRequestHandler):
    bot = None
    
    def log_message(self, format, *args):
        pass
    
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'healthy'}).encode())
        else:
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
                self.wfile.write(json.dumps({'status': 'running', 'name': 'KeyGen.ai'}).encode())
    
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

# Create bot BEFORE server
print("Loading AI...", flush=True)
Handler.bot = KeyGenAI()
print("AI loaded!", flush=True)

# Create and start server
print(f"Starting server on 0.0.0.0:{PORT}...", flush=True)
server = HTTPServer(('0.0.0.0', PORT), Handler)
print(f"Server running on port {PORT}", flush=True)

try:
    server.serve_forever()
except KeyboardInterrupt:
    server.shutdown()
