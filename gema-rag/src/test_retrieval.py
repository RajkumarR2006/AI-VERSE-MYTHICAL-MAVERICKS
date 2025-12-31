"""
GEMA-RAG v2.3 - Test Retrieval System
Query the hybrid retrieval engine
"""

import json
import numpy as np
import faiss
import pickle
from pathlib import Path
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

# Load models
print("Loading models...")
minilm = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Load indices
print("Loading indices...")
index_dir = Path('data/index')
minilm_index = faiss.read_index(str(index_dir / 'faiss_minilm.index'))

with open(index_dir / 'bm25.pkl', 'rb') as f:
    bm25 = pickle.load(f)

with open(index_dir / 'chunk_ids.json', 'r') as f:
    chunk_ids = json.load(f)

# Load chunks
print("Loading chunks...")
chunks = []
with open('data/parsed/chunks.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        chunks.append(json.loads(line))

# Create chunk lookup
chunk_lookup = {c['chunk_id']: c for c in chunks}

def hybrid_search(query, top_k=10):
    """
    Hybrid retrieval: MiniLM (dense) + BM25 (sparse)
    """
    # Dense search with MiniLM
    query_embedding = minilm.encode([query])[0]
    faiss.normalize_L2(np.array([query_embedding]).astype('float32'))
    
    dense_scores, dense_indices = minilm_index.search(
        np.array([query_embedding]).astype('float32'), 
        top_k * 2
    )
    
    # Sparse search with BM25
    tokenized_query = query.lower().split()
    bm25_scores = bm25.get_scores(tokenized_query)
    bm25_top_indices = np.argsort(bm25_scores)[-top_k*2:][::-1]
    
    # Combine results (weighted fusion)
    results = {}
    
    # Add dense results (weight: 0.6)
    for idx, score in zip(dense_indices[0], dense_scores[0]):
        chunk_id = chunk_ids[int(idx)]
        results[chunk_id] = results.get(chunk_id, 0) + float(score) * 0.6
    
    # Add BM25 results (weight: 0.4)
    max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1.0
    for idx in bm25_top_indices:
        chunk_id = chunk_ids[int(idx)]
        normalized_score = bm25_scores[int(idx)] / max_bm25
        results[chunk_id] = results.get(chunk_id, 0) + normalized_score * 0.4
    
    # Sort by combined score
    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    # Return chunks with scores
    return [
        {
            'chunk': chunk_lookup[chunk_id],
            'score': score
        }
        for chunk_id, score in sorted_results
    ]

def display_results(results):
    """Pretty print search results"""
    print("\n" + "="*80)
    print("SEARCH RESULTS")
    print("="*80 + "\n")
    
    for i, result in enumerate(results, 1):
        chunk = result['chunk']
        score = result['score']
        
        print(f"Result {i} (Score: {score:.4f})")
        print(f"Source: {chunk['filename']} (Page {chunk['page']})")
        print(f"Language: {chunk['language']} | Trust: {chunk['trust_score']}")
        
        # Show canonicals if present
        if chunk['canonicals']:
            print(f"Amount: {chunk['canonicals'].get('amount_surface', 'N/A')}")
        
        print(f"\nText:\n{chunk['text'][:500]}...")
        print("\n" + "-"*80 + "\n")

def interactive_mode():
    """Interactive query loop"""
    print("\n" + "="*80)
    print("GEMA-RAG v2.3 - Interactive Retrieval")
    print("="*80)
    print("Type your questions below. Type 'exit' to quit.\n")
    
    while True:
        query = input("Query: ").strip()
        
        if query.lower() in ['exit', 'quit', 'q']:
            print("\nGoodbye!")
            break
        
        if not query:
            continue
        
        print(f"\nSearching for: '{query}'...")
        results = hybrid_search(query, top_k=5)
        display_results(results)

if __name__ == '__main__':
    # Test queries
    test_queries = [
        "What is the maximum amount under Startup India Seed Fund?",
        "Which investors funded fintech startups in 2025?",
        "Tamil Nadu startup policy eligibility",
    ]
    
    print("\n" + "="*80)
    print("Running test queries...")
    print("="*80 + "\n")
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = hybrid_search(query, top_k=3)
        display_results(results)
        input("Press Enter for next query...")
    
    # Switch to interactive mode
    interactive_mode()
