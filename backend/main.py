from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import traceable
import google.generativeai as genai

# Add current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from database import FAQDatabase

load_dotenv()

# Initialize LangSmith if available
langsmith_enabled = False
try:
    from langsmith_config import setup_langsmith
    setup_langsmith()
    langsmith_enabled = True
    print("✅ LangSmith tracking enabled")
except Exception as e:
    print(f"⚠️  LangSmith not configured: {e}")

app = FastAPI(title="FAQ Bot API - Multi-AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
db = FAQDatabase()

# AI Components - initialize separately
openai_available = False
gemini_available = False
llm_chain = None
gemini_model = None
working_model = None

# Try to initialize OpenAI/LangChain (skip if problematic)
if os.getenv("OPENAI_API_KEY"):
    try:
        from langchain_openai import OpenAI
        from langchain.prompts import PromptTemplate
        from langchain.chains import LLMChain

        llm = OpenAI(
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model_name="gpt-3.5-turbo-instruct"
        )

        prompt_template = PromptTemplate(
            input_variables=["question", "context"],
            template="""You are a helpful FAQ bot. Based on the following FAQ information, provide a natural and helpful response to the user's question.

FAQ Context:
{context}

User Question: {question}

Please provide a clear, concise, and helpful response. If the FAQ context doesn't fully answer the question, acknowledge what you know and suggest contacting customer support for more specific help.

Response:"""
        )

        llm_chain = LLMChain(llm=llm, prompt=prompt_template)
        openai_available = True
        print("✅ OpenAI/LangChain initialized successfully")

    except Exception as e:
        print(f"⚠️  OpenAI/LangChain initialization failed: {e}")
        openai_available = False

# Try to initialize Gemini
if os.getenv("GOOGLE_API_KEY"):
    try:
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

        # Try different model names - some regions have different available models
        model_names_to_try = [
            'gemini-1.5-flash',
            'gemini-1.5-pro',
            'gemini-pro',
            'models/gemini-pro',
            'models/gemini-1.5-flash'
        ]

        gemini_model = None
        working_model = None

        for model_name in model_names_to_try:
            try:
                print(f"🧪 Trying model: {model_name}")
                test_model = genai.GenerativeModel(model_name)
                # Test with a simple generation
                test_response = test_model.generate_content("Hello")
                if test_response.text:
                    gemini_model = test_model
                    working_model = model_name
                    print(f"✅ Working model found: {model_name}")
                    break
            except Exception as model_error:
                print(f"❌ Model {model_name} failed: {model_error}")
                continue

        if gemini_model:
            gemini_available = True
            print(f"✅ Google Gemini initialized successfully with model: {working_model}")
        else:
            print("❌ No working Gemini models found")
            gemini_available = False

    except Exception as e:
        print(f"⚠️  Gemini initialization failed: {e}")
        gemini_available = False
else:
    print("⚠️  No GOOGLE_API_KEY found")
    gemini_available = False

# Gemini response function with LangSmith tracking
@traceable(
    name="gemini_generate_response",
    metadata={
        "provider": "google",
        "model": lambda: working_model or "gemini-unknown",
        "framework": "direct_api"
    }
)
def generate_gemini_response(question: str, context: str) -> str:
    """Generate response using Google Gemini with LangSmith tracking"""
    if not gemini_model:
        print("❌ Gemini model not initialized")
        return None

    try:
        # Create comprehensive prompt
        prompt = f"""You are a helpful FAQ bot. Based on the following FAQ information, provide a natural and helpful response to the user's question.

FAQ Context:
{context}

User Question: {question}

Please provide a clear, concise, and helpful response. If the FAQ context doesn't fully answer the question, acknowledge what you know and suggest contacting customer support for more specific help.

Response:"""

        print(f"🚀 Sending to Gemini ({working_model})...")

        # Configure generation parameters
        generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=500,
            top_p=0.9,
            top_k=40
        )

        response = gemini_model.generate_content(
            prompt,
            generation_config=generation_config
        )

        if hasattr(response, 'text') and response.text:
            print(f"✅ Got Gemini response: {len(response.text)} chars")
            return response.text.strip()
        else:
            print(f"❌ No text in Gemini response")
            return None

    except Exception as e:
        print(f"❌ Gemini error: {e}")
        # Re-raise for LangSmith to track the error
        raise e

