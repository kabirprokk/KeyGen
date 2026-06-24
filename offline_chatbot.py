"""
KeyGen.ai - Production AI Engine
Uses Gunicorn for Render deployment
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
from difflib import SequenceMatcher
from datetime import datetime

# ========== AI ENGINE ==========
class KeyGenAI:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.knowledge_dir = os.path.join(self.base_dir, "knowledge")
        self.collected_dir = os.path.join(self.knowledge_dir, "collected")
        self.qa_cache = {}
        self.sentences = []
        self.nodes = {}
        self.total_activations = 0
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
                                        nid = hashlib.md5(sent.encode('utf-8')).hexdigest()[:12]
                                        self.nodes[nid] = {'content': sent, 'type': 'fact' if re.search(r'\b(is|are|was|were)\b', sent, re.I) else 'concept', 'fires': 0}
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

        if low.rstrip('!.,? ') in self.greetings or (len(low.split()) <= 2 and any(g in low for g in ['hi','hey','hello','yo','sup'])):
            return random.choice(self.greet_responses)

        if any(op in low for op in ['+','-','*','/','plus','minus','times','divided']):
            text = low.replace('plus','+').replace('minus','-').replace('times','*').replace('divided by','/').replace('x','*')
            match = re.search(r'(\d+(?:\.\d+)?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)', text)
            if match:
                a, op, b = float(match.group(1)), match.group(2), float(match.group(3))
                ops = {'+': a+b, '-': a-b, '*': a*b, '/': a/b if b!=0 else None}
                if op in ops and ops[op] is not None:
                    r = ops[op]
                    return str(int(r) if r == int(r) else round(r, 4))

        if low.startswith("learn "):
            content = raw[6:].strip()
            for sep in [" : ", " = ", " -> "]:
                if sep in content:
                    q, a = content.split(sep, 1)
                    self.qa_cache[q.strip().lower()] = a.strip()
                    self._save()
                    return "Learned!"
            return "Format: learn question : answer"

        if low == 'help': return "Commands: help | status | time | calculate expr | define term | search query | learn Q : A"
        if low == 'status': return f"Q&A: {len(self.qa_cache)} | Sentences: {len(self.sentences)} | Nodes: {len(self.nodes)}"
        if low == 'time': return datetime.now().strftime('%H:%M:%S')
        if low.startswith("calculate "):
            text = raw[10:].lower().replace('plus','+').replace('minus','-').replace('times','*')
            match = re.search(r'(\d+)\s*([+\-*/])\s*(\d+)', text)
            if match:
                a, op, b = int(match.group(1)), match.group(2), int(match.group(3))
                ops = {'+': a+b, '-': a-b, '*': a*b, '/': a//b if b!=0 else None}
                if op in ops and ops[op] is not None: return str(ops[op])
            return "Cannot solve"
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

        if low in self.qa_cache: return self.qa_cache[low]

        best, bs = None, 0
        for q, a in self.qa_cache.items():
            s = SequenceMatcher(None, low, q).ratio()
            if s > bs and s > 0.6: best, bs = a, s
        if best: return best

        if self.sentences:
            qw = set(re.findall(r'\b\w+\b', low))
            scored = []
            for s in self.sentences:
                sw = set(re.findall(r'\b\w+\b', s.lower()))
                overlap = len(qw & sw) / max(len(qw), 1)
                if overlap > 0.15:
                    scored.append((overlap, s))
            if scored:
                scored.sort(reverse=True, key=lambda x: x[0])
                return scored[0][1][:500]

        return "I don't know that yet. Teach me: learn question : answer"


# ========== FLASK APP FOR RENDER ==========
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)
ai = KeyGenAI()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '')
    response = ai.get_response(message)
    return jsonify({'response': response})

@app.route('/stats')
def stats():
    return jsonify({'qa_cache': len(ai.qa_cache), 'sentences': len(ai.sentences), 'nodes': len(ai.nodes)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
