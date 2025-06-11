from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import Dict
from g4f.client import Client

# FastAPI app with security and metadata
app = FastAPI(
    title="KinoVerse Movie Assistant API",
    description="Production-grade API for KinoVerse - AI-powered movie assistant",
    version="1.4.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    dependencies=[Depends(APIKeyHeader(name="X-API-KEY"))]
)

# Professional security implementation
api_key_header = APIKeyHeader(name="X-API-KEY")
VALID_API_KEY = "k1n0V3rs3-Pr0d-2025-S3cr3t"

# System prompt with comprehensive movie knowledge
EXPANDED_SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are KinoVerse, an expert movie assistant AI with extensive film knowledge. Your capabilities include:\n\n"
        "1. Providing detailed movie information: plots, cast/crew, trivia, release details\n"
        "2. Making personalized recommendations based on preferences\n"
        "3. Comparing films across genres and eras\n"
        "4. Analyzing themes, symbolism, and film techniques\n"
        "5. Tracking industry news and awards season updates\n\n"
        "Response Guidelines:\n"
        "- Always cite multiple sources when possible\n"
        "- Prioritize accuracy over speculation\n"
        "- Warn about spoilers before revealing plot details\n"
        "- Provide streaming availability information\n"
        "- Compare critical reception vs audience ratings\n"
        "- For recommendations, suggest contemporary and classic options\n"
        "- Format responses with clear section headers\n"
        "- Never provide illegal streaming sources"
    )
}

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, list] = {}

    def create_session(self, chat_id: str, first_message: str):
        self.sessions[chat_id] = [
            EXPANDED_SYSTEM_PROMPT,
            {"role": "user", "content": first_message}
        ]
        return chat_id

    def add_message(self, chat_id: str, message: str, role: str = "user"):
        if chat_id not in self.sessions:
            raise KeyError("Session not found")
        self.sessions[chat_id].append({"role": role, "content": message})
        
    def get_session(self, chat_id: str):
        return self.sessions.get(chat_id, None)
    
    def delete_session(self, chat_id: str):
        if chat_id in self.sessions:
            del self.sessions[chat_id]

session_manager = SessionManager()

class KinoVerseAIClient:
    def __init__(self):
        self.client = Client()
    
    def query(self, messages: list) -> str:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                web_search=True,
                timeout=15
            )
            return response.choices[0].message.content
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"AI service unavailable: {str(e)}"
            )

ai_client = KinoVerseAIClient()

class SessionResponse(BaseModel):
    status: str
    session_id: str

class AIResponse(BaseModel):
    response: str

class ErrorResponse(BaseModel):
    error: str
    details: str = None

@app.post("/chat/sessions", 
          response_model=SessionResponse,
          responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def create_chat_session(
    starting_message: str = Query(..., min_length=3),
    api_key: str = Depends(api_key_header)
):
    """Create new chat session with starting message"""
    if api_key != VALID_API_KEY:
        raise HTTPException(
            status_code=401, 
            detail={"error": "Unauthorized", "details": "Invalid API Key"}
        )
    
    import uuid
    session_id = str(uuid.uuid4())
    session_manager.create_session(session_id, starting_message)
    
    messages = session_manager.get_session(session_id)
    response = ai_client.query(messages)
    session_manager.add_message(session_id, response, "assistant")
    
    return {"status": "created", "session_id": session_id}

@app.post("/chat/sessions/{session_id}/messages", 
          response_model=AIResponse,
          responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def send_message(
    session_id: str,
    message: str = Query(..., min_length=1),
    api_key: str = Depends(api_key_header)
):
    """Send a message to an existing chat session"""
    if api_key != VALID_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if session_id not in session_manager.sessions:
        raise HTTPException(
            status_code=404, 
            detail={"error": "Session not found", "details": "Create session first"}
        )
    
    session_manager.add_message(session_id, message)
    messages = session_manager.get_session(session_id)
    response = ai_client.query(messages)
    session_manager.add_message(session_id, response, "assistant")
    
    return {"response": response}

@app.delete("/chat/sessions/{session_id}", 
            response_model=dict,
            responses={404: {"model": ErrorResponse}})
async def delete_session(
    session_id: str,
    api_key: str = Depends(api_key_header)
):
    if api_key != VALID_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if session_id not in session_manager.sessions:
        raise HTTPException(
            status_code=404, 
            detail={"error": "Session not found"}
        )
    
    session_manager.delete_session(session_id)
    return {"status": "deleted", "session_id": session_id}

@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "active", "service": "KinoVerse API"}

@app.get("/services", include_in_schema=False)
async def list_services():
    return {
        "ai_model": "gpt-4o-mini", 
        "features": ["web_search", "session_mgmt", "film_db_query"],
        "schema_version": "1.4"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)
