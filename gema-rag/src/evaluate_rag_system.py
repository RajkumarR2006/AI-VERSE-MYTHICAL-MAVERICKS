from pathlib import Path
import pickle
import faiss
import numpy as np
import time
import json
import pandas as pd
from datetime import datetime
from sentence_transformers import SentenceTransformer
from groq import Groq

# Configuration
INDEX_DIR = Path("data/index")
FAISS_INDEX_PATH = INDEX_DIR / "faiss_index.bin"
METADATA_PATH = INDEX_DIR / "metadata.pkl"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
GROQ_API_KEY = ""  # Replace with your Groq API key

# --- GROUND TRUTH TEST DATA ---
# Curated from your actual corpus
TEST_DATA = [
    # === TOPIC 1: STARTUP INDIA SEED FUND SCHEME (SISFS) ===
    {
        "question": "What is the maximum grant amount under the Startup India Seed Fund Scheme?",
        "ground_truth": "Up to Rs. 20 Lakhs",
        "category": "SISFS"
    },
    {
        "question": "What is the maximum investment amount through convertible debentures under SISFS?",
        "ground_truth": "Up to Rs. 50 Lakhs",
        "category": "SISFS"
    },
    {
        "question": "Who is eligible to apply for the Seed Fund Scheme?",
        "ground_truth": "A DPIIT recognized startup incorporated not more than 2 years ago",
        "category": "SISFS"
    },
    {
        "question": "Can individual entrepreneurs apply for the Seed Fund Scheme?",
        "ground_truth": "No, only DPIIT recognized startups can apply",
        "category": "SISFS"
    },
    {
        "question": "What can the Seed Fund grant be used for?",
        "ground_truth": "Validation of Proof of Concept, prototype development, or product trials",
        "category": "SISFS"
    },
    {
        "question": "How many incubators can a startup apply to under SISFS?",
        "ground_truth": "A startup can apply to 3 different incubators",
        "category": "SISFS"
    },
    {
        "question": "What is the total allocation for SISFS scheme?",
        "ground_truth": "Rs. 945 Crores",
        "category": "SISFS"
    },
    
    # === TOPIC 2: TAMIL NADU STARTUP POLICY ===
    {
        "question": "What is TANSEED?",
        "ground_truth": "Tamil Nadu Startup Seed Fund, a support equity-linked grant fund scheme for early-stage startups",
        "category": "TN Policy"
    },
    {
        "question": "What type of funding does Tamil Nadu provide to startups?",
        "ground_truth": "Seed investment, establishment cost support, and funding for innovation infrastructure",
        "category": "TN Policy"
    },
    
    # === TOPIC 3: VENTURE CAPITAL & INVESTORS ===
    {
        "question": "Name top venture capital investors in Indian agri-tech",
        "ground_truth": "Bessemer Venture Partners, Pioneering Ventures, Y Combinator",
        "category": "Investors"
    },
    {
        "question": "Which investors funded fintech startups in India?",
        "ground_truth": "Sequoia Capital, Accel Partners, Tiger Global, Matrix Partners",
        "category": "Investors"
    },
    
    # === TOPIC 4: FUNDING TRENDS ===
    {
        "question": "Which sectors received most funding in 2022?",
        "ground_truth": "Fintech, E-commerce, Edtech, and Enterprise SaaS",
        "category": "Trends"
    },
    {
        "question": "What was the total funding raised by Indian startups in 2020?",
        "ground_truth": "Approximately $25 Billion",
        "category": "Trends"
    },
    
    # === TOPIC 5: SPECIFIC SCENARIOS ===
    {
        "question": "Can a 3-year-old startup apply for SISFS?",
        "ground_truth": "No, the startup must be incorporated not more than 2 years ago",
        "category": "Scenarios"
    },
    {
        "question": "Does SISFS support service-based startups?",
        "ground_truth": "Yes, SISFS is sector-agnostic",
        "category": "Scenarios"
    },
]


def load_retrieval_system():
    """Load FAISS index, metadata, and embedding model"""
    index = faiss.read_index(str(FAISS_INDEX_PATH))
    with open(METADATA_PATH, "rb") as f:
        metadata = pickle.load(f)
    model = SentenceTransformer(EMBEDDING_MODEL)
    return index, metadata, model


def retrieve_chunks(query, index, metadata, model, top_k=5):
    """Retrieve top-k most relevant chunks"""
    query_embedding = model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(query_embedding)
    scores, indices = index.search(query_embedding.astype('float32'), top_k)
    
    results = []
    for score, idx in zip(scores[0], indices[0]):
        chunk_meta = metadata[idx]
        results.append({
            "score": float(score),
            "chunk_id": chunk_meta["chunk_id"],
            "filename": chunk_meta["filename"],
            "trust_score": chunk_meta["trust_score"],
            "text": chunk_meta["text"]
        })
    return results


def generate_answer(query, retrieved_chunks, groq_client):
    """Generate answer using Groq LLM with evidence constraint"""
    # Build context from retrieved chunks
    context = "CONTEXT SNIPPETS:\n\n"
    for i, chunk in enumerate(retrieved_chunks, 1):
        context += f"[Snippet {i}]\n"
        context += f"Source: {chunk['filename']}\n"
        context += f"Trust Score: {chunk['trust_score']}\n"
        context += f"Text: {chunk['text'][:400]}...\n\n"
    
    # Strict prompt
    prompt = f"""You are a factual assistant for Indian startup funding intelligence.

MANDATORY RULES:
1. Use ONLY the CONTEXT SNIPPETS below to answer. Do not add external knowledge.
2. If the context does not contain sufficient information, respond: "Insufficient evidence in the corpus."
3. For numeric facts (amounts, dates), use exact values from the context.
4. Keep answers concise (2-3 sentences maximum).
5. Do not invent information not present in the context.

{context}

QUESTION: {query}

ANSWER:"""

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=200
        )
        answer = completion.choices[0].message.content.strip()
        return answer
    except Exception as e:
        return f"Error generating answer: {str(e)}"


def evaluate_answer_with_llm(question, generated_answer, ground_truth, groq_client):
    """Use LLM as judge to score answer accuracy (0-100)"""
    eval_prompt = f"""You are a strict grading assistant.

Question: {question}
Correct Answer: {ground_truth}
Student Answer: {generated_answer}

Task: Rate the Student Answer on a scale of 0 to 100 based on factual accuracy compared to the Correct Answer.

Scoring Guide:
- 100: Perfectly matches the correct answer
- 80-99: Correct with minor wording differences
- 60-79: Mostly correct but missing some details
- 40-59: Partially correct
- 1-39: Incorrect but attempts to answer
- 0: Completely wrong or says "Insufficient evidence" when answer exists

OUTPUT ONLY THE NUMBER (0-100). NO OTHER TEXT.
"""

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": eval_prompt}],
            temperature=0,
            max_tokens=10
        )
        score_text = completion.choices[0].message.content.strip()
        score = int(''.join(filter(str.isdigit, score_text)))
        return min(max(score, 0), 100)  # Clamp to 0-100
    except Exception as e:
        print(f"   ⚠️ Eval error: {e}")
        return 0


def compute_retrieval_metrics(retrieved_chunks, ground_truth):
    """Compute retrieval quality metrics"""
    # Heuristic: Check if ground truth keywords appear in top chunks
    gt_keywords = set(ground_truth.lower().split())
    
    # Precision@K: How many retrieved chunks contain relevant keywords
    relevant_count = 0
    for chunk in retrieved_chunks:
        chunk_text_lower = chunk["text"].lower()
        if any(kw in chunk_text_lower for kw in gt_keywords if len(kw) > 3):
            relevant_count += 1
    
    precision_at_k = relevant_count / len(retrieved_chunks) if retrieved_chunks else 0
    
    # Top-1 score (relevance of best match)
    top1_score = retrieved_chunks[0]["score"] if retrieved_chunks else 0
    
    # Average trust score of retrieved chunks
    avg_trust = np.mean([c["trust_score"] for c in retrieved_chunks]) if retrieved_chunks else 0
    
    return {
        "precision_at_5": precision_at_k,
        "top1_score": top1_score,
        "avg_trust_score": avg_trust
    }