# OpenAI response function (already tracked by LangChain)
def generate_openai_response(question: str, context: str) -> str:
    """Generate response using OpenAI/LangChain (automatically tracked)"""
    if not llm_chain:
        return None

    try:
        response = llm_chain.run(question=question, context=context)
        return response.strip() if response else None

    except Exception as e:
        print(f"OpenAI generation error: {e}")
        # Check if it's a quota error
        if "quota" in str(e).lower() or "insufficient" in str(e).lower():
            print("🚫 OpenAI quota exceeded - falling back to Gemini")
        return None

class QuestionRequest(BaseModel):
    question: str

class FAQResponse(BaseModel):
    question: str
    answer: str
    relevant_faqs: List[dict]
    confidence: Optional[str] = None
    ai_provider: Optional[str] = None
    langsmith_enabled: Optional[bool] = None

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        if db.get_collection_count() == 0:
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "../data/faq_data.json"),
                os.path.join(os.getcwd(), "data/faq_data.json"),
                "data/faq_data.json",
                "../data/faq_data.json"
            ]

            faq_data_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    faq_data_path = path
                    break

            if faq_data_path:
                db.populate_database(faq_data_path)
                print(f"✅ Database populated from {faq_data_path}")
            else:
                print("⚠️  FAQ data file not found")
        else:
            print(f"✅ Database already contains {db.get_collection_count()} entries")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

@app.get("/")
async def root():
    return {
        "message": "FAQ Bot API - Multi-AI Support with LangSmith",
        "ai_providers": {
            "openai_available": openai_available,
            "gemini_available": gemini_available,
            "gemini_model": working_model if gemini_available else None
        },
        "monitoring": {
            "langsmith_enabled": langsmith_enabled
        },
        "database_entries": db.get_collection_count()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database_entries": db.get_collection_count(),
        "ai_providers": {
            "openai": openai_available,
            "gemini": gemini_available
        },
        "monitoring": {
            "langsmith": langsmith_enabled
        },
        "total_ai_options": sum([openai_available, gemini_available])
    }

@traceable(name="faq_bot_conversation")
@app.post("/ask", response_model=FAQResponse)
async def ask_question(request: QuestionRequest):
    """Main FAQ endpoint with full LangSmith tracking"""
    try:
        # Search for relevant FAQs
        try:
            relevant_faqs = db.search_faqs(request.question, n_results=3)
        except TypeError:
            try:
                relevant_faqs = db.search_faqs(request.question, top_k=3)
            except Exception as e:
                print(f"Database search error: {e}")
                relevant_faqs = []

        if not relevant_faqs:
            return FAQResponse(
                question=request.question,
                answer="I don't have information about that specific question. Please contact our support team for assistance.",
                relevant_faqs=[],
                confidence="low",
                ai_provider="none",
                langsmith_enabled=langsmith_enabled
            )

        # Create context from relevant FAQs
        context = "\n".join([
            f"Q: {faq.get('question', faq.get('metadata', {}).get('question', 'Unknown'))}\nA: {faq.get('answer', faq.get('metadata', {}).get('answer', 'Unknown'))}"
            for faq in relevant_faqs
        ])

        # Try AI response generation - OpenAI first, then Gemini fallback
        ai_response = None
        ai_provider = "none"

        # Try OpenAI first (automatically tracked by LangChain)
        if openai_available:
            ai_response = generate_openai_response(request.question, context)
            if ai_response:
                ai_provider = "openai"
                print(f"✅ OpenAI response generated for: {request.question}")

        # Fallback to Gemini if OpenAI failed (now tracked!)
        if not ai_response and gemini_available:
            ai_response = generate_gemini_response(request.question, context)
            if ai_response:
                ai_provider = "gemini"
                print(f"✅ Gemini response generated for: {request.question}")

        # Final fallback to first FAQ if no AI worked
        if not ai_response:
            first_faq = relevant_faqs[0]
            ai_response = first_faq.get('answer', first_faq.get('metadata', {}).get('answer', 'No answer available'))
            ai_provider = "fallback"
            print(f"⚠️  Using fallback response for: {request.question}")

        return FAQResponse(
            question=request.question,
            answer=ai_response.strip() if isinstance(ai_response, str) else str(ai_response),
            relevant_faqs=relevant_faqs,
            confidence="high" if len(relevant_faqs) >= 2 else "medium",
            ai_provider=ai_provider,
            langsmith_enabled=langsmith_enabled
        )

    except Exception as e:
        print(f"Error processing question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/faqs")
async def get_all_faqs():
    """Get all available FAQs for reference"""
    try:
        count = db.get_collection_count()
        if count == 0:
            return {"faqs": [], "message": "No FAQs in database"}

        try:
            all_faqs = db.search_faqs("", n_results=count)
        except:
            try:
                all_faqs = db.search_faqs("", top_k=count)
            except:
                all_faqs = []

        return {"faqs": all_faqs, "count": len(all_faqs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving FAQs: {str(e)}")

@app.get("/debug")
async def debug_info():
    """Debug endpoint to check system status"""
    return {
        "working_directory": os.getcwd(),
        "env_vars": {
            "OPENAI_API_KEY": "Set" if os.getenv("OPENAI_API_KEY") else "Not set",
            "GOOGLE_API_KEY": "Set" if os.getenv("GOOGLE_API_KEY") else "Not set",
            "LANGCHAIN_API_KEY": "Set" if os.getenv("LANGCHAIN_API_KEY") else "Not set",
        },
        "ai_status": {
            "openai_available": openai_available,
            "gemini_available": gemini_available,
            "gemini_model": working_model,
            "fallback_mode": not (openai_available or gemini_available)
        },
        "monitoring": {
            "langsmith_enabled": langsmith_enabled
        },
        "database_count": db.get_collection_count()
    }

# Test individual AI providers with tracking
@traceable(name="test_openai_endpoint")
@app.post("/test-openai")
async def test_openai_response(request: QuestionRequest):
    """Test OpenAI specifically"""
    if not openai_available:
        raise HTTPException(status_code=503, detail="OpenAI not available")

    response = generate_openai_response(request.question, "Test context")
    return {"provider": "openai", "response": response, "status": "success" if response else "failed"}

@traceable(name="test_gemini_endpoint")
@app.post("/test-gemini")
async def test_gemini_response(request: QuestionRequest):
    """Test Gemini specifically"""
    if not gemini_available:
        raise HTTPException(status_code=503, detail="Gemini not available")

    response = generate_gemini_response(request.question, "Test context")
    return {"provider": "gemini", "response": response, "status": "success" if response else "failed"}

# New endpoint for LangSmith feedback
@app.post("/feedback")
async def submit_feedback(run_id: str, score: float, comment: str = ""):
    """Submit user feedback for LangSmith tracking"""
    if not langsmith_enabled:
        return {"success": False, "message": "LangSmith not enabled"}

    try:
        from langsmith_config import log_feedback
        success = log_feedback(run_id, score, comment)
        return {"success": success, "message": "Feedback logged" if success else "Failed to log feedback"}
    except Exception as e:
        return {"success": False, "message": f"Error: {e}"}

# New endpoint to get monitoring stats
@app.get("/monitoring/stats")
async def get_monitoring_stats():
    """Get basic monitoring statistics"""
    return {
        "langsmith_enabled": langsmith_enabled,
        "ai_providers": {
            "openai": {
                "available": openai_available,
                "tracked": openai_available  # LangChain auto-tracks
            },
            "gemini": {
                "available": gemini_available,
                "model": working_model,
                "tracked": langsmith_enabled  # Only tracked if LangSmith enabled
            }
        },
        "database": {
            "entries": db.get_collection_count(),
            "status": "healthy" if db.get_collection_count() > 0 else "empty"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)