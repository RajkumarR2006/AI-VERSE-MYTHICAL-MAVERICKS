import os
import re
from groq import Groq
from dotenv import load_dotenv
import json
import random
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Groq Client
groq_client = Groq(api_key=os.getenv("write your api key"))

# Load FAQ Data
try:
    with open('../data/sisfs_facts.json', 'r') as f:
        faq_data = json.load(f)
    print(f"✓ Loaded {len(faq_data)} FAQ entries from sisfs_facts.json")
except:
    print("⚠️ FAQ file not found. FAQ lookup disabled.")
    faq_data = {}

def check_faq(query):
    """
    Checks if the query matches a static FAQ entry.
    """
    query_lower = query.lower()
    for key, entry in faq_data.items():
        if key.lower() in query_lower:
            return {
                "answer": entry['answer'],
                "confidence": 1.0,
                "source": "FAQ"
            }
    return None

def handle_chitchat(query):
    """
    Handles conversational queries using the LLM (Gen AI mode).
    Does NOT search the vector database.
    """
    try:
        prompt = f"""
        SYSTEM ROLE: You are Aura, a friendly and professional AI Startup Consultant for India.
        
        USER INPUT: "{query}"
        
        INSTRUCTIONS:
        1. The user is engaging in casual conversation (small talk, greeting, or personal questions).
        2. **Be Generative:** Reply naturally and warmly. Do not use canned responses.
        3. **Stay in Persona:** You are helpful, polite, and professional. 
        4. **The Pivot:** After answering the small talk, gently ask if they need help with **Indian Startups, Funding Schemes, or Government Policy**.
        5. **No Hallucinations:** Do NOT invent startup data for personal questions.
        
        ANSWER:
        """
        
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant named Aura."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=150
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return "I'm here and ready to help! (System note: LLM connection issue)"

def generate_answer(query, context_chunks):
    """
    Generates a professional answer with DYNAMIC openings in the Target Language.
    """
    # 1. Prepare Context (Robust check for both flat and nested 'chunk' data)
    num_sources = len(context_chunks)
    context_text = ""
    
    for i, item in enumerate(context_chunks, 1):
        # Safety check: Handle both flat data and nested 'chunk' data
        data = item.get('chunk', item)
        
        filename = data.get('filename', 'Source')
        page = data.get('page', 'N/A')
        text = data.get('text', '')
        
        context_text += f"\n[Source {i}] {filename} (Page {page})\n{text}\n"

    # 2. Dynamic Persona
    personas = [
        "an experienced Startup Consultant for the Indian market.",
        "a Government Policy Advisor helping MSMEs navigate schemes.",
        "a strategic Investment Analyst explaining funding opportunities."
    ]
    current_persona = random.choice(personas)
    
    # 3. Current Time
    current_time = datetime.now().strftime("%I:%M %p")
    
    # 4. The Updated Prompt (Fixes Repetition & Language Mismatch)
    prompt = f"""
    ROLE: You are Aura, {current_persona}
    CURRENT TIME: {current_time}
    
    TASK: Answer the user's question using the provided Context.
    
    STRICT GUIDELINES:
    1. **Dynamic Opening (CRITICAL):** - Start with a professional opening sentence strictly in the **SAME LANGUAGE** as the User's Question.
       - **DO NOT** use "That is a great question" every time. 
       - **Vary your openings.** Examples (Translate these to the target language): 
         * "Here is the detailed analysis based on the documents..."
         * "I have found the specific information you are looking for..."
         * "According to the startup policy reports..."
         * "Let's look at the funding details..."
    
    2. **Generative Synthesis:** Do not just copy-paste. Read the context, understand the intent, and explain it clearly in your own professional voice.
    3. **Clarity & Detail:** Explain the answer clearly and in detail. Ensure the user fully understands the 'Why' and 'How'.
    4. **Formatting:** - Use **Bold text** for key terms, numbers, and important headings.
       - Use bullet points for steps or lists.
       - Break long paragraphs into smaller chunks.
    5. **Citation:** You MUST cite sources as [Source 1], [Source 2] etc. immediately after the fact.
    6. **Language Rule:** The ENTIRE response (Opening + Content) must be in the **SAME LANGUAGE** as the user's question (English, Hindi, or Tamil). Ensure the answer is complete and does not cut off.
    7. **Safety:** If the answer is not in the context, politely state that you don't have that specific information.
    
    CONTEXT:
    {context_text}
    
    USER QUESTION: {query}
    
    ANSWER:
    """
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are Aura, a professional AI consultant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4, # Slightly higher to encourage varied openings
            max_tokens=1500  # High limit for Tamil/Hindi
        )
        
        answer = response.choices[0].message.content.strip()
        
        # Citation Safety Check
        citations = re.findall(r'\[Source (\d+)\]', answer)
        for cite in citations:
            if int(cite) > num_sources:
                answer = answer.replace(f'[Source {cite}]', f'[Source {num_sources}]')
        
        return answer

    except Exception as e:
        return f"❌ Error generating answer: {str(e)}"
    
# Legacy wrapper support
def answer_question(query, silent=False):
    pass