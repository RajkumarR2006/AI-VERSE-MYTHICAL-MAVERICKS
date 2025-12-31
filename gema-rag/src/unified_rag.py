"""
GEMA-RAG v2.5 - Unified RAG System
FINAL PRODUCTION VERSION - GEN-AI CONVERSATIONAL MODE
"""

# Import the new handle_chitchat function
from answer_question import generate_answer, check_faq, handle_chitchat
from query_graph import GraphQueryEngine
from verify_answer import AnswerVerifier
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import numpy as np
import pandas as pd

class UnifiedRAG:
    """
    Unified RAG system with Intelligent Generative Routing.
    """
    
    def __init__(self):
        print("="*80)
        print("🚀 Initializing GEMA-RAG v2.5 (Gen-AI Mode)")
        print("="*80 + "\n")
        
        # 1. Load Search Components (for Semantic Route)
        print("Loading Retrieval Engines...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = faiss.read_index('../data/index/faiss_minilm.index')
        with open('../data/parsed/chunks.jsonl', 'r', encoding='utf-8') as f:
            self.chunks = [json.loads(line) for line in f]
        print(f"✓ Loaded {len(self.chunks)} documents")

        # 2. Load Graph Engine
        print("Loading Graph Query Engine...")
        self.graph_engine = GraphQueryEngine()
        
        # 3. Load Verifier
        print("Loading Answer Verifier...")
        self.verifier = AnswerVerifier()
        
        print("\n✓ All systems ready!\n")
    
    def classify_query(self, query):
        """
        Classifies query to route to the correct engine.
        """
        q = query.lower().strip()
        
        # 1. GEN-AI SMALL TALK (Expanded List)
        # Catches greetings, feelings, compliments, insults, and meta-questions
        chitchat_triggers = [
            'hi', 'hello', 'hey', 'good morning', 'good evening', 
            'how are you', 'how r u', 'how is it going', 'whats up',
            'who are you', 'what is your name', 'are you human', 'you are smart',
            'thank you', 'thanks', 'cool', 'ok', 'bye', 'goodbye'
        ]
        
        # If it's a short conversational phrase
        if q in chitchat_triggers or (len(q) < 30 and any(t in q for t in chitchat_triggers)):
            return 'SMALL_TALK'
            
        # 2. CAPABILITY (Specific questions about features)
        if 'what can you do' in q or 'help me' in q:
            return 'CAPABILITY'

        # 3. GRAPH (Data Relationships)
        graph_keywords = ['list of', 'which investors', 'which sectors', 'how many', 'relationships']
        if any(k in q for k in graph_keywords):
            return 'GRAPH'
        
        # 4. FAQ (Specific Facts)
        faq_keywords = ['maximum grant', 'eligible', 'interest rate', 'tenure']
        if any(k in q for k in faq_keywords):
            return 'FAQ'
        
        # 5. SEMANTIC (Default deep search)
        return 'SEMANTIC'
    
    def retrieve_documents(self, query, k=5):
        """
        Retrieves relevant documents and Normalizes them for the UI (Fixes 'Unknown Document').
        """
        query_vector = self.model.encode([query])
        D, I = self.index.search(query_vector, k)
        results = []
        
        for idx in I[0]:
            if idx < len(self.chunks):
                raw_chunk = self.chunks[idx]
                
                # --- NORMALIZATION FIX ---
                # 1. Safely extract data (Handle both flat and nested 'chunk' data)
                data = raw_chunk.get('chunk', raw_chunk)
                
                # 2. Get fields with fallbacks
                filename = data.get('filename') or data.get('source') or "Unknown Document"
                page = data.get('page') or "1"
                text = data.get('text') or data.get('content') or ""
                
                # 3. Create a "Super Chunk" that works for ANY UI (Vercel/Streamlit/NextJS)
                normalized_chunk = {
                    # Top level keys (for Python logic)
                    'text': text,
                    'chunk': data, 
                    
                    # Keys for common UIs 
                    'page_content': text, 
                    'source': filename,
                    'filename': filename,
                    'page': page,
                    
                    # Nested Metadata (Crucial for Sidebars)
                    'metadata': {
                        'filename': filename,
                        'source': filename,
                        'page': page,
                        'file_path': filename
                    }
                }
                results.append(normalized_chunk)
                
        return results
    
    def answer(self, query, verbose=True):
        """
        Main routing logic with GEN-AI Small Talk.
        """
        if verbose:
            print(f"\n❓ Query: {query}")
        
        query_type = self.classify_query(query)
        if verbose:
            print(f"🎯 Query Type: {query_type}")
        
        # --- Route 1: SMALL TALK (Gen AI Mode) ---
        if query_type == 'SMALL_TALK':
            # We call the LLM directly with a "Chitchat Prompt"
            # No context needed. Pure Gen AI conversation.
            gen_response = handle_chitchat(query)
            
            return {
                'query': query,
                'answer': gen_response,
                'source': 'CHAT_AI',
                'confidence': 1.0,
                'verified': True
            }

        # --- Route 2: CAPABILITY ---
        if query_type == 'CAPABILITY':
            return {
                'query': query,
                'answer': "I am Aura, your Startup Consultant. I can help you find **Funding Schemes**, analyze **Investors**, and understand **Government Policy**. Try asking: *'What is the SISFS scheme?'*",
                'source': 'CHAT_SYSTEM',
                'confidence': 1.0,
                'verified': True
            }

        # --- Route 3: FAQ ---
        if query_type == 'FAQ':
            faq_result = check_faq(query)
            if faq_result:
                return {
                    'query': query,
                    'answer': faq_result['answer'],
                    'source': 'FAQ',
                    'confidence': faq_result['confidence'],
                    'verified': True
                }

        # --- Route 4: GRAPH ---
        if query_type == 'GRAPH':
            graph_answer = self.graph_engine.answer_graph_query(query)
            if graph_answer:
                return {
                    'query': query,
                    'answer': graph_answer,
                    'source': 'GRAPH',
                    'confidence': 1.0,
                    'verified': True
                }

        # --- Route 5: SEMANTIC RAG (Deep Search) ---
        # 1. Retrieve
        context_chunks = self.retrieve_documents(query)
        
        # 2. Generate (using the professional prompt)
        rag_answer = generate_answer(query, context_chunks)
        
        # 3. Verify
        verification = self.verifier.verify_answer(
            answer=rag_answer, 
            sources=context_chunks, 
            source_type='RAG'
        )
        
        return {
            'query': query,
            'answer': rag_answer,
            'source': 'SEMANTIC',
            'sources': context_chunks,
            'confidence': 0.85,
            'verified': verification['verified']
        }
        
    def interactive(self):
        print("Aura Unified System Online. Type 'exit' to stop.")
        while True:
            try:
                q = input("💬 Question: ").strip()
                if q.lower() in ['exit', 'quit']: break
                res = self.answer(q)
                print(f"🤖 Aura: {res['answer']}\n")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

# Needed for imports
import json

if __name__ == '__main__':
    rag = UnifiedRAG()
    rag.interactive()