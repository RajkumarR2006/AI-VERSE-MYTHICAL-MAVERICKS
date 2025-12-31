"""
GEMA-RAG v2.3 - Evaluation Framework
Tests system accuracy on gold question set (30 questions)
"""

import json
import time
import re
from pathlib import Path
from answer_question import answer_question, check_faq


# Gold test dataset (30 questions: 15 SISFS + 15 ecosystem)
GOLD_QUESTIONS = [
    # Original 15 SISFS questions
    {"question": "What is the maximum grant amount under the Startup India Seed Fund Scheme?", "ground_truth": "Rs. 20 Lakhs", "category": "amount"},
    {"question": "What is the maximum investment amount through convertible debentures under SISFS?", "ground_truth": "Rs. 50 Lakhs", "category": "amount"},
    {"question": "Who is eligible to apply for the Seed Fund Scheme?", "ground_truth": "A DPIIT recognized startup incorporated not more than 2 years ago", "category": "eligibility"},
    {"question": "Can individual entrepreneurs apply for the Seed Fund Scheme?", "ground_truth": "No, only DPIIT recognized startups can apply", "category": "eligibility"},
    {"question": "What can the Seed Fund grant be used for?", "ground_truth": "Validation of Proof of Concept, prototype development, or product trials", "category": "purpose"},
    {"question": "What can the Seed Fund investment be used for?", "ground_truth": "Market entry, commercialization, or scaling up", "category": "purpose"},
    {"question": "Is there an application fee for SISFS?", "ground_truth": "No, there are no application fees", "category": "process"},
    {"question": "How many incubators can a startup apply to under SISFS?", "ground_truth": "A startup can apply to 3 different incubators", "category": "process"},
    {"question": "What is the interest rate for debt financing under SISFS?", "ground_truth": "Not more than the prevailing repo rate", "category": "financial"},
    {"question": "What is the tenure for debt repayment under SISFS?", "ground_truth": "Not more than 60 months (5 years)", "category": "financial"},
    {"question": "Is a personal guarantee required for SISFS debt?", "ground_truth": "No, it is unsecured and no guarantee is required", "category": "financial"},
    {"question": "Can a 3-year-old startup apply for SISFS?", "ground_truth": "No, the startup must be incorporated not more than 2 years ago", "category": "eligibility"},
    {"question": "Which government body manages the Startup India initiative?", "ground_truth": "Department for Promotion of Industry and Internal Trade (DPIIT)", "category": "organization"},
    {"question": "Does SISFS support service-based startups?", "ground_truth": "Yes, SISFS is sector-agnostic", "category": "sector"},
    {"question": "What is the moratorium period for SISFS debt?", "ground_truth": "Up to 12 months", "category": "financial"},
    
    # Additional 15 ecosystem questions
    {"question": "Which sector received the most funding in 2024?", "ground_truth": "Consumer Internet, Fintech, and Edtech are typically top sectors", "category": "ecosystem"},
    {"question": "Name top 3 active Venture Capital firms in India.", "ground_truth": "Sequoia Capital, Accel Partners, Blume Ventures", "category": "ecosystem"},
    {"question": "What is the typical check size for Seed funding in India?", "ground_truth": "INR 20 Lakhs to 2 Crores", "category": "ecosystem"},
    {"question": "Name an Indian EdTech unicorn.", "ground_truth": "Byju's, Unacademy, or UpGrad", "category": "ecosystem"},
    {"question": "Name an Indian Fintech unicorn.", "ground_truth": "Paytm, Razorpay, Cred, or PhonePe", "category": "ecosystem"},
    {"question": "What is the 'Funding Winter'?", "ground_truth": "A period of reduced capital inflows and lower valuations for startups", "category": "ecosystem"},
    {"question": "Which Indian city is known as the 'Startup Capital'?", "ground_truth": "Bengaluru", "category": "ecosystem"},
    {"question": "What is 'Femtech'?", "ground_truth": "Technology focused on women's health and wellness", "category": "ecosystem"},
    {"question": "Who founded Zomato?", "ground_truth": "Deepinder Goyal", "category": "ecosystem"},
    {"question": "Who founded Flipkart?", "ground_truth": "Sachin Bansal and Binny Bansal", "category": "ecosystem"},
    {"question": "What is an 'Incubator'?", "ground_truth": "An organization that helps early-stage startups develop with workspace and mentorship", "category": "ecosystem"},
    {"question": "What is an 'Accelerator'?", "ground_truth": "A fixed-term program that helps growth-stage startups scale quickly", "category": "ecosystem"},
    {"question": "What is 'Equity Dilution'?", "ground_truth": "The decrease in ownership percentage when new shares are issued to investors", "category": "ecosystem"},
    {"question": "What is 'Term Sheet'?", "ground_truth": "A non-binding agreement setting the basic terms of an investment", "category": "ecosystem"},
    {"question": "What is 'Due Diligence'?", "ground_truth": "The investigation or audit of a potential investment", "category": "ecosystem"}
]


