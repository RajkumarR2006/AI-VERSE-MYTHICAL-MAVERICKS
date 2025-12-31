"""
GEMA-RAG v2.3 - Index Builder
Builds MiniLM + LaBSE + BM25 indices
"""

import json
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import pickle

def main():
    # Paths relative to src/ folder
    chunks_path = Path('../data/parsed/chunks.jsonl')
    index_dir = Path('../data/index')
    
    # Create index directory if it doesn't exist
    index_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if chunks file exists
    if not chunks_path.exists():
        print(f"❌ Error: {chunks_path.absolute()} not found!")
        print(f"   Please run 'python ingest_data.py' first to create chunks.")
        print(f"   Make sure you have PDF/CSV files in data/raw/ folder.")
        return
    
    # Load chunks
    chunks = []
    with open(chunks_path, 'r', encoding='utf-8') as f:
        for line in f:
            chunks.append(json.loads(line))
    
    print(f"✓ Loaded {len(chunks)} chunks from {chunks_path.name}")
    
    if len(chunks) == 0:
        print("❌ No chunks found. Please run ingest_data.py first.")
        return
    
    # Build MiniLM index
    print("\n" + "="*60)
    print("Building MiniLM index...")
    print("="*60)
    minilm = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    minilm_embeddings = minilm.encode([c['text'] for c in chunks], show_progress_bar=True)
    
    minilm_index = faiss.IndexFlatIP(384)  # MiniLM dimension = 384
    faiss.normalize_L2(minilm_embeddings.astype('float32'))
    minilm_index.add(minilm_embeddings.astype('float32'))
    faiss.write_index(minilm_index, str(index_dir / 'faiss_minilm.index'))
    print(f"✓ MiniLM index created: {len(chunks)} chunks")
    
    # Build LaBSE index (Indic chunks only)
    print("\n" + "="*60)
    print("Building LaBSE index (for Indic language chunks)...")
    print("="*60)
    indic_chunks = [c for c in chunks if c.get('language') in ['hi', 'ta', 'te', 'kn', 'ml']]
    
    if indic_chunks:
        print(f"Found {len(indic_chunks)} Indic language chunks")
        labse = SentenceTransformer('sentence-transformers/LaBSE')
        labse_embeddings = labse.encode([c['text'] for c in indic_chunks], show_progress_bar=True)
        
        labse_index = faiss.IndexFlatIP(768)  # LaBSE dimension = 768
        faiss.normalize_L2(labse_embeddings.astype('float32'))
        labse_index.add(labse_embeddings.astype('float32'))
        faiss.write_index(labse_index, str(index_dir / 'faiss_labse.index'))
        
        # Save Indic chunk IDs
        with open(index_dir / 'indic_chunk_ids.json', 'w') as f:
            json.dump([c['chunk_id'] for c in indic_chunks], f)
        print(f"✓ LaBSE index created: {len(indic_chunks)} Indic chunks")
    else:
        print("⚠️ No Indic language chunks found. Skipping LaBSE index.")
        print("   All chunks are in English.")
    
    # Build BM25 index
    print("\n" + "="*60)
    print("Building BM25 index...")
    print("="*60)
    tokenized_corpus = [c['text'].lower().split() for c in chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    
    with open(index_dir / 'bm25.pkl', 'wb') as f:
        pickle.dump(bm25, f)
    print(f"✓ BM25 index created: {len(chunks)} chunks")
    
    # Save chunk ID mapping
    with open(index_dir / 'chunk_ids.json', 'w') as f:
        json.dump([c['chunk_id'] for c in chunks], f)
    
    # Summary
    print("\n" + "="*60)
    print("✅ INDEXING COMPLETE")
    print("="*60)
    print(f"Total chunks indexed: {len(chunks)}")
    print(f"MiniLM index: {len(chunks)} chunks (English + All)")
    print(f"LaBSE index: {len(indic_chunks)} chunks (Indic languages)")
    print(f"BM25 index: {len(chunks)} chunks (Keyword matching)")
    print(f"\nIndex location: {index_dir.absolute()}")
    print("="*60)

if __name__ == '__main__':
    main()
