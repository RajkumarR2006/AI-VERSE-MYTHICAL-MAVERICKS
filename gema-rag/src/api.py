from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from unified_rag import UnifiedRAG  # Direct import

# --- CONFIGURATION ---
app = FastAPI(title="GEMA-RAG API")

# Allow Vercel to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Variable for the Brain
rag_system = None

class QueryRequest(BaseModel):
    question: str

@app.on_event("startup")
def startup_event():
    """Initialize the Advanced RAG System on Startup"""
    global rag_system
    print("\n" + "="*50)
    print("🚀 BOOTING UP GEMA-RAG V2.3 (PRODUCTION)...")
    print("="*50)
    try:
        # This initializes the Router, Graph, Semantic Engine, and Verifier
        rag_system = UnifiedRAG()
        print("✅ GEMA-RAG is Online and Ready!")
    except Exception as e:
        print(f"❌ CRITICAL ERROR during startup: {e}")

@app.post("/chat")
async def chat_endpoint(request: QueryRequest):
    """The Main Endpoint that Vercel calls"""
    global rag_system
    
    print(f"\n📩 RECEIVED: {request.question}")

    if not rag_system:
        raise HTTPException(status_code=503, detail="System is still booting up.")

    try:
        # 1. Ask the Super Brain (Triggering the 4-Lane Highway)
        response = rag_system.answer(request.question, verbose=True)

        # 2. Extract Answer components
        final_answer = response.get('answer', "I could not generate an answer.")
        source_layer = response.get('source', 'UNKNOWN')
        is_verified = response.get('verified', False) # Capture Verification Status
        
        formatted_sources = []

        # 3. Format Sources based on Layer
        if source_layer == 'SEMANTIC':
            raw_sources = response.get('sources', [])
            for item in raw_sources[:3]: 
                chunk = item.get('chunk', {})
                formatted_sources.append({
                    "source": chunk.get('filename', 'Unknown Document'),
                    "content": f"Page {chunk.get('page', '?')}: {chunk.get('text', '')[:150]}..."
                })
        
        elif source_layer == 'GRAPH':
            formatted_sources.append({
                "source": "Knowledge Graph 🕸️",
                "content": "Derived from structured relationships in the database."
            })

        elif source_layer == 'FAQ':
             formatted_sources.append({
                "source": "Official FAQ Database 📚",
                "content": "Verified answer from the SISFS official guidelines."
            })
        
        elif source_layer == 'CHAT':
             # No sources for greetings
             pass

        # 4. Return Full Response to Frontend
        is_verified = response.get('verified', False)

        return {
            "answer": final_answer,
            "sources": formatted_sources,
            "verified": is_verified,  # Now sending verification status!
            "type": source_layer
        }

    except Exception as e:
        print(f"❌ ERROR generating answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))