"""
GEMA-RAG v2.4.0 - Code-Mixing Handler
- Method 3: Query Expansion ✓
- Method 7: Enhanced Translation ✓
"""

import re
from deep_translator import GoogleTranslator

# Language detection
HINDI_STOPWORDS = {'ka', 'ki', 'ke', 'hai', 'hain', 'ko', 'se', 'me', 'par', 'kya', 'kitna', 'kaise', 'kab', 'kahan', 'kyon'}
TAMIL_STOPWORDS = {'enna', 'yenna', 'eppadi', 'eppo', 'enga', 'ethana', 'antha', 'intha', 'da', 'na', 'illa'}
TELUGU_STOPWORDS = {'emi', 'ela', 'eppudu', 'ekkada', 'enta', 'aa', 'ee', 'lo', 'ki', 'ni', 'ledu'}

LANGUAGE_NAMES = {
    'hi': 'Hindi (हिंदी)',
    'ta': 'Tamil (தமிழ்)',
    'te': 'Telugu (తెలుగు)',
    'kn': 'Kannada (ಕನ್ನಡ)',
    'ml': 'Malayalam (മലയാളം)',
    'en': 'English'
}

# Method 3: Query Expansion Mappings
QUERY_EXPANSIONS = {
    'funding': ['investment', 'capital', 'finance', 'fund', 'money'],
    'investment': ['funding', 'capital', 'finance'],
    'capital': ['funding', 'investment', 'finance'],
    'startup': ['company', 'venture', 'business', 'enterprise', 'firm'],
    'company': ['startup', 'venture', 'business', 'enterprise'],
    'venture': ['startup', 'company', 'business'],
    'grant': ['funding', 'subsidy', 'financial support', 'aid'],
    'subsidy': ['grant', 'financial support', 'aid'],
    'support': ['aid', 'assistance', 'help'],
    'scheme': ['program', 'initiative', 'plan', 'policy'],
    'program': ['scheme', 'initiative', 'plan'],
    'initiative': ['scheme', 'program', 'plan'],
    'apply': ['application', 'registration', 'enroll'],
    'eligible': ['qualification', 'criteria', 'requirement'],
    'eligibility': ['qualification', 'criteria', 'requirement'],
    'maximum': ['highest', 'max', 'top'],
    'minimum': ['lowest', 'min'],
    'amount': ['sum', 'value', 'quantum'],
    'seed': ['early stage', 'initial'],
}


def expand_query(query, lang='en', max_expansions=3, verbose=False):
    """
    Method 3: Expand query with domain-specific synonyms
    """
    if lang not in ['en']:
        return query
    
    query_lower = query.lower()
    expanded_terms = []
    matched_keywords = []
    
    for keyword, synonyms in QUERY_EXPANSIONS.items():
        if keyword.lower() in query_lower:
            matched_keywords.append(keyword)
            expanded_terms.extend(synonyms[:max_expansions])
    
    expanded_terms = [term for term in set(expanded_terms) if term.lower() not in query_lower]
    expanded_terms = expanded_terms[:5]
    
    if expanded_terms:
        expanded_query = query + ' ' + ' '.join(expanded_terms)
        
        if verbose:
            print(f"  🔍 Query expansion applied:")
            print(f"     Original keywords: {', '.join(matched_keywords)}")
            print(f"     Added terms: {', '.join(expanded_terms)}")
        
        return expanded_query
    
    return query


def detect_code_mixing(query):
    """Detect code-mixing"""
    words = query.lower().split()
    
    hindi_count = sum(1 for w in words if w in HINDI_STOPWORDS)
    tamil_count = sum(1 for w in words if w in TAMIL_STOPWORDS)
    telugu_count = sum(1 for w in words if w in TELUGU_STOPWORDS)
    
    if hindi_count > 0:
        return True, 'hi'
    elif tamil_count > 0:
        return True, 'ta'
    elif telugu_count > 0:
        return True, 'te'
    
    return False, 'en'


def detect_pure_indic(query):
    """Detect pure Indic language using character sets"""
    devanagari = len(re.findall(r'[\u0900-\u097F]', query))
    tamil = len(re.findall(r'[\u0B80-\u0BFF]', query))
    telugu = len(re.findall(r'[\u0C00-\u0C7F]', query))
    kannada = len(re.findall(r'[\u0C80-\u0CFF]', query))
    malayalam = len(re.findall(r'[\u0D00-\u0D7F]', query))
    
    total_chars = len(query.replace(' ', ''))
    
    if total_chars == 0:
        return False, 'en'
    
    if devanagari / total_chars > 0.5:
        return True, 'hi'
    elif tamil / total_chars > 0.5:
        return True, 'ta'
    elif telugu / total_chars > 0.5:
        return True, 'te'
    elif kannada / total_chars > 0.5:
        return True, 'kn'
    elif malayalam / total_chars > 0.5:
        return True, 'ml'
    
    return False, 'en'