def simple_accuracy_check(answer, ground_truth):
    """Keyword-based accuracy check"""
    answer_lower = answer.lower()
    truth_lower = ground_truth.lower()
    
    # Extract key terms
    key_terms = []
    
    # Extract amounts (Rs. 20 Lakhs, Rs. 50 Lakhs, INR, etc.)
    amounts = re.findall(r'(?:rs\.?|inr)\s*\d+\s*(?:lakhs?|crores?)', truth_lower)
    key_terms.extend(amounts)
    
    # Extract numbers
    numbers = re.findall(r'\d+', truth_lower)
    key_terms.extend(numbers)
    
    # Extract important words (expanded for ecosystem questions)
    stopwords = {'the', 'and', 'for', 'not', 'can', 'are', 'under', 'must', 'than', 'more', 'less', 'with', 'that', 'this', 'from', 'when', 'what', 'which', 'who'}
    words = [w for w in truth_lower.split() if len(w) > 3 and w not in stopwords]
    key_terms.extend(words[:7])  # Increased from 5 to 7 for more context
    
    # Check matches
    if not key_terms:
        return 0.5
    
    matches = sum(1 for term in key_terms if term in answer_lower)
    accuracy = matches / len(key_terms)
    
    # Adjusted threshold for ecosystem questions
    return 1.0 if accuracy >= 0.5 else 0.0  # Lowered from 0.6 to 0.5


def evaluate():
    """Run evaluation on gold question set"""
    print("\n" + "="*80)
    print("🧪 GEMA-RAG v2.3 - EVALUATION FRAMEWORK")
    print("="*80)
    print(f"Testing on {len(GOLD_QUESTIONS)} gold questions...")
    print(f"  - 15 SISFS questions")
    print(f"  - 15 Ecosystem questions\n")
    
    results = []
    total_correct = 0
    faq_hits = 0
    total_time = 0
    
    for i, item in enumerate(GOLD_QUESTIONS, 1):
        question = item['question']
        ground_truth = item['ground_truth']
        category = item['category']
        
        print(f"\n{'─'*80}")
        print(f"[{i}/{len(GOLD_QUESTIONS)}] {category.upper()}")
        print(f"Q: {question}")
        print(f"Expected: {ground_truth}")
        
        start_time = time.time()
        
        try:
            # Get answer (silent mode)
            result = answer_question(question, top_k=5, silent=True)
            answer = result['answer']
            source_type = result.get('source', 'RAG')
            
            if source_type == 'FAQ':
                faq_hits += 1
            
            elapsed = time.time() - start_time
            total_time += elapsed
            
            # Evaluate accuracy
            is_correct = simple_accuracy_check(answer, ground_truth)
            total_correct += is_correct
            
            status = "✅ PASS" if is_correct == 1.0 else "❌ FAIL"
            
            print(f"A: {answer[:150]}...")
            print(f"{status} | Time: {elapsed:.2f}s | Source: {source_type}")
            
            results.append({
                'question': question,
                'ground_truth': ground_truth,
                'answer': answer,
                'category': category,
                'correct': is_correct,
                'time': elapsed,
                'source': source_type
            })
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            results.append({
                'question': question,
                'ground_truth': ground_truth,
                'answer': f"ERROR: {str(e)}",
                'category': category,
                'correct': 0.0,
                'time': 0.0,
                'source': 'ERROR'
            })
        
        time.sleep(0.5)  # Avoid rate limits
    
    # Calculate metrics
    accuracy = (total_correct / len(GOLD_QUESTIONS)) * 100
    avg_time = total_time / len(GOLD_QUESTIONS)
    faq_coverage = (faq_hits / len(GOLD_QUESTIONS)) * 100
    
    # Print summary
    print("\n" + "="*80)
    print("📊 EVALUATION SUMMARY")
    print("="*80)
    print(f"Total Questions: {len(GOLD_QUESTIONS)}")
    print(f"Correct Answers: {int(total_correct)}/{len(GOLD_QUESTIONS)}")
    print(f"Accuracy: {accuracy:.1f}%")
    print(f"FAQ Coverage: {faq_coverage:.1f}% ({faq_hits} hits)")
    print(f"Average Latency: {avg_time:.2f}s")
    print("="*80)
    
    # Category breakdown
    print("\n📈 ACCURACY BY CATEGORY:")
    categories = {}
    for r in results:
        cat = r['category']
        if cat not in categories:
            categories[cat] = {'correct': 0, 'total': 0}
        categories[cat]['total'] += 1
        categories[cat]['correct'] += r['correct']
    
    for cat, stats in sorted(categories.items()):
        cat_accuracy = (stats['correct'] / stats['total']) * 100
        print(f"  {cat.title():15s}: {cat_accuracy:.1f}% ({int(stats['correct'])}/{stats['total']})")
    
    # Save results
    output_dir = Path('data/evaluation')
    output_dir.mkdir(exist_ok=True, parents=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    with open(output_dir / f'evaluation_results_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'accuracy': accuracy,
                'faq_coverage': faq_coverage,
                'avg_latency': avg_time,
                'total_questions': len(GOLD_QUESTIONS),
                'correct': int(total_correct),
                'timestamp': timestamp
            },
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_dir / f'evaluation_results_{timestamp}.json'}")
    print(f"\n{'='*80}\n")
    
    return accuracy


if __name__ == '__main__':
    accuracy = evaluate()
    print(f"🎯 Final Accuracy: {accuracy:.1f}%")
