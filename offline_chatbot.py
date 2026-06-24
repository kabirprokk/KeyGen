"""
KeyGen.ai - Simple Working Version for Render
"""
import os
import json
import re
import random
import math
from datetime import datetime
from difflib import SequenceMatcher
from flask import Flask, request, jsonify, send_from_directory

# Create Flask app FIRST
app = Flask(__name__)

# Simple AI class
class SimpleAI:
    def __init__(self):
        self.qa = {}
        self.sentences = []
        self.load()
    
    def load(self):
        base = os.path.dirname(os.path.abspath(__file__))
        knowledge = os.path.join(base, "knowledge")
        collected = os.path.join(knowledge, "collected")
        
        for d in [knowledge, collected]:
            if os.path.exists(d):
                for f in os.listdir(d):
                    if f.endswith('.txt'):
                        try:
                            with open(os.path.join(d, f), 'r', encoding='utf-8', errors='ignore') as file:
                                text = file.read()
                                for sent in re.split(r'(?<=[.!?])\s+', text):
                                    sent = sent.strip()
                                    if len(sent) > 10:
                                        self.sentences.append(sent)
                                for subj, obj in re.findall(r'(.+?)\s+is\s+(.+?)[.!]', text, re.IGNORECASE):
                                    if len(subj.strip()) > 2 and len(obj.strip()) > 2:
                                        self.qa[f"what is {subj.strip().lower()}"] = f"{subj.strip()} is {obj.strip()}."
                        except: pass
        
        for jf in ['data.json', 'gk_knowledge.json']:
            try:
                fp = os.path.join(base, jf)
                if os.path.exists(fp):
                    with open(fp, 'r') as f:
                        for item in json.load(f):
                            if 'q' in item and 'a' in item:
                                self.qa[item['q'].lower()] = item['a']
            except: pass
        
        try:
            lf = os.path.join(knowledge, "learned_knowledge.json")
            if os.path.exists(lf):
                with open(lf, 'r') as f:
                    for q, a in json.load(f).items():
                        self.qa[q.lower()] = a
        except: pass
    
    def respond(self, msg):
        msg = msg.strip()
        low = msg.lower()
        
        # Greetings
        g = {'hi','hello','hey','good morning','good afternoon','good evening','howdy','sup','yo','hola','heya','heyy','hii'}
        if low.rstrip('!.,? ') in g:
            return random.choice(["Hello!","Hi there!","Hey!","Greetings!","Welcome!"])
        
        # Math
        if any(op in low for op in ['+','-','*','/','plus','minus','times']):
            text = low.replace('plus','+').replace('minus','-').replace('times','*')
            m = re.search(r'(\d+)\s*([+\-*/])\s*(\d+)', text)
            if m:
                a,op,b = int(m.group(1)),m.group(2),int(m.group(3))
                if op=='+': return str(a+b)
                if op=='-': return str(a-b)
                if op=='*': return str(a*b)
                if op=='/' and b!=0: return str(a//b)
        
        # Learn
        if low.startswith("learn "):
            c = msg[6:].strip()
            for s in [" : "," = "," -> "]:
                if s in c:
                    q,a = c.split(s,1)
                    self.qa[q.strip().lower()] = a.strip()
                    try:
                        base = os.path.dirname(os.path.abspath(__file__))
                        knowledge = os.path.join(base, "knowledge")
                        os.makedirs(knowledge, exist_ok=True)
                        with open(os.path.join(knowledge, "learned_knowledge.json"), 'w') as f:
                            json.dump(self.qa, f, indent=2)
                    except: pass
                    return "Learned!"
            return "Format: learn question : answer"
        
        # Commands
        if low == 'help': return "help | status | time | calculate | define | search | learn"
        if low == 'status': return f"Q&A: {len(self.qa)} | Sentences: {len(self.sentences)}"
        if low == 'time': return datetime.now().strftime('%H:%M:%S')
        if low.startswith("calculate "):
            t = low[10:].replace('plus','+').replace('minus','-').replace('times','*')
            m = re.search(r'(\d+)\s*([+\-*/])\s*(\d+)', t)
            if m:
                a,op,b = int(m.group(1)),m.group(2),int(m.group(3))
                ops = {'+':a+b,'-':a-b,'*':a*b,'/':a//b if b!=0 else 0}
                return str(ops.get(op,0))
        if low.startswith("define "):
            t = low[7:]
            q = f"what is {t}"
            if q in self.qa: return self.qa[q]
            for k,v in self.qa.items():
                if t in k: return v
            return f"No definition for '{msg[7:]}'"
        if low.startswith("search "):
            q = low[7:]
            r = [s[:300] for s in self.sentences if q in s.lower()][:5]
            return "\n".join(f"- {x}" for x in r) if r else "No results"
        
        # Exact match
        if low in self.qa: return self.qa[low]
        
        # Fuzzy match
        best,bs = None,0
        for k,v in self.qa.items():
            s = SequenceMatcher(None,low,k).ratio()
            if s>bs and s>0.6: best,bs = v,s
        if best: return best
        
        # Sentence search
        qw = set(re.findall(r'\b\w+\b', low))
        scored = []
        for s in self.sentences:
            sw = set(re.findall(r'\b\w+\b', s.lower()))
            o = len(qw&sw)/max(len(qw),1)
            if o>0.15: scored.append((o,s))
        if scored:
            scored.sort(reverse=True,key=lambda x:x[0])
            return scored[0][1][:500]
        
        return "I don't know that. Teach me: learn question : answer"

# Create AI instance
ai = SimpleAI()

# Routes
@app.route('/')
def index():
    try:
        return send_from_directory('.', 'index.html')
    except:
        return jsonify({'status':'running','name':'KeyGen.ai'})

@app.route('/health')
def health():
    return jsonify({'status':'healthy'})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    msg = data.get('message','')
    resp = ai.respond(msg)
    return jsonify({'response':resp})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
