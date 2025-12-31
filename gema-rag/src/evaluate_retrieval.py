from pathlib import Path
import pickle
import faiss
import numpy as np
import time
from sentence_transformers import SentenceTransformer
import json
from datetime import datetime

INDEX_DIR = Path("data/index")
FAISS_INDEX_PATH = INDEX_DIR / "faiss_index.bin"
METADATA_PATH = INDEX_DIR / "metadata.pkl"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# 15 diverse test queries covering different aspects
TEST_QUERIES = [
    # Government schemes
    "What is Startup India Seed Fund Scheme?",
    "Tamil Nadu startup policy funding amount",
    "What are the eligibility criteria for SISFS?",
    
    # Specific amounts/numbers
    "How much funding was allocated to SISFS?",
    "What is the maximum investment amount through convertible debentures?",
    
    # Investors
    "Which venture capital investors fund agri-tech startups?",
    "List top investors in Indian startups",
    "Who invested in fintech startups in 2024?",
    
    # Sectors and trends
    "Startup funding trends in 2025",
    "Which sectors received most funding in India?",
    "Agriculture technology startup funding",
    
    # Geographic
    "Startup funding in Tamil Nadu",
    "Which states have startup policies?",
    
    # Complex queries
    "How do early stage startups get seed funding in India?",
    "What support do non-metro startups get from government schemes?"
]


def load_system():
    """Load FAISS index, metadata, and model"""
    index = faiss.read_index(str(FAISS_INDEX_PATH))
    with open(METADATA_PATH, "rb") as f:
        metadata = pickle.load(f)
    model = SentenceTransformer(EMBEDDING_MODEL)
    return index, metadata, model


def evaluate_query(query, index, metadata, model, top_k=5):
    """Evaluate single query with timing"""
    start_time = time.time()
    
    # Generate embedding
    query_embedding = model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(query_embedding)
    
    # Search
    scores, indices = index.search(query_embedding.astype('float32'), top_k)
    
    latency = (time.time() - start_time) * 1000  # milliseconds
    
    # Collect results
    results = []
    for score, idx in zip(scores[0], indices[0]):
        chunk_meta = metadata[idx]
        results.append({
            "score": float(score),
            "chunk_id": chunk_meta["chunk_id"],
            "filename": chunk_meta["filename"],
            "trust_score": chunk_meta["trust_score"],
            "language": chunk_meta["language"]
        })
    
    return {
        "query": query,
        "latency_ms": latency,
        "top_score": float(scores[0][0]),
        "avg_top5_score": float(np.mean(scores[0])),
        "results": results
    }


def compute_metrics(eval_results):
    """Compute aggregate metrics"""
    latencies = [r["latency_ms"] for r in eval_results]
    top_scores = [r["top_score"] for r in eval_results]
    avg_scores = [r["avg_top5_score"] for r in eval_results]
    
    # Accuracy heuristic: queries with top score > 0.6 considered "good"
    good_retrievals = sum(1 for score in top_scores if score > 0.6)
    accuracy = (good_retrievals / len(top_scores)) * 100
    
    metrics = {
        "total_queries": len(eval_results),
        "avg_latency_ms": np.mean(latencies),
        "min_latency_ms": np.min(latencies),
        "max_latency_ms": np.max(latencies),
        "avg_top_score": np.mean(top_scores),
        "avg_top5_score": np.mean(avg_scores),
        "accuracy_percent": accuracy,
        "queries_above_threshold": good_retrievals
    }
    
    return metrics


def display_evaluation_summary(metrics, eval_results):
    """Pretty print evaluation results"""
    print("\n" + "=" * 80)
    print("📊 RETRIEVAL EVALUATION RESULTS")
    print("=" * 80)
    
    print(f"\n⏱️  LATENCY METRICS")
    print(f"   Average: {metrics['avg_latency_ms']:.2f} ms")
    print(f"   Min: {metrics['min_latency_ms']:.2f} ms")
    print(f"   Max: {metrics['max_latency_ms']:.2f} ms")
    
    print(f"\n🎯 RELEVANCE METRICS")
    print(f"   Average Top-1 Score: {metrics['avg_top_score']:.4f}")
    print(f"   Average Top-5 Score: {metrics['avg_top5_score']:.4f}")
    print(f"   Retrieval Accuracy: {metrics['accuracy_percent']:.1f}% ({metrics['queries_above_threshold']}/{metrics['total_queries']} queries)")
    
    print(f"\n📋 PER-QUERY BREAKDOWN")
    print("-" * 80)
    
    for i, result in enumerate(eval_results, 1):
        status = "✅" if result["top_score"] > 0.6 else "⚠️"
        print(f"\n{status} Query {i}: {result['query'][:60]}...")
        print(f"   Latency: {result['latency_ms']:.2f}ms | Top Score: {result['top_score']:.4f}")
        print(f"   Best Match: {result['results'][0]['filename']} (trust: {result['results'][0]['trust_score']})")


def save_evaluation_report(metrics, eval_results):
    """Save detailed evaluation report"""
    report_dir = Path("data/evaluation")
    report_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"eval_report_{timestamp}.json"
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "model": EMBEDDING_MODEL,
        "metrics": metrics,
        "detailed_results": eval_results
    }
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Detailed report saved to: {report_path}")


def main():
    print("=" * 80)
    print("🧪 RETRIEVAL SYSTEM EVALUATION")
    print("=" * 80)
    
    # Load system
    print("\n🔄 Loading retrieval system...")
    index, metadata, model = load_system()
    print(f"✅ System loaded: {index.ntotal} vectors, {len(metadata)} chunks")
    
    # Run evaluation
    print(f"\n🔄 Evaluating {len(TEST_QUERIES)} test queries...")
    eval_results = []
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"   [{i}/{len(TEST_QUERIES)}] {query[:50]}...")
        result = evaluate_query(query, index, metadata, model, top_k=5)
        eval_results.append(result)
    
    # Compute metrics
    print("\n🔄 Computing aggregate metrics...")
    metrics = compute_metrics(eval_results)
    
    # Display results
    display_evaluation_summary(metrics, eval_results)
    
    # Save report
    save_evaluation_report(metrics, eval_results)
    
    print("\n" + "=" * 80)
    print("✅ EVALUATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
