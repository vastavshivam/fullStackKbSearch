"""
Enhanced Widget Chat API with proper Knowledge Base integration
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import google.generativeai as genai
import os
import logging
import json
from datetime import datetime

# Import services
from services.simple_widget_service import SimpleWidgetService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize widget service
widget_service = SimpleWidgetService()

# Configure Gemini AI with environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ Gemini AI configured for enhanced widget chat")
else:
    print("⚠️ GEMINI_API_KEY not found. Widget AI features will be limited.")

class EnhancedChatRequest(BaseModel):
    message: str
    client_id: str
    session_id: str = "default"
    user_id: str = "anonymous"
    include_kb: bool = True
    max_kb_results: int = 3

class ChatResponse(BaseModel):
    response: str
    used_knowledge_base: bool
    kb_sources: List[str]
    response_time_ms: int
    session_id: str
    error: Optional[str] = None

@router.post("/enhanced-chat", response_model=ChatResponse)
async def enhanced_widget_chat(request: EnhancedChatRequest):
    """
    Enhanced chat endpoint with proper knowledge base integration and error handling
    """
    start_time = datetime.now()
    
    try:
        # Get widget configuration
        config_data = widget_service.get_widget_config(request.client_id)
        if not config_data:
            return ChatResponse(
                response="Widget configuration not found. Please contact support.",
                used_knowledge_base=False,
                kb_sources=[],
                response_time_ms=0,
                session_id=request.session_id,
                error="config_not_found"
            )
        
        config = config_data['config_data']
        
        # Check if AI is enabled
        if not config.get('ai_enabled', True):
            fallback = config.get('fallback_response', "AI is currently disabled for this widget.")
            return ChatResponse(
                response=fallback,
                used_knowledge_base=False,
                kb_sources=[],
                response_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                session_id=request.session_id
            )
        
        # Get knowledge base documents
        kb_documents = widget_service.get_knowledge_base_documents(request.client_id)
        kb_context = ""
        used_sources = []
        
        if kb_documents and request.include_kb:
            # Search for relevant content
            relevant_docs = search_knowledge_base(request.message, kb_documents, request.max_kb_results)
            
            if relevant_docs:
                kb_context = "\\n\\n--- KNOWLEDGE BASE CONTEXT ---\\n"
                for i, doc in enumerate(relevant_docs):
                    kb_context += f"\\n[Source {i+1}: {doc['filename']}]\\n{doc['content'][:1500]}...\\n"
                    used_sources.append(doc['filename'])
                kb_context += "\\n--- END KNOWLEDGE BASE CONTEXT ---\\n\\n"
        
        # Build AI prompt
        system_prompt = build_system_prompt(config, kb_context)
        full_prompt = f"{system_prompt}\\n\\nUser Question: {request.message}\\n\\nPlease provide a helpful response."
        
        # Generate AI response
        if GEMINI_API_KEY:
            try:
                model = genai.GenerativeModel(config.get('ai_model', 'gemini-1.5-flash'))
                response = model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=config.get('temperature', 0.7),
                        top_p=config.get('top_p', 0.9),
                        max_output_tokens=min(config.get('max_response_length', 500) * 4, 2048),
                    )
                )
                ai_response = response.text if response.text else config.get('fallback_response', "I couldn't generate a response.")
            except Exception as e:
                logger.error(f"Gemini API error: {e}")
                # Fallback to knowledge base only
                if kb_context and used_sources:
                    ai_response = f"Based on our knowledge base:\\n\\n{kb_context[:1000]}..."
                else:
                    ai_response = f"I'm sorry, there was an issue processing your request. Error: {str(e)[:100]}"
        else:
            # No API key - use knowledge base only
            if kb_context and used_sources:
                ai_response = f"Based on our knowledge base:\\n\\n{kb_context[:1000]}..."
            else:
                ai_response = "AI service is not configured. Please contact support."
        
        # Apply response length limit
        max_length = config.get('max_response_length', 500)
        if len(ai_response) > max_length:
            ai_response = ai_response[:max_length] + "..."
        
        response_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return ChatResponse(
            response=ai_response,
            used_knowledge_base=bool(used_sources),
            kb_sources=used_sources,
            response_time_ms=response_time,
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"Enhanced chat error: {e}")
        response_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return ChatResponse(
            response="I apologize, but I encountered an error processing your request. Please try again.",
            used_knowledge_base=False,
            kb_sources=[],
            response_time_ms=response_time,
            session_id=request.session_id,
            error=str(e)
        )

def search_knowledge_base(query: str, documents: List[Dict], max_results: int = 3) -> List[Dict]:
    """
    Search knowledge base documents for relevant content
    """
    if not documents:
        return []
    
    query_words = set(query.lower().split())
    scored_docs = []
    
    for doc in documents:
        content = doc.get('content', '').lower()
        # Simple keyword matching - can be enhanced with semantic search
        score = sum(1 for word in query_words if len(word) > 3 and word in content)
        
        if score > 0:
            scored_docs.append({
                'filename': doc['filename'],
                'content': doc['content'],
                'file_type': doc.get('file_type', 'text'),
                'score': score
            })
    
    # Sort by score and return top results
    scored_docs.sort(key=lambda x: x['score'], reverse=True)
    return scored_docs[:max_results]

def build_system_prompt(config: Dict, kb_context: str = "") -> str:
    """
    Build system prompt from configuration
    """
    prompt_parts = []
    
    # Base system prompt
    if config.get('system_prompt'):
        prompt_parts.append(config['system_prompt'])
    
    # Custom instructions
    if config.get('custom_instructions'):
        prompt_parts.append(config['custom_instructions'])
    
    # Knowledge base instructions
    if kb_context:
        prompt_parts.append("""
IMPORTANT: You are an AI assistant with access to specific knowledge base information. 
Always prioritize information from the knowledge base context over general knowledge.
If the knowledge base contains relevant information, use it as your primary source.
If asked about topics not covered in the knowledge base, you may use general knowledge but mention this limitation.
Always be helpful, accurate, and reference sources when using knowledge base information.
""")
    
    # Personality and tone
    personality = config.get('ai_personality', 'helpful')
    tone = config.get('response_tone', 'balanced')
    prompt_parts.append(f"Respond in a {personality} manner with a {tone} tone.")
    
    # Add knowledge base context
    if kb_context:
        prompt_parts.append(kb_context)
    
    return "\\n\\n".join(prompt_parts)

@router.get("/chat/test/{client_id}")
async def test_chat_setup(client_id: str):
    """
    Test endpoint to verify chat setup for a widget
    """
    try:
        # Check widget config
        config_data = widget_service.get_widget_config(client_id)
        if not config_data:
            return {"error": "Widget configuration not found", "client_id": client_id}
        
        # Check knowledge base
        kb_docs = widget_service.get_knowledge_base_documents(client_id)
        
        # Check Gemini API
        gemini_status = "configured" if GEMINI_API_KEY else "not_configured"
        
        return {
            "client_id": client_id,
            "config_exists": True,
            "config_data": config_data['config_data'],
            "knowledge_base_documents": len(kb_docs),
            "kb_preview": [{"filename": doc["filename"], "content_length": len(doc["content"])} for doc in kb_docs[:3]],
            "gemini_api_status": gemini_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        }
