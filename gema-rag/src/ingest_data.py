"""
GEMA-RAG v2.5.2 - CSV CONTEXT FIX (STRICT DETECTION)
✅ Optimized PDF chunking (Method 5)
✅ FIXED: Strict funding detection (entity + financial)
✅ Smart column name matching
✅ Robust encoding handling
"""

import json
import re
import hashlib
from pathlib import Path
from datetime import datetime
import pdfplumber
import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np
import warnings

warnings.filterwarnings('ignore')

try:
    from langdetect import detect_langs
    LANGDETECT_AVAILABLE = True
except:
    LANGDETECT_AVAILABLE = False

# PDF Chunking Parameters
SEMANTIC_THRESHOLD = 0.65
MAX_CHUNK_WORDS = 300
MIN_CHUNK_WORDS_PDF = 50

print("Loading LaBSE model...")
labse = SentenceTransformer('sentence-transformers/LaBSE')
print("✓ LaBSE loaded\n")


def canonicalize_numerics(text):
    """Extract and normalize amounts"""
    canonicals = {}
    patterns = [
        (r'₹\s*([\d,]+\.?\d*)\s*Cr(?:ore)?', lambda x: float(x.replace(',', '')) * 10_000_000, 'INR'),
        (r'₹\s*([\d,]+\.?\d*)\s*[Ll]akh', lambda x: float(x.replace(',', '')) * 100_000, 'INR'),
        (r'Rs\.?\s*([\d,]+\.?\d*)\s*Cr(?:ore)?', lambda x: float(x.replace(',', '')) * 10_000_000, 'INR'),
        (r'Rs\.?\s*([\d,]+\.?\d*)\s*[Ll]akh', lambda x: float(x.replace(',', '')) * 100_000, 'INR'),
        (r'\$\s*([\d,]+\.?\d*)\s*[Mm]', lambda x: float(x.replace(',', '')) * 1_000_000, 'USD'),
        (r'\$\s*([\d,]+\.?\d*)\s*[Bb]', lambda x: float(x.replace(',', '')) * 1_000_000_000, 'USD'),
    ]
    
    for pattern, converter, currency in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                amount_str = match.group(1)
                if amount_str and amount_str.strip() not in ['.', ',', '']:
                    canonicals['amount_surface'] = match.group(0)
                    canonicals['amount_number'] = int(converter(amount_str))
                    canonicals['currency'] = currency
                    break
            except:
                continue
    
    return canonicals


def detect_language(text):
    """Detect language with fallback"""
    if not LANGDETECT_AVAILABLE or not text or len(text.strip()) < 20:
        return 'en'
    
    try:
        lang_results = detect_langs(text)
        return lang_results[0].lang if lang_results else 'en'
    except:
        return 'en'


def semantic_chunk(text, threshold=SEMANTIC_THRESHOLD, max_chunk_words=MAX_CHUNK_WORDS, min_chunk_words=MIN_CHUNK_WORDS_PDF):
    """Semantic chunking for PDFs"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) < 3:
        return [text] if text.strip() else []
    
    sentences = [s for s in sentences if s.strip()]
    if not sentences:
        return []
    
    try:
        embeddings = labse.encode(sentences, batch_size=16, show_progress_bar=False)
        chunks = []
        current_chunk = [sentences[0]]
        current_word_count = len(sentences[0].split())
        
        for i in range(1, len(sentences)):
            similarity = np.dot(embeddings[i-1], embeddings[i]) / (
                np.linalg.norm(embeddings[i-1]) * np.linalg.norm(embeddings[i]) + 1e-8
            )
            
            next_sentence = sentences[i]
            next_word_count = len(next_sentence.split())
            
            should_split = (similarity < threshold and current_word_count >= min_chunk_words) or \
                          (current_word_count + next_word_count > max_chunk_words)
            
            if should_split:
                chunk_text = ' '.join(current_chunk)
                if chunk_text.strip():
                    chunks.append(chunk_text)
                current_chunk = [next_sentence]
                current_word_count = next_word_count
            else:
                current_chunk.append(next_sentence)
                current_word_count += next_word_count
        
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            if current_word_count < min_chunk_words and chunks:
                chunks[-1] += ' ' + chunk_text
            elif chunk_text.strip():
                chunks.append(chunk_text)
        
        return chunks
    
    except Exception as e:
        return [text] if text.strip() else []


def process_pdf(pdf_path):
    """Process PDFs with optimized semantic chunking"""
    chunks = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if not text or not text.strip():
                    continue
                
                page_chunks = semantic_chunk(text)
                
                for chunk_text in page_chunks:
                    if not chunk_text.strip():
                        continue
                    
                    chunk_id = hashlib.md5(
                        f"{pdf_path.name}_{page_num}_{chunk_text[:50]}".encode()
                    ).hexdigest()[:8]
                    
                    chunks.append({
                        'chunk_id': chunk_id,
                        'filename': pdf_path.name,
                        'page': page_num,
                        'text': chunk_text,
                        'language': detect_language(chunk_text),
                        'word_count': len(chunk_text.split()),
                        'trust_score': 0.95 if 'DPIIT' in pdf_path.name or 'Guidelines' in pdf_path.name else 0.85,
                        'canonicals': canonicalize_numerics(chunk_text),
                        'doc_date': datetime.now().isoformat(),
                    })
    
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:50]}")
    
    return chunks


def find_column(col_lower_list, keywords):
    """Helper: Find first column matching any keyword"""
    for idx, col in enumerate(col_lower_list):
        for keyword in keywords:
            if keyword in col:
                return idx
    return None


def process_csv(csv_path):
    """
    Process CSVs with STRICT CONTEXT TEMPLATES (v2.5.2)
    ✅ Requires BOTH entity AND financial columns for funding template
    ✅ Smart column matching
    ✅ Better fallback handling
    """
    chunks = []
    df = None
    
    # Try multiple encodings
    for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
        try:
            df = pd.read_csv(csv_path, encoding=encoding, low_memory=False)
            break
        except:
            continue
    
    if df is None or df.empty:
        return chunks
    
    # Normalize column names
    df.columns = [str(col).strip() for col in df.columns]
    col_lower = [col.lower() for col in df.columns]
    col_str = ' '.join(col_lower)
    
    # ✅ STRICT DETECTION: Must have BOTH entity AND financial columns
    has_entity = any(k in col_str for k in ['startup', 'company', 'organization', 'firm', 'business'])
    has_financial = any(k in col_str for k in ['amount', 'investor', 'round', 'funding', 'series', 'valuation'])
    
    is_funding_data = has_entity and has_financial
    
    # Process each row
    for idx in range(len(df)):
        try:
            row = df.iloc[idx]
            
            if is_funding_data:
                # ✅ SMART TEMPLATE for funding data
                # Find columns using flexible matching
                startup_idx = find_column(col_lower, ['startup', 'company', 'name', 'organization'])
                investor_idx = find_column(col_lower, ['investor', 'investors', 'lead'])
                amount_idx = find_column(col_lower, ['amount', 'funding', 'investment', 'valuation'])
                round_idx = find_column(col_lower, ['round', 'stage', 'series', 'type'])
                year_idx = find_column(col_lower, ['year', 'date', 'founded'])
                sector_idx = find_column(col_lower, ['sector', 'industry', 'vertical', 'category'])
                city_idx = find_column(col_lower, ['city', 'location', 'headquarters'])
                
                # Extract values with validation
                startup = str(row.iloc[startup_idx]).strip() if startup_idx is not None and pd.notna(row.iloc[startup_idx]) else None
                investor = str(row.iloc[investor_idx]).strip() if investor_idx is not None and pd.notna(row.iloc[investor_idx]) else None
                amount = str(row.iloc[amount_idx]).strip() if amount_idx is not None and pd.notna(row.iloc[amount_idx]) else None
                round_type = str(row.iloc[round_idx]).strip() if round_idx is not None and pd.notna(row.iloc[round_idx]) else None
                year = str(row.iloc[year_idx]).strip() if year_idx is not None and pd.notna(row.iloc[year_idx]) else None
                sector = str(row.iloc[sector_idx]).strip() if sector_idx is not None and pd.notna(row.iloc[sector_idx]) else None
                city = str(row.iloc[city_idx]).strip() if city_idx is not None and pd.notna(row.iloc[city_idx]) else None
                
                # Clean values (remove 'nan', empty strings)
                def clean_val(v):
                    if v and v.lower() not in ['nan', 'none', 'null', '']:
                        return v
                    return None
                
                startup = clean_val(startup)
                investor = clean_val(investor)
                amount = clean_val(amount)
                round_type = clean_val(round_type)
                year = clean_val(year)
                sector = clean_val(sector)
                city = clean_val(city)
                
                # Build descriptive sentence (only if we have meaningful data)
                if not startup and not investor and not amount:
                    # Skip empty rows
                    continue
                
                parts = ["Funding Record:"]
                
                if startup:
                    parts.append(startup)
                    if city:
                        parts.append(f"(based in {city})")
                else:
                    parts.append("A startup")
                
                if sector:
                    parts.append(f"in the {sector} sector")
                
                parts.append("raised")
                
                if amount:
                    parts.append(amount)
                else:
                    parts.append("funding")
                
                if investor:
                    parts.append(f"from {investor}")
                
                if round_type:
                    parts.append(f"in a {round_type} round")
                
                if year:
                    # Extract just the year if it's a date
                    year_match = re.search(r'(19|20)\d{2}', year)
                    if year_match:
                        year = year_match.group(0)
                    parts.append(f"in {year}")
                
                text = " ".join(parts) + "."
                
            else:
                # ✅ FALLBACK for non-funding CSVs (government data, patents, etc.)
                values = []
                for val in row.values:
                    if pd.notna(val):
                        val_str = str(val).strip()
                        if val_str and val_str.lower() not in ['nan', 'none', 'null', '']:
                            values.append(val_str)
                
                if not values:
                    continue
                
                # Add descriptive prefix based on filename
                filename_lower = csv_path.name.lower()
                if 'patent' in filename_lower:
                    prefix = "Patent Record:"
                elif 'copyright' in filename_lower:
                    prefix = "Copyright Record:"
                elif 'policy' in filename_lower or 'scheme' in filename_lower:
                    prefix = "Policy Record:"
                elif 'unicorn' in filename_lower:
                    prefix = "Unicorn Startup:"
                else:
                    prefix = "Data Record:"
                
                text = f"{prefix} {', '.join(values[:12])}."
            
            # Create chunk
            chunk_id = hashlib.md5(f"{csv_path.name}_{idx}".encode()).hexdigest()[:8]
            
            chunks.append({
                'chunk_id': chunk_id,
                'filename': csv_path.name,
                'page': idx + 1,
                'text': text,
                'language': 'en',
                'word_count': len(text.split()),
                'trust_score': 0.90,
                'canonicals': canonicalize_numerics(text),
                'doc_date': datetime.now().isoformat(),
            })
            
        except Exception as e:
            # Silently skip bad rows
            continue
    
    return chunks


def process_excel(excel_path):
    """Process Excel files (same logic as CSV)"""
    chunks = []
    df = None
    
    try:
        if excel_path.suffix.lower() == '.xlsx':
            df = pd.read_excel(excel_path, engine='openpyxl')
        else:
            try:
                df = pd.read_excel(excel_path, engine='xlrd')
            except:
                df = pd.read_excel(excel_path)
    except:
        try:
            df = pd.read_excel(excel_path)
        except:
            return chunks
    
    if df is None or df.empty:
        return chunks
    
    # Use same logic as CSV processing
    # Save as temp CSV and process
    temp_csv_path = excel_path.with_suffix('.csv')
    df.to_csv(temp_csv_path, index=False)
    chunks = process_csv(temp_csv_path)
    
    # Update filenames back to original
    for chunk in chunks:
        chunk['filename'] = excel_path.name
    
    # Clean up temp file
    try:
        temp_csv_path.unlink()
    except:
        pass
    
    return chunks


def main():
    raw_dir = Path('../data/raw')
    parsed_dir = Path('../data/parsed')
    parsed_dir.mkdir(parents=True, exist_ok=True)
    
    all_chunks = []
    stats = {
        'pdf_success': 0, 'pdf_fail': 0,
        'csv_success': 0, 'csv_fail': 0,
        'excel_success': 0, 'excel_fail': 0
    }
    
    print("\n" + "="*70)
    print("🚀 GEMA-RAG v2.5.2 - CSV CONTEXT FIX (STRICT)")
    print("="*70)
    print("\n📊 Optimizations:")
    print(f"   PDF Chunking:")
    print(f"     • Threshold: {SEMANTIC_THRESHOLD} (granular)")
    print(f"     • Max size: {MAX_CHUNK_WORDS} words")
    print(f"     • Min size: {MIN_CHUNK_WORDS_PDF} words")
    print(f"   CSV/Excel Chunking:")
    print(f"     ✅ STRICT detection (entity + financial)")
    print(f"     ✅ Smart column matching")
    print(f"     • Robust encoding (4 attempts)")
    print("="*70 + "\n")
    
    # Process PDFs
    pdf_files = list(raw_dir.glob('*.pdf'))
    if pdf_files:
        print(f"📄 Processing {len(pdf_files)} PDF files...")
        for pdf_path in pdf_files:
            print(f"  → {pdf_path.name}")
            try:
                chunks = process_pdf(pdf_path)
                if chunks:
                    all_chunks.extend(chunks)
                    avg_words = sum(c['word_count'] for c in chunks) / len(chunks)
                    print(f"    ✓ {len(chunks)} chunks | Avg: {avg_words:.1f} words")
                    stats['pdf_success'] += 1
                else:
                    print(f"    ⚠️ No chunks extracted")
                    stats['pdf_fail'] += 1
            except Exception as e:
                print(f"    ❌ Failed: {str(e)[:40]}")
                stats['pdf_fail'] += 1
        print()
    
    # Process CSVs
    csv_files = list(raw_dir.glob('*.csv'))
    if csv_files:
        print(f"📊 Processing {len(csv_files)} CSV files...")
        for csv_path in csv_files:
            print(f"  → {csv_path.name}")
            try:
                chunks = process_csv(csv_path)
                if chunks:
                    all_chunks.extend(chunks)
                    print(f"    ✓ {len(chunks)} chunks")
                    stats['csv_success'] += 1
                else:
                    print(f"    ⚠️ No chunks")
                    stats['csv_fail'] += 1
            except Exception as e:
                print(f"    ❌ Failed: {str(e)[:40]}")
                stats['csv_fail'] += 1
        print()
    
    # Process Excel
    excel_files = list(raw_dir.glob('*.xls*'))
    if excel_files:
        print(f"📈 Processing {len(excel_files)} Excel files...")
        for excel_path in excel_files:
            print(f"  → {excel_path.name}")
            try:
                chunks = process_excel(excel_path)
                if chunks:
                    all_chunks.extend(chunks)
                    print(f"    ✓ {len(chunks)} chunks")
                    stats['excel_success'] += 1
                else:
                    print(f"    ⚠️ No chunks")
                    stats['excel_fail'] += 1
            except Exception as e:
                print(f"    ❌ Failed: {str(e)[:40]}")
                stats['excel_fail'] += 1
        print()
    
    # Save all chunks
    output_path = parsed_dir / 'chunks.jsonl'
    with open(output_path, 'w', encoding='utf-8') as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    
    # Calculate statistics
    pdf_chunks = [c for c in all_chunks if c['filename'].endswith('.pdf')]
    csv_chunks = [c for c in all_chunks if c['filename'].endswith('.csv')]
    excel_chunks = [c for c in all_chunks if c['filename'].endswith(('.xls', '.xlsx'))]
    
    print("="*70)
    print("✅ INGESTION COMPLETE")
    print("="*70)
    print(f"\n📊 Overall Statistics:")
    print(f"   Total chunks: {len(all_chunks):,}")
    print(f"   PDFs: {stats['pdf_success']}/{stats['pdf_success']+stats['pdf_fail']}")
    print(f"   CSVs: {stats['csv_success']}/{stats['csv_success']+stats['csv_fail']}")
    print(f"   Excel: {stats['excel_success']}/{stats['excel_success']+stats['excel_fail']}")
    
    if pdf_chunks:
        avg_pdf_words = sum(c['word_count'] for c in pdf_chunks) / len(pdf_chunks)
        median_pdf_words = sorted([c['word_count'] for c in pdf_chunks])[len(pdf_chunks)//2]
        print(f"\n📄 PDF Chunks (Optimized):")
        print(f"   Count: {len(pdf_chunks):,}")
        print(f"   Avg: {avg_pdf_words:.1f} words")
        print(f"   Median: {median_pdf_words:.1f} words")
    
    if csv_chunks or excel_chunks:
        csv_excel = csv_chunks + excel_chunks
        avg_csv_words = sum(c['word_count'] for c in csv_excel) / len(csv_excel)
        print(f"\n📊 CSV/Excel Chunks (With Smart Context):")
        print(f"   Count: {len(csv_excel):,}")
        print(f"   Avg: {avg_csv_words:.1f} words")
        print(f"   ✅ Strict detection + Smart matching applied!")
    
    print(f"\n💾 Output: {output_path.absolute()}")
    
    print(f"\n✨ Why This Is Best:")
    print(f"   ✅ PDF chunks optimized (semantic chunking)")
    print(f"   ✅ CSV chunks have RICH CONTEXT")
    print(f"   ✅ Strict detection (entity + financial required)")
    print(f"   ✅ Expected avg CSV words: 30-45")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. python build_index.py")
    print(f"   2. python build_knowledge_graph.py")
    print(f"   3. python unified_rag.py")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