def run_evaluation():
    """Main evaluation pipeline"""
    print("=" * 80)
    print("🧪 COMPREHENSIVE RAG SYSTEM EVALUATION")
    print("=" * 80)
    
    # Load system
    print("\n🔄 Loading retrieval system...")
    index, metadata, model = load_retrieval_system()
    print(f"✅ Loaded: {index.ntotal} vectors, {len(metadata)} chunks")
    
    # Initialize Groq
    print("🔄 Initializing Groq LLM...")
    if "YOUR_GROQ" in GROQ_API_KEY:
        print("⚠️  Warning: Using placeholder API key. Set GROQ_API_KEY in script.")
        groq_client = None
    else:
        groq_client = Groq(api_key=GROQ_API_KEY)
    
    # Run evaluation
    results = []
    print(f"\n🔄 Evaluating {len(TEST_DATA)} test questions...\n")
    print(f"{'QUESTION':<55} | {'TIME':<8} | {'ACCURACY':<8} | {'TOP-1':<8}")
    print("-" * 95)
    
    total_time = 0
    total_accuracy = 0
    total_retrieval_score = 0
    
    for item in TEST_DATA:
        q = item["question"]
        truth = item["ground_truth"]
        category = item["category"]
        
        try:
            # Start timing
            start_time = time.time()
            
            # 1. Retrieve
            retrieved_chunks = retrieve_chunks(q, index, metadata, model, top_k=5)
            
            # 2. Generate answer (if Groq available)
            if groq_client:
                generated_answer = generate_answer(q, retrieved_chunks, groq_client)
                
                # 3. Evaluate accuracy
                accuracy_score = evaluate_answer_with_llm(q, generated_answer, truth, groq_client)
                time.sleep(0.5)  # Rate limit protection
            else:
                generated_answer = "[Skipped - No API key]"
                accuracy_score = 0
            
            # 4. Compute retrieval metrics
            retrieval_metrics = compute_retrieval_metrics(retrieved_chunks, truth)
            
            end_time = time.time()
            time_taken = round(end_time - start_time, 2)
            
            # Print row
            q_short = q[:52] + "..." if len(q) > 52 else q
            print(f"{q_short:<55} | {time_taken:<8} | {accuracy_score:<8} | {retrieval_metrics['top1_score']:.4f}")
            
            # Store results
            results.append({
                "category": category,
                "question": q,
                "ground_truth": truth,
                "generated_answer": generated_answer,
                "accuracy_score": accuracy_score,
                "retrieval_top1_score": retrieval_metrics["top1_score"],
                "retrieval_precision_at_5": retrieval_metrics["precision_at_5"],
                "avg_trust_score": retrieval_metrics["avg_trust_score"],
                "latency_seconds": time_taken,
                "top_source": retrieved_chunks[0]["filename"] if retrieved_chunks else "N/A"
            })
            
            total_time += time_taken
            total_accuracy += accuracy_score
            total_retrieval_score += retrieval_metrics["top1_score"]
            
        except Exception as e:
            print(f"❌ Error on '{q[:50]}...': {e}")
    
    # Compute aggregate metrics
    n = len(results)
    if n > 0:
        avg_accuracy = round(total_accuracy / n, 1)
        avg_latency = round(total_time / n, 2)
        avg_retrieval_score = round(total_retrieval_score / n, 4)
        
        # Category-wise breakdown
        df = pd.DataFrame(results)
        category_stats = df.groupby("category").agg({
            "accuracy_score": "mean",
            "retrieval_top1_score": "mean",
            "latency_seconds": "mean"
        }).round(2)
        
        # Display final report
        print("\n" + "=" * 80)
        print("📊 FINAL EVALUATION REPORT")
        print("=" * 80)
        print(f"\n🎯 ANSWER QUALITY")
        print(f"   Average Accuracy: {avg_accuracy}/100")
        print(f"   Questions > 80 score: {len(df[df['accuracy_score'] >= 80])}/{n}")
        print(f"   Questions < 50 score: {len(df[df['accuracy_score'] < 50])}/{n}")
        
        print(f"\n🔍 RETRIEVAL QUALITY")
        print(f"   Average Top-1 Score: {avg_retrieval_score}")
        print(f"   Average Trust Score: {df['avg_trust_score'].mean():.2f}")
        print(f"   Average Precision@5: {df['retrieval_precision_at_5'].mean():.2f}")
        
        print(f"\n⏱️  PERFORMANCE")
        print(f"   Average Latency: {avg_latency}s")
        print(f"   Total Time: {round(total_time, 1)}s")
        
        print(f"\n📋 CATEGORY BREAKDOWN")
        print(category_stats.to_string())
        
        # Save detailed results
        report_dir = Path("data/evaluation")
        report_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        csv_path = report_dir / f"rag_eval_{timestamp}.csv"
        df.to_csv(csv_path, index=False)
        print(f"\n💾 Detailed results saved to: {csv_path}")
        
        # Save JSON summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "model": EMBEDDING_MODEL,
            "total_questions": n,
            "metrics": {
                "avg_accuracy": avg_accuracy,
                "avg_latency": avg_latency,
                "avg_retrieval_score": avg_retrieval_score,
                "avg_trust_score": float(df['avg_trust_score'].mean())
            },
            "category_stats": category_stats.to_dict()
        }
        
        json_path = report_dir / f"rag_eval_summary_{timestamp}.json"
        with open(json_path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"💾 Summary saved to: {json_path}")
        
        print("\n" + "=" * 80)
        print("✅ EVALUATION COMPLETE")
        print("=" * 80)


if __name__ == "__main__":
    run_evaluation()
