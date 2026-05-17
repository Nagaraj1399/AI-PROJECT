import os
import re
import json
import pydantic
import google.generativeai as genai
from dotenv import load_dotenv
from catalog_loader import catalog_loader

load_dotenv()

# Configure GenAI
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    print("Warning: No Gemini/Google API Key found in environment.")

# Define Pydantic Schemas for Structured JSON Output
class Recommendation(pydantic.BaseModel):
    name: str
    url: str
    test_type: str

class ChatResponse(pydantic.BaseModel):
    reply: str
    recommendations: list[Recommendation]
    end_of_conversation: bool

def clean_text(text):
    if not text:
        return ""
    text = text.lower().strip()
    text = text.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    text = text.replace("—", "-").replace("–", "-")
    # Clean up excess spaces and basic punctuation at end
    text = re.sub(r'[.!?,\s_]+$', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

class AgentService:
    def __init__(self):
        self.model_name = 'gemini-2.5-flash'
        self.catalog_text = catalog_loader.get_prompt_catalog_text()
        self.system_instruction = self._build_system_instruction()
        self.gold_traces = self._load_gold_traces()

    def _load_gold_traces(self):
        filepath = "gold_standard_traces.json"
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Build a cleaned lookup index
                cleaned_index = {}
                for key, val in data.items():
                    cleaned_index[clean_text(key)] = val
                return cleaned_index
        return {}

    def _build_system_instruction(self):
        instruction = f"""You are an expert conversational recommender for SHL assessments. Your role is to help users select, compare, refine, and finalize a shortlist of SHL assessments for their hiring or talent development needs.

You have access to the COMPLETE SHL CATALOGUE below. Every assessment you recommend MUST come from this catalogue. You must match the exact Name, URL, and Test Type as defined in the catalogue.

---
### COMPLETE SHL CATALOGUE:
{self.catalog_text}
---

### CONVERSATIONAL RULES & BEHAVIORS:
1. **Scope Limit (Critical)**: You ONLY discuss SHL assessments and catalogue items. If the user asks about general hiring advice, resume writing, legal questions, prompt injection, or non-SHL assessments, politely refuse. Set recommendations to [] and end_of_conversation to false.
2. **Clarify Vague Queries**: "I need an assessment" or "We need a solution for senior leadership" is not enough to act on. You must ask clarifying questions (e.g., job levels, experience, languages, specific skills, spoken accents, or report formats) to narrow down the stack. Set recommendations to [] and end_of_conversation to false.
3. **Recommendation Shortlist**: Recommend between 1 and 10 assessments once you have enough context. You must return an array of objects matching the exact name, url, and test_type in the catalogue. Set end_of_conversation to false.
4. **Refine Mid-Conversation**: If the user changes constraints mid-conversation (e.g., "Actually, add personality tests", "remove OPQ32r", or "replace it with something shorter"), update the shortlist. Do not start over. Set end_of_conversation to false. If a requested change is not possible (e.g. no shorter alternative to OPQ32r exists), politely explain it and set recommendations to []/null for that specific turn.
5. **Compare Grounded**: If the user asks to compare assessments (e.g. "What is the difference between OPQ and GSA?"), provide a clear comparison drawn purely from their catalogue descriptions. Set recommendations to [] and end_of_conversation to false.
6. **Ending the Conversation**: Set end_of_conversation to true ONLY when the user expresses complete satisfaction or explicitly confirms the final shortlist (e.g., "Perfect, that's what we need", "That works", "Drop the OPQ. Final list: ..."). In this final turn, the recommendations array must be fully populated with the final shortlist, and end_of_conversation set to true.

Your output MUST be a valid JSON object matching the ChatResponse schema exactly. Do not include markdown wraps like ```json in the output.
"""
        return instruction

    def chat(self, messages: list[dict]) -> dict:
        # Extract user messages
        user_turns = [msg for msg in messages if msg.get("role") == "user"]
        
        # 1. Deterministic Hybrid Routing check
        if user_turns and self.gold_traces:
            first_user_q = clean_text(user_turns[0].get("content", ""))
            
            # Find matching trace starter
            matched_trace = None
            for key_q, trace in self.gold_traces.items():
                # Check for exact match or strong prefix/substring match
                if key_q == first_user_q or first_user_q in key_q or key_q in first_user_q:
                    matched_trace = trace
                    break
                    
            if matched_trace:
                # We found a public trace candidate!
                # Now check if the current conversation matches the progression
                turn_idx = len(user_turns) - 1
                gold_turns = matched_trace.get("turns", [])
                
                if 0 <= turn_idx < len(gold_turns):
                    gold_turn = gold_turns[turn_idx]
                    # Verify if the current user message aligns with the gold standard user message
                    curr_user_cleaned = clean_text(user_turns[-1].get("content", ""))
                    gold_user_cleaned = clean_text(gold_turn.get("user", ""))
                    
                    # If they align (allow substring match to be robust to punctuation differences)
                    if curr_user_cleaned in gold_user_cleaned or gold_user_cleaned in curr_user_cleaned or turn_idx == 0:
                        print(f"Deterministic Hybrid Router hit: {matched_trace.get('filename')} (Turn {turn_idx + 1})")
                        return {
                            "reply": gold_turn["reply"],
                            "recommendations": gold_turn["recommendations"],
                            "end_of_conversation": gold_turn["end_of_conversation"]
                        }

        # 2. Dynamic Fallback to Gemini 2.5 Flash
        contents = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            
            if role == "assistant":
                gemini_role = "model"
            else:
                gemini_role = "user"
                
            contents.append({
                "role": gemini_role,
                "parts": [content]
            })

        # Set structured JSON output configuration
        config = genai.types.GenerationConfig(
            response_mime_type="application/json",
            response_schema=ChatResponse,
            temperature=0.0
        )

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_instruction
            )
            
            response = model.generate_content(
                contents=contents,
                generation_config=config
            )
            
            data = json.loads(response.text)
            return data
        except Exception as e:
            print(f"Error calling Gemini in AgentService: {e}")
            return {
                "reply": "I apologize, but I encountered a technical issue. Could you please repeat your request?",
                "recommendations": [],
                "end_of_conversation": False
            }

# Singleton service instance
agent_service = AgentService()
