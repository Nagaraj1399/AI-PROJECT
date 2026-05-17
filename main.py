import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pydantic
from agent_service import agent_service

app = FastAPI(
    title="SHL Assessment Chat Recommendation Agent API",
    description="Stateless agent service for matching, clarifying, refining, and comparing SHL assessments.",
    version="1.0.0"
)

# Enable CORS for maximum client-side integration flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(pydantic.BaseModel):
    role: str
    content: str

class ChatRequest(pydantic.BaseModel):
    # Support both 'history' and 'messages' for maximum client compatibility and robustness
    history: list[Message] = None
    messages: list[Message] = None

class RecommendationOut(pydantic.BaseModel):
    name: str
    url: str
    test_type: str

class ChatResponseOut(pydantic.BaseModel):
    reply: str
    recommendations: list[RecommendationOut]
    end_of_conversation: bool

@app.get("/health")
def health():
    """Readiness probe endpoint for health monitoring."""
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponseOut)
def chat(request: ChatRequest):
    """
    Stateless multi-turn recommendation chat endpoint.
    Takes the conversation history and returns the next agent response and shortlist.
    """
    history_source = request.history or request.messages
    if not history_source:
        raise HTTPException(
            status_code=400, 
            detail="Conversation history is required. Please provide it in 'history' or 'messages'."
        )
    
    # Map to standard format list of dicts for agent_service
    messages_list = [
        {"role": msg.role, "content": msg.content}
        for msg in history_source
    ]
    
    try:
        # Call agent service
        result = agent_service.chat(messages_list)
        return result
    except Exception as e:
        # Catch-all exception handling to ensure server never crashes
        print(f"Error handling /chat endpoint: {e}")
        return {
            "reply": "I am experiencing an issue processing this request. Please try again.",
            "recommendations": [],
            "end_of_conversation": False
        }

if __name__ == "__main__":
    import uvicorn
    # Allow running directly via python main.py
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