def translate_to_english(query, source_lang='hi'):
    """
    Method 7: Enhanced translation with entity preservation
    """
    try:
        # Domain terms to protect from translation
        domain_terms = [
            'SISFS', 'DPIIT', 'startup', 'Startup India', 'Zepto', 'seed fund', 
            'grant', 'SIDBI', 'Series A', 'Series B', 'Series C', 'Series D', 
            'Series E', 'funding round', 'crore', 'lakh', 'Rs'
        ]
        
        protected_query = query
        protection_map = {}
        
        # Protect domain terms
        for i, term in enumerate(domain_terms):
            if term.lower() in query.lower():
                placeholder = f"___PROTECTED_{i}___"
                protected_query = re.sub(re.escape(term), placeholder, 
                                        protected_query, flags=re.IGNORECASE)
                protection_map[placeholder] = term
        
        # Translate
        translator = GoogleTranslator(source=source_lang, target='en')
        translated = translator.translate(protected_query)
        
        # Restore protected terms
        for placeholder, original_term in protection_map.items():
            translated = translated.replace(placeholder, original_term)
        
        # Restore uppercase entities
        entities = re.findall(r'\b[A-Z]{2,}\b', query)
        for entity in entities:
            translated = re.sub(entity.lower(), entity, translated, flags=re.IGNORECASE)
        
        return translated.strip()
    
    except Exception as e:
        print(f"  ⚠️ Translation error: {e}")
        return query


def translate_from_english(text, target_lang='hi'):
    """
    Method 7: Enhanced back-translation with preservation
    """
    if target_lang == 'en':
        return text
    
    try:
        # Protect monetary amounts
        amount_pattern = r'Rs\.?\s*\d+[\d,]*(?:\.\d+)?\s*(?:Crore|Lakh|Million|Billion)?'
        amounts = re.findall(amount_pattern, text, re.IGNORECASE)
        
        protected_text = text
        protection_map = {}
        
        # Protect amounts
        for i, amount in enumerate(amounts):
            placeholder = f"___AMOUNT_{i}___"
            protected_text = protected_text.replace(amount, placeholder)
            protection_map[placeholder] = amount
        
        # Protect domain terms
        domain_terms = ['SISFS', 'DPIIT', 'Startup India', 'SIDBI', 
                       'Series E', 'Series D', 'Series C', 'Series B', 'Series A']
        for i, term in enumerate(domain_terms):
            if term in protected_text:
                placeholder = f"___TERM_{i}___"
                protected_text = protected_text.replace(term, placeholder)
                protection_map[placeholder] = term
        
        # Translate
        translator = GoogleTranslator(source='en', target=target_lang)
        translated = translator.translate(protected_text)
        
        # Restore protected content
        for placeholder, original in protection_map.items():
            translated = translated.replace(placeholder, original)
        
        # Clean up artifacts
        translated = re.sub(r'रु\.', 'Rs.', translated)
        translated = re.sub(r'ரூ\.', 'Rs.', translated)
        
        return translated.strip()
    
    except Exception as e:
        print(f"  ⚠️ Translation error: {e}")
        return text


def handle_multilingual_query(query, verbose=True, expand_queries=True):
    """
    Main handler with Methods 3, 7
    """
    # Detect pure Indic
    is_pure_indic, pure_lang = detect_pure_indic(query)
    
    if is_pure_indic:
        if verbose:
            lang_name = LANGUAGE_NAMES.get(pure_lang, pure_lang.upper())
            print(f"  🌏 Pure {lang_name} detected")
            print(f"  📝 Original query: {query}")
        
        # Method 7: Enhanced translation
        translated_query = translate_to_english(query, source_lang=pure_lang)
        
        if verbose:
            print(f"  ✅ Translated to English: {translated_query}")
        
        # Method 3: Query expansion
        if expand_queries:
            expanded_query = expand_query(translated_query, lang='en', verbose=verbose)
            translated_query = expanded_query
        
        return translated_query, pure_lang, True
    
    # Detect code-mixing
    is_mixed, mixed_lang = detect_code_mixing(query)
    
    if is_mixed:
        if verbose:
            lang_name = LANGUAGE_NAMES.get(mixed_lang, mixed_lang.upper())
            print(f"  🔀 Code-mixing detected: {lang_name}+English")
            print(f"  📝 Original query: {query}")
        
        translated_query = translate_to_english(query, source_lang=mixed_lang)
        
        if verbose:
            print(f"  ✅ Translated to English: {translated_query}")
        
        if expand_queries:
            expanded_query = expand_query(translated_query, lang='en', verbose=verbose)
            translated_query = expanded_query
        
        return translated_query, mixed_lang, True
    
    # Pure English with expansion
    if expand_queries:
        expanded_query = expand_query(query, lang='en', verbose=verbose)
        return expanded_query, 'en', False
    
    return query, 'en', False


if __name__ == '__main__':
    test_queries = [
        "What is the maximum grant amount?",
        "SISFS ka maximum grant kitna hai?",
        "SISFS के तहत अधिकतम अनुदान राशि क्या है?",
        "How to apply for seed funding?",
    ]
    
    print("="*70)
    print("🧪 Testing Methods 3 & 7")
    print("="*70 + "\n")
    
    for query in test_queries:
        print(f"Input: {query}")
        processed, lang, needs_back = handle_multilingual_query(query, verbose=True, expand_queries=True)
        print(f"Final: {processed}")
        print(f"Language: {lang}\n")
        print("-" * 70)
