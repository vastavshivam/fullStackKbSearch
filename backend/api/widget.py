from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request, File, UploadFile, Header
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
import uuid
import asyncio
import time
import requests
import base64
import os
from datetime import datetime, timezone
import logging
import google.generativeai as genai
import jwt

# Database and services
from services.simple_widget_service import widget_service

# Configure Gemini AI
GEMINI_API_KEY = "AIzaSyD1T3nf1zMMTRU6a6pRlRrOukV4Bgbcmp0"
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ Gemini AI configured successfully for widget")
else:
    print("⚠️ GEMINI_API_KEY not found. Widget AI features will be disabled.")

logger = logging.getLogger(__name__)

router = APIRouter()

# Helper function to extract user email from authorization token
def get_user_email_from_token(authorization: Optional[str] = Header(None)) -> str:
    """Extract user email from authorization header token"""
    if not authorization:
        # For demo purposes, return default user
        return "krish.ishaan@gmail.com"
    
    try:
        # Remove "Bearer " prefix if present
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        
        # Handle demo tokens
        if token.startswith("demo_token_"):
            return "krish.ishaan@gmail.com"
        
        # For real JWT tokens, decode and extract email
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get("email", "krish.ishaan@gmail.com")
        except:
            return "krish.ishaan@gmail.com"
            
    except Exception as e:
        logger.warning(f"Failed to extract user email from token: {e}")
        return "krish.ishaan@gmail.com"

# Add CORS middleware to allow PATCH and OPTIONS
def add_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Widget configuration models
class WidgetConfig(BaseModel):
    client_id: str
    domain: str
    position: str = "bottom-right"  # bottom-right, bottom-left, top-right, top-left
    theme: str = "light"  # light, dark, auto
    primary_color: str = "#007bff"
    chat_title: str = "AI Assistant"
    welcome_message: str = "Hello! How can I help you today?"
    knowledge_base_ids: List[str] = []
    allowed_domains: List[str] = []
    analytics_enabled: bool = True
    is_active: bool = True
    rate_limit: int = 100  # messages per hour
    max_file_size: int = 10  # MB
    enabled_features: List[str] = ["chat", "voice", "file_upload", "feedback"]
    
    # Advanced Appearance Settings
    font_family: str = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    button_size: int = 60
    button_shape: str = "circle"  # circle, square
    border_width: int = 0
    border_color: str = "transparent"
    shadow_style: str = "0 4px 12px rgba(0,0,0,0.15)"
    animation_type: str = "none"  # none, pulse, bounce, shake, glow
    animation_duration: str = "2s"
    
    # Mascot/Icon Settings
    mascot_type: str = "chat"  # chat, robot, support, question, custom
    custom_icon: str = ""  # SVG or image URL for custom mascot
    
    # Chat Window Settings
    chat_width: int = 350
    chat_height: int = 500
    chat_background: str = "white"
    chat_border_radius: int = 12
    chat_border_width: int = 0
    chat_border_color: str = "transparent"
    
    # Header Settings
    header_background: str = ""  # Uses primary_color if empty
    header_text_color: str = "white"
    header_font_size: str = "16px"
    
    # Messages Settings
    messages_background: str = "#f8f9fa"
    bot_message_background: str = "#e9ecef"
    bot_message_color: str = "#333"
    user_message_background: str = ""  # Uses primary_color if empty
    user_message_color: str = "white"
    message_font_size: str = "14px"
    
    # Input Area Settings
    input_area_background: str = "white"
    input_background: str = "white"
    input_text_color: str = "#333"
    input_border_color: str = "#ddd"
    input_border_radius: int = 8
    input_font_size: str = "14px"
    input_placeholder: str = "Type your message..."
    
    # Send Button Settings
    send_button_color: str = ""  # Uses primary_color if empty
    send_button_text_color: str = "white"
    send_button_border_radius: int = 8
    send_button_font_size: str = "14px"
    send_button_text: str = "Send"
    
    # AI Configuration Settings
    ai_enabled: bool = True
    ai_provider: str = "gemini"  # gemini, openai, claude, local
    ai_model: str = "gemini-1.5-pro"  # gemini-1.5-flash, gemini-1.5-pro, gpt-4, claude-3, etc.
    ai_api_key: str = ""  # API key for the AI provider
    
    # AI Personality & Behavior
    ai_personality: str = "helpful"  # helpful, professional, friendly, creative, technical
    ai_tone: str = "conversational"  # conversational, formal, casual, enthusiastic
    ai_response_style: str = "detailed"  # brief, detailed, comprehensive, bullet-points
    ai_language: str = "en"  # en, es, fr, de, etc.
    
    # AI Prompts & Instructions
    system_prompt: str = "You are a helpful AI assistant embedded in a website widget. Be concise, friendly, and helpful."
    custom_instructions: str = ""  # Additional custom instructions for the AI
    greeting_prompt: str = ""  # Custom greeting when chat starts
    fallback_response: str = "I'm sorry, I couldn't understand that. Could you please rephrase your question?"
    
    # AI Features & Capabilities
    voice_enabled: bool = True
    image_analysis_enabled: bool = True
    file_upload_enabled: bool = True
    web_search_enabled: bool = False
    knowledge_base_priority: bool = True  # Prioritize KB over general AI knowledge
    
    # AI Response Limits
    max_response_length: int = 500  # Maximum characters in AI response
    response_timeout: int = 30  # Timeout in seconds
    max_conversation_history: int = 10  # Number of previous messages to include in context
    
    # AI Safety & Moderation
    content_filtering: bool = True
    inappropriate_content_response: str = "I can't help with that type of request. Please ask something else."
    blocked_topics: List[str] = []  # Topics to avoid
    allowed_topics: List[str] = []  # Only respond to these topics if specified
    
    # Advanced AI Settings
    temperature: float = 0.7  # AI creativity/randomness (0.0-1.0)
    top_p: float = 0.9  # Nucleus sampling parameter
    frequency_penalty: float = 0.0  # Penalize repeated tokens
    presence_penalty: float = 0.0  # Penalize new topics
    
    # Multimodal AI Settings
    image_processing_prompt: str = "Analyze this image and provide a helpful description or answer any questions about it."
    voice_transcription_language: str = "en-US"
    voice_response_enabled: bool = False  # Text-to-speech for responses
    voice_response_voice: str = "en-US-Standard-A"  # Voice for TTS
    
    # Context & Memory
    conversation_memory: bool = True  # Remember conversation context
    user_preferences_memory: bool = False  # Remember user preferences across sessions
    session_context_enabled: bool = True  # Include page context in AI requests

class AnalyticsEvent(BaseModel):
    client_id: str
    event_type: str  # chat_start, message_sent, file_uploaded, feedback_given, ai_response, user_joined, user_left, conversation_lead
    timestamp: datetime = datetime.now(timezone.utc)
    user_id: Optional[str] = None
    user_info: Optional[Dict] = {}  # Name, email, location, device, etc.
    session_id: str
    metadata: Optional[Dict] = {}
    conversation_data: Optional[Dict] = {}  # Message content, sentiment, intent, etc.
    lead_score: Optional[float] = 0.0  # Potential lead score 0-1
    user_location: Optional[Dict] = {}  # IP-based location data
    device_info: Optional[Dict] = {}  # Browser, OS, device type

class ToggleRequest(BaseModel):
    is_active: bool

# In-memory storage (replace with Redis/DB in production)
active_connections: Dict[str, List[WebSocket]] = {}  # Multiple connections per client
widget_configs: Dict[str, WidgetConfig] = {}
analytics_events: List[AnalyticsEvent] = []
knowledge_bases: Dict[str, List[Dict]] = {}  # Client KB data

def load_widget_config_from_db(client_id: str) -> Optional[WidgetConfig]:
    """Load widget configuration from database and cache in memory"""
    config_data = widget_service.get_widget_config(client_id)
    
    if config_data:
        # Convert database config to WidgetConfig object
        widget_config = WidgetConfig(**config_data['config_data'])
        widget_configs[client_id] = widget_config
        return widget_config
    
    return None

@router.websocket("/ws/{client_id}")
async def websocket_widget_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time widget updates"""
    await websocket.accept()
    
    # Support multiple connections per client
    if client_id not in active_connections:
        active_connections[client_id] = []
    active_connections[client_id].append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "config_update":
                # Update widget configuration
                config_data = message["data"]
                config_data["client_id"] = client_id
                widget_configs[client_id] = WidgetConfig(**config_data)
                
                # Broadcast config update to all connected widgets for this client
                await broadcast_to_client(client_id, {
                    "type": "config_update",
                    "data": config_data
                })
                
            elif message["type"] == "analytics":
                # Store analytics event
                event_data = message["data"]
                event_data["client_id"] = client_id
                
                # Ensure session_id is present
                if "session_id" not in event_data:
                    event_data["session_id"] = f"session_{client_id}_{int(time.time())}"
                
                # Ensure timestamp is present
                if "timestamp" not in event_data:
                    event_data["timestamp"] = datetime.now()
                
                try:
                    analytics_events.append(AnalyticsEvent(**event_data))
                    
                    # Broadcast analytics to dashboard listeners
                    await broadcast_to_client(f"{client_id}_dashboard", {
                        "type": "analytics_update",
                        "data": event_data
                    })
                except Exception as e:
                    logger.error(f"Analytics event error: {e}")
                    logger.error(f"Event data: {event_data}")
                
            elif message["type"] == "knowledge_base_update":
                # Update knowledge base
                kb_data = message["data"]
                knowledge_bases[client_id] = kb_data
                
                # Broadcast KB update to all widgets
                await broadcast_to_client(client_id, {
                    "type": "knowledge_base_update",
                    "data": kb_data
                })
                
            await websocket.send_text(json.dumps({
                "type": "ack",
                "timestamp": datetime.now().isoformat()
            }))
            
    except WebSocketDisconnect:
        if client_id in active_connections:
            active_connections[client_id].remove(websocket)
            if not active_connections[client_id]:
                del active_connections[client_id]
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        if client_id in active_connections and websocket in active_connections[client_id]:
            active_connections[client_id].remove(websocket)

async def broadcast_to_client(client_id: str, message: Dict):
    """Broadcast message to all connections for a specific client"""
    if client_id in active_connections:
        disconnected = []
        for websocket in active_connections[client_id]:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected websockets
        for ws in disconnected:
            active_connections[client_id].remove(ws)
        
        # Clean up empty connection lists
        if not active_connections[client_id]:
            del active_connections[client_id]

@router.get("/list")
async def list_widgets(user_email: str = Depends(get_user_email_from_token)):
    """Get list of widgets for the authenticated user"""
    try:
        # Get user-specific widgets from database
        user_widgets = widget_service.get_widgets_by_user(user_email)
        
        widgets_list = []
        for widget in user_widgets:
            # Widget config is already parsed in the service
            config_data = widget['config']
            client_id = widget['client_id']
            
            widgets_list.append({
                **config_data,
                "client_id": client_id,
                "connection_count": len(active_connections.get(client_id, [])),
                "created_at": widget.get('created_at', "2025-01-01"),
                "user_email": widget['user_email']
            })
        
        return {"widgets": widgets_list, "total": len(widgets_list)}
        
    except Exception as e:
        logger.error(f"Error listing widgets for user {user_email}: {e}")
        # Fallback to in-memory widgets if database fails
        widgets_list = []
        for client_id, config in widget_configs.items():
            widgets_list.append({
                **config.dict(),
                "connection_count": len(active_connections.get(client_id, [])),
                "created_at": "2025-01-01"
            })
        
        return {"widgets": widgets_list, "total": len(widgets_list)}

@router.post("/config")
async def create_or_update_widget_config(config: WidgetConfig, user_email: str = Depends(get_user_email_from_token)):
    """Create or update widget configuration for authenticated user"""
    # Save to database with user email
    success = widget_service.save_widget_config(config.client_id, config.dict(), user_email)
    
    if success:
        # Keep in memory cache for WebSocket updates
        widget_configs[config.client_id] = config
        
        # Broadcast update to connected widgets
        await broadcast_to_client(config.client_id, {
            "type": "config_update",
            "data": config.dict()
        })
        
        return {"message": "Widget configuration saved to database", "client_id": config.client_id, "user_email": user_email}
    else:
        raise HTTPException(status_code=500, detail="Failed to save widget configuration")

@router.get("/config/{client_id}")
async def get_widget_config(client_id: str, user_email: str = Depends(get_user_email_from_token)):
    """Get widget configuration for authenticated user"""
    config_data = widget_service.get_widget_config(client_id)
    
    if not config_data:
        raise HTTPException(status_code=404, detail="Widget configuration not found")
    
    # Check if user owns this widget
    if config_data.get('user_email') != user_email:
        raise HTTPException(status_code=403, detail="Access denied: Widget belongs to another user")
    
    return config_data['config_data']

@router.delete("/config/{client_id}")
async def delete_widget_config(client_id: str, user_email: str = Depends(get_user_email_from_token)):
    """Delete widget configuration for authenticated user"""
    config_data = widget_service.get_widget_config(client_id)
    
    if not config_data:
        raise HTTPException(status_code=404, detail="Widget configuration not found")
    
    # Check if user owns this widget
    if config_data.get('user_email') != user_email:
        raise HTTPException(status_code=403, detail="Access denied: Widget belongs to another user")
    
    # Delete from database
    success = widget_service.delete_widget_config(client_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete widget configuration")
    
    # Remove from memory cache if exists
    if client_id in widget_configs:
        del widget_configs[client_id]
    
    # Disconnect WebSocket if active
    if client_id in active_connections:
        for connection in active_connections[client_id]:
            await connection.close()
        del active_connections[client_id]
    
    return {"message": "Widget deleted successfully"}
    
    return {"message": "Widget configuration deleted"}

@router.options("/toggle/{client_id}")
async def toggle_options(client_id: str):
    return JSONResponse({"message": "CORS preflight OK"})

@router.patch("/toggle/{client_id}")
async def toggle_widget_status(client_id: str, toggle_request: ToggleRequest):
    """Toggle widget active/inactive status"""
    config_data = widget_service.get_widget_config(client_id)
    
    if not config_data:
        raise HTTPException(status_code=404, detail="Widget configuration not found")
    
    # Update the is_active status in database
    config_data['config_data']['is_active'] = toggle_request.is_active
    success = widget_service.save_widget_config(client_id, config_data['config_data'])
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update widget status")
    
    # Update memory cache if exists
    if client_id in widget_configs:
        widget_configs[client_id].is_active = toggle_request.is_active
    
    # Broadcast status update to connected widgets
    await broadcast_to_client(client_id, {
        "type": "status_update",
        "data": {
            "is_active": toggle_request.is_active,
            "message": f"Widget {'activated' if toggle_request.is_active else 'deactivated'}"
        }
    })
    
    status = "activated" if toggle_request.is_active else "deactivated"
    return {
        "message": f"Widget {status} successfully",
        "client_id": client_id,
        "is_active": toggle_request.is_active
    }


# --- ADVANCED GEMINI AI ENDPOINT ---

@router.post("/chat/gemini/{client_id}")
async def chat_gemini(client_id: str, message: str = "", voice: Optional[UploadFile] = None, image: Optional[UploadFile] = None):
    """Advanced Gemini AI chat endpoint with knowledge base integration"""
    
    # Get widget configuration (try memory first, then database)
    config = widget_configs.get(client_id)
    if not config:
        config = load_widget_config_from_db(client_id)
    
    if not config:
        return {"response": "Widget configuration not found"}
    
    if not config.ai_enabled:
        return {"response": config.fallback_response}
    
    # Check if Gemini is configured
    if not GEMINI_API_KEY:
        return {"response": "AI service not configured. Please contact administrator."}
    
    try:
        # Get client's knowledge base from database
        db_kb_documents = widget_service.get_knowledge_base_documents(client_id)
        # Also check in-memory for backward compatibility
        memory_kb_documents = knowledge_bases.get(client_id, [])
        
        # Combine both sources - transform database format to match expected format
        client_kb = []
        
        # Add database documents
        for doc in db_kb_documents:
            client_kb.append({
                "filename": doc.get("filename", "Unknown"),
                "content": doc.get("content", ""),
                "type": doc.get("file_type", "text")
            })
        
        # Add memory documents (if any)
        client_kb.extend(memory_kb_documents)
        
        kb_context = ""
        
        if client_kb and config.knowledge_base_priority:
            # Search through knowledge base for relevant content
            relevant_content = []
            user_message_lower = message.lower() if message else ""
            
            for doc in client_kb:
                doc_content = doc.get("content", "")
                # Simple keyword matching - you can enhance with semantic search
                if any(word in doc_content.lower() for word in user_message_lower.split() if len(word) > 3):
                    relevant_content.append({
                        "filename": doc.get("filename", "Unknown"),
                        "content": doc_content[:2000],  # Limit content length
                        "type": doc.get("type", "text")
                    })
            
            # Limit to top 3 most relevant documents
            if relevant_content:
                kb_context = "\n\n--- KNOWLEDGE BASE CONTEXT ---\n"
                for i, doc in enumerate(relevant_content[:3]):
                    kb_context += f"\n[Document {i+1}: {doc['filename']}]\n{doc['content']}\n"
                kb_context += "\n--- END KNOWLEDGE BASE CONTEXT ---\n\n"
        
        # Build the AI prompt with system instructions and knowledge base
        full_prompt = ""
        
        # Add system instructions
        if config.system_prompt:
            full_prompt += f"{config.system_prompt}\n"
        if config.custom_instructions:
            full_prompt += f"{config.custom_instructions}\n"
        
        # Add knowledge base priority instruction
        if client_kb and config.knowledge_base_priority:
            full_prompt += f"""
IMPORTANT: You are an AI assistant for this specific organization. Use the provided KNOWLEDGE BASE CONTEXT as your PRIMARY source of information. 

Guidelines:
1. ALWAYS prioritize information from the knowledge base context over general knowledge
2. If the user's question can be answered using the knowledge base, base your response primarily on that information
3. If the knowledge base doesn't contain relevant information, you may use your general knowledge but mention this limitation
4. Always be helpful and accurate
5. Reference the source document when using knowledge base information

"""
        
        # Add personality and tone guidance
        full_prompt += f"Respond in a {config.ai_personality} and {config.ai_tone} manner with {config.ai_response_style} style.\n"
        
        # Add knowledge base context if available
        if kb_context:
            full_prompt += kb_context
        
        # Add the user message
        if message:
            full_prompt += f"User Question: {message}\n\nPlease provide a helpful response based on the above context and guidelines."
        
        # Initialize Gemini model
        if image and config.image_analysis_enabled:
            # Use Gemini Pro Vision for image analysis
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Process image
            image_bytes = await image.read()
            image_data = {
                'mime_type': image.content_type,
                'data': image_bytes
            }
            
            # Create content with image and text
            content = [full_prompt]
            if config.image_processing_prompt:
                content.append(config.image_processing_prompt)
            content.append(image_data)
            
            response = model.generate_content(
                content,
                generation_config=genai.types.GenerationConfig(
                    temperature=config.temperature,
                    top_p=config.top_p,
                    max_output_tokens=min(config.max_response_length * 4, 2048),
                )
            )
        else:
            # Use regular Gemini Pro for text
            model = genai.GenerativeModel(config.ai_model or 'gemini-1.5-flash')
            
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=config.temperature,
                    top_p=config.top_p,
                    max_output_tokens=min(config.max_response_length * 4, 2048),
                )
            )
        
        # Extract answer
        answer = response.text if response.text else config.fallback_response
        
        # Apply response length limit
        if len(answer) > config.max_response_length:
            answer = answer[:config.max_response_length] + "..."
        
        # Content filtering
        if config.content_filtering:
            # Simple content filtering - you can enhance this
            blocked_words = ["harmful", "inappropriate"] + config.blocked_topics
            if any(word.lower() in answer.lower() for word in blocked_words):
                answer = config.inappropriate_content_response
        
        # Add metadata about knowledge base usage
        response_metadata = {
            "used_knowledge_base": bool(kb_context),
            "knowledge_base_documents": len(client_kb),
            "relevant_documents_found": len(relevant_content) if 'relevant_content' in locals() else 0
        }
        
    except Exception as e:
        logger.error(f"Gemini AI error: {e}")
        error_message = str(e)
        # Always try to provide knowledge base response if AI fails
        if client_kb and message:
            user_message_lower = message.lower()
            best_match = None
            best_score = 0
            for doc in client_kb:
                doc_content = doc.get("content", "").lower()
                score = sum(1 for word in user_message_lower.split() if len(word) > 3 and word in doc_content)
                if score > best_score:
                    best_score = score
                    best_match = doc
            if best_match and best_score > 0:
                content = best_match.get("content", "")[:800]
                filename = best_match.get("filename", "Knowledge Base")
                answer = f"**Based on our knowledge base ({filename}):**\n\n{content}...\n\n*Note: AI service is temporarily unavailable, showing direct knowledge base content.*"
            else:
                answer = "🚫 **AI Service Temporarily Unavailable**\n\nThe AI service has reached its daily usage limit. Please try again tomorrow or contact us directly at info@climethic.com for assistance."
        elif "api key" in error_message.lower():
            answer = "🔧 **AI Service Configuration Issue**\n\nThere's a configuration issue with the AI service. Please contact support for assistance."
        else:
            answer = f"⚠️ **AI Service Error**\n\nThere was a temporary issue with the AI service. Please try again in a moment.\n\n*Error details: {str(e)[:100]}...*"
        response_metadata = {"error": True, "error_type": "api_error"}
    
    # Store analytics
    if config.analytics_enabled:
        analytics_events.append(AnalyticsEvent(
            client_id=client_id,
            event_type="ai_response",
            session_id=f"session_{client_id}_{int(time.time())}",
            metadata={
                "ai_provider": config.ai_provider,
                "ai_model": config.ai_model,
                "response_length": len(answer),
                "has_voice": voice is not None,
                "has_image": image is not None,
                "message_length": len(message) if message else 0,
                "used_knowledge_base": response_metadata.get("used_knowledge_base", False),
                "kb_documents_count": response_metadata.get("knowledge_base_documents", 0)
            }
        ))
    
    return {
        "response": answer,
        "metadata": response_metadata
    }

def get_position_styles(position: str) -> str:
    """Get CSS positioning styles based on position setting"""
    positions = {
        "bottom-right": "bottom: 20px; right: 20px;",
        "bottom-left": "bottom: 20px; left: 20px;",
        "top-right": "top: 20px; right: 20px;",
        "top-left": "top: 20px; left: 20px;"
    }
    return positions.get(position, positions["bottom-right"])

def get_chat_position(position: str) -> str:
    """Get chat window positioning relative to button"""
    positions = {
        "bottom-right": "bottom: 70px; right: 0;",
        "bottom-left": "bottom: 70px; left: 0;",
        "top-right": "top: 70px; right: 0;",
        "top-left": "top: 70px; left: 0;"
    }
    return positions.get(position, positions["bottom-right"])

@router.get("/script/{client_id}")
async def get_widget_script(client_id: str, request: Request):
    """Generate the widget JavaScript code for embedding"""
    
    # Get client config (try memory first, then database, then defaults)
    config = widget_configs.get(client_id)
    if not config:
        config = load_widget_config_from_db(client_id)
    if not config:
        config = WidgetConfig(client_id=client_id, domain="")
    
    # Check if widget is active
    if not config.is_active:
        # Return empty script if widget is deactivated
        return HTMLResponse(
            content=f"// Widget {client_id} is currently deactivated",
            media_type="application/javascript"
        )
    
    # Get the server URL from request
    server_url = f"{request.url.scheme}://{request.url.netloc}"
    
    script_content = f"""
(function() {{
    // Widget Configuration
    let config = {json.dumps(config.dict(), default=str)};
    const serverUrl = '{server_url}';
    const clientId = '{client_id}';
    let websocket = null;
    let widgetContainer = null;
    let isOpen = false;
    
    // Initialize widget
    function initWidget() {{
        // Remove existing widget if any
        const existing = document.getElementById('ai-kb-widget-' + clientId);
        if (existing) existing.remove();
        
        // Create widget container
        widgetContainer = document.createElement('div');
        widgetContainer.id = 'ai-kb-widget-' + clientId;
        updateWidgetStyles();
        
        // Add to page
        document.body.appendChild(widgetContainer);
        
        // Connect WebSocket for live updates
        connectWebSocket();
        
        // Render widget
        renderWidget();
    }}
    
    function updateWidgetStyles() {{
        if (!widgetContainer) return;
        
        widgetContainer.style.cssText = `
            position: fixed;
            ${{getPositionStyles(config.position)}}
            z-index: 10000;
            font-family: ${{config.font_family || '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'}};
            transition: all 0.3s ease;
        `;
    }}
    
    function getPositionStyles(position) {{
        const positions = {{
            "bottom-right": "bottom: 20px; right: 20px;",
            "bottom-left": "bottom: 20px; left: 20px;",
            "top-right": "top: 20px; right: 20px;",
            "top-left": "top: 20px; left: 20px;"
        }};
        return positions[position] || positions["bottom-right"];
    }}
    
    function getChatPosition(position) {{
        const positions = {{
            "bottom-right": "bottom: 80px; right: 0;",
            "bottom-left": "bottom: 80px; left: 0;",
            "top-right": "top: 80px; right: 0;",
            "top-left": "top: 80px; left: 0;"
        }};
        return positions[position] || positions["bottom-right"];
    }}
    
    function renderWidget() {{
        if (!widgetContainer) return;
        
        const mascotIcon = getMascotIcon(config.mascot_type || 'chat');
        const buttonSize = config.button_size || 60;
        
        widgetContainer.innerHTML = `
            <div id="widget-button" style="
                width: ${{buttonSize}}px;
                height: ${{buttonSize}}px;
                background: ${{config.primary_color || '#007bff'}};
                border-radius: ${{config.button_shape === 'square' ? '12px' : '50%'}};
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: ${{config.shadow_style || '0 4px 12px rgba(0,0,0,0.15)'}};
                transition: all 0.3s ease;
                border: ${{config.border_width || 0}}px solid ${{config.border_color || 'transparent'}};
                animation: ${{config.animation_type || 'none'}} ${{config.animation_duration || '2s'}} infinite;
            " onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
                ${{mascotIcon}}
            </div>
            
            <div id="widget-chat" style="
                display: none;
                width: ${{config.chat_width || 350}}px;
                height: ${{config.chat_height || 500}}px;
                background: ${{config.chat_background || 'white'}};
                border-radius: ${{config.chat_border_radius || 12}}px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.12);
                position: absolute;
                ${{getChatPosition(config.position)}}
                flex-direction: column;
                overflow: hidden;
                border: ${{config.chat_border_width || 0}}px solid ${{config.chat_border_color || 'transparent'}};
            ">
                <div style="
                    background: ${{config.header_background || config.primary_color || '#007bff'}};
                    color: ${{config.header_text_color || 'white'}};
                    padding: 16px;
                    font-weight: 600;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: ${{config.header_font_size || '16px'}};
                ">
                    <span>${{config.chat_title || 'AI Assistant'}}</span>
                    <button onclick="toggleChat()" style="
                        background: none;
                        border: none;
                        color: ${{config.header_text_color || 'white'}};
                        cursor: pointer;
                        font-size: 18px;
                    ">&times;</button>
                </div>
                
                <div id="chat-messages" style="
                    flex: 1;
                    overflow-y: auto;
                    padding: 16px;
                    background: ${{config.messages_background || '#f8f9fa'}};
                ">
                    <div style="
                        background: ${{config.bot_message_background || '#e9ecef'}};
                        color: ${{config.bot_message_color || '#333'}};
                        padding: 12px;
                        border-radius: 12px;
                        margin-bottom: 12px;
                        font-size: ${{config.message_font_size || '14px'}};
                    ">
                        ${{config.welcome_message || 'Hello! How can I help you today?'}}
                    </div>
                </div>
                
                <div style="
                    padding: 16px;
                    border-top: 1px solid #e9ecef;
                    background: ${{config.input_area_background || 'white'}};
                ">
                    <div style="display: flex; gap: 8px; margin-bottom: 8px;">
                        <input type="text" id="chat-input" placeholder="${{config.input_placeholder || 'Type your message...'}}" style="
                            flex: 1;
                            padding: 12px;
                            border: 1px solid ${{config.input_border_color || '#ddd'}};
                            border-radius: ${{config.input_border_radius || '8px'}};
                            font-size: ${{config.input_font_size || '14px'}};
                            background: ${{config.input_background || 'white'}};
                            color: ${{config.input_text_color || '#333'}};
                        " onkeypress="if(event.key==='Enter') sendMessage()">
                        
                        ${{config.voice_enabled ? `
                            <button id="voice-btn" onclick="toggleVoiceRecording()" style="
                                background: none;
                                border: 2px solid #666;
                                border-radius: 50%;
                                padding: 10px;
                                cursor: pointer;
                                color: #666;
                                font-size: 16px;
                                width: 45px;
                                height: 45px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                transition: all 0.3s ease;
                                position: relative;
                            " title="Live Voice Recording">🎤</button>
                        ` : ''}}
                        
                        <button onclick="sendMessage()" style="
                            padding: 12px 16px;
                            background: ${{config.send_button_color || config.primary_color || '#007bff'}};
                            color: ${{config.send_button_text_color || 'white'}};
                            border: none;
                            border-radius: ${{config.send_button_border_radius || '8px'}};
                            cursor: pointer;
                            font-size: ${{config.send_button_font_size || '14px'}};
                        ">${{config.send_button_text || 'Send'}}</button>
                    </div>
                    
                    ${{config.voice_enabled ? `
                        <div id="voice-status" style="
                            font-size: 11px;
                            color: #666;
                            text-align: center;
                            margin-bottom: 8px;
                            background: #f8f9fa;
                            padding: 4px 8px;
                            border-radius: 12px;
                            display: inline-block;
                        ">Click microphone for live voice</div>
                    ` : ''}}
                    
                    ${{config.image_analysis_enabled ? `
                        <div style="
                            font-size: 11px;
                            color: #666;
                            text-align: center;
                            margin-bottom: 8px;
                            opacity: 0.8;
                        ">
                            💡 Paste images with Ctrl+V or drag & drop files
                        </div>
                    ` : ''}}
                    
                    <!-- Advanced AI Features -->
                    <div style="display: flex; gap: 8px; align-items: center; font-size: 12px; color: #666;">
                        ${{config.voice_enabled ? `
                            <button id="voice-btn" onclick="toggleVoiceRecording()" style="
                                display: flex; align-items: center; gap: 4px; cursor: pointer;
                                background: none; border: 1px solid #ddd; border-radius: 4px;
                                padding: 4px 8px; font-size: 12px;
                            ">
                                🎤 <span id="voice-status">Voice</span>
                            </button>
                        ` : ''}}
                        
                        ${{config.image_analysis_enabled ? `
                            <label style="display: flex; align-items: center; gap: 4px; cursor: pointer;">
                                <input type="file" id="image-input" accept="image/*" style="display: none;" onchange="handleImageUpload(event)">
                                📷 Image
                            </label>
                        ` : ''}}
                        
                        ${{config.file_upload_enabled ? `
                            <label style="display: flex; align-items: center; gap: 4px; cursor: pointer;">
                                <input type="file" id="file-input" style="display: none;" onchange="handleFileUpload(event)">
                                📎 File
                            </label>
                        ` : ''}}
                        
                        <small style="color: #999;">Paste images with Ctrl+V</small>
                    </div>
                </div>
            </div>
        `;
        
        // Add event listeners
        document.getElementById('widget-button').onclick = toggleChat;
        document.getElementById('chat-input').onkeypress = function(e) {{
            if (e.key === 'Enter') sendMessage();
        }};
    }}
    
    function getMascotIcon(type) {{
        const icons = {{
            'chat': '<svg width="24" height="24" fill="white" viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h4l4 4 4-4h4c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>',
            'robot': '<svg width="24" height="24" fill="white" viewBox="0 0 24 24"><path d="M12,2A2,2 0 0,1 14,4C14,4.74 13.6,5.39 13,5.73V7H14A7,7 0 0,1 21,14H22A1,1 0 0,1 23,15V18A1,1 0 0,1 22,19H21V20A2,2 0 0,1 19,22H5A2,2 0 0,1 3,20V19H2A1,1 0 0,1 1,18V15A1,1 0 0,1 2,14H3A7,7 0 0,1 10,7H11V5.73C10.4,5.39 10,4.74 10,4A2,2 0 0,1 12,2M12,4A0.5,0.5 0 0,0 11.5,4.5A0.5,0.5 0 0,0 12,5A0.5,0.5 0 0,0 12.5,4.5A0.5,0.5 0 0,0 12,4M7.5,13A2.5,2.5 0 0,0 10,15.5A2.5,2.5 0 0,0 12.5,13A2.5,2.5 0 0,0 10,10.5A2.5,2.5 0 0,0 7.5,13M14.5,13A2.5,2.5 0 0,0 17,15.5A2.5,2.5 0 0,0 19.5,13A2.5,2.5 0 0,0 17,10.5A2.5,2.5 0 0,0 14.5,13Z"/></svg>',
            'support': '<svg width="24" height="24" fill="white" viewBox="0 0 24 24"><path d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/></svg>',
            'question': '<svg width="24" height="24" fill="white" viewBox="0 0 24 24"><path d="M10,19H13V22H10V19M12,2C17.35,2.22 19.68,7.62 16.5,11.67C15.67,12.67 14.33,13.33 13.67,14.17C13,15 13,16 13,17H10C10,15.33 10,13.92 10.67,12.92C11.33,11.92 12.67,11.33 13.5,10.67C15.92,8.43 15.32,5.26 12,5A3,3 0 0,0 9,8H6A6,6 0 0,1 12,2Z"/></svg>',
            'custom': config.custom_icon || '<svg width="24" height="24" fill="white" viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h4l4 4 4-4h4c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>'
        }};
        return icons[type] || icons['chat'];
    }}
    
    function connectWebSocket() {{
        const wsUrl = serverUrl.replace('http', 'ws') + '/api/widget/ws/' + clientId;
        websocket = new WebSocket(wsUrl);
        
        websocket.onopen = function() {{
            console.log('Widget WebSocket connected');
        }};
        
        websocket.onmessage = function(event) {{
            const message = JSON.parse(event.data);
            
            if (message.type === 'config_update') {{
                // Live update configuration
                config = message.data;
                updateWidgetStyles();
                renderWidget();
                console.log('Widget updated live!');
            }} else if (message.type === 'status_update') {{
                if (!message.data.is_active) {{
                    // Widget deactivated - hide it
                    if (widgetContainer) {{
                        widgetContainer.style.display = 'none';
                    }}
                }} else {{
                    // Widget activated - show it
                    if (widgetContainer) {{
                        widgetContainer.style.display = 'block';
                    }}
                }}
            }}
        }};
        
        websocket.onclose = function() {{
            console.log('Widget WebSocket disconnected, reconnecting...');
            setTimeout(connectWebSocket, 3000);
        }};
    }}
    
    window.toggleChat = function() {{
        const chatDiv = document.getElementById('widget-chat');
        const buttonDiv = document.getElementById('widget-button');
        
        if (isOpen) {{
            chatDiv.style.display = 'none';
            isOpen = false;
        }} else {{
            chatDiv.style.display = 'flex';
            isOpen = true;
            
            // Send analytics event
            if (websocket && websocket.readyState === WebSocket.OPEN) {{
                websocket.send(JSON.stringify({{
                    type: 'analytics',
                    data: {{
                        event_type: 'chat_opened',
                        client_id: clientId,
                        timestamp: new Date().toISOString(),
                        session_id: 'session_' + Date.now(),
                        metadata: {{
                            user_agent: navigator.userAgent,
                            page_url: window.location.href,
                            page_title: document.title
                        }}
                    }}
                }}));
            }}
        }}
    }};
    
    window.sendMessage = function() {{
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        if (!message) return;
        
        // Add message to chat
        const messagesDiv = document.getElementById('chat-messages');
        messagesDiv.innerHTML += `
            <div style="
                background: ${{config.user_message_background || config.primary_color || '#007bff'}};
                color: ${{config.user_message_color || 'white'}};
                padding: 12px;
                border-radius: 12px;
                margin-bottom: 12px;
                margin-left: 20px;
                font-size: ${{config.message_font_size || '14px'}};
            ">${{message}}</div>
        `;
        
        input.value = '';
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        
        // Send to advanced AI endpoint
        sendToAI(message);
        
        // Send analytics
        if (websocket && websocket.readyState === WebSocket.OPEN) {{
            websocket.send(JSON.stringify({{
                type: 'analytics',
                data: {{
                    event_type: 'message_sent',
                    client_id: clientId,
                    timestamp: new Date().toISOString(),
                    session_id: 'session_' + Date.now(),
                    metadata: {{
                        message_length: message.length,
                        page_url: window.location.href,
                        ai_enabled: config.ai_enabled
                    }}
                }}
            }}));
        }}
    }};
    
    function sendToAI(message, voiceFile = null, imageFile = null) {{
        // Show typing indicator
        const messagesDiv = document.getElementById('chat-messages');
        const typingId = 'typing-' + Date.now();
        messagesDiv.innerHTML += `
            <div id="${{typingId}}" style="
                background: ${{config.bot_message_background || '#e9ecef'}};
                color: ${{config.bot_message_color || '#333'}};
                padding: 12px;
                border-radius: 12px;
                margin-bottom: 12px;
                margin-right: 20px;
                font-size: ${{config.message_font_size || '14px'}};
                font-style: italic;
            ">AI is thinking...</div>
        `;
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        
        // Prepare form data for multimodal AI
        const formData = new FormData();
        if (message) formData.append('message', message);
        if (voiceFile) formData.append('voice', voiceFile);
        if (imageFile) formData.append('image', imageFile);
        
        // Call AI endpoint
        fetch(serverUrl + '/api/widget/chat/gemini/' + clientId, {{
            method: 'POST',
            body: formData
        }})
        .then(response => response.json())
        .then(data => {{
            // Remove typing indicator
            const typingElement = document.getElementById(typingId);
            if (typingElement) typingElement.remove();
            
            // Add AI response
            messagesDiv.innerHTML += `
                <div style="
                    background: ${{config.bot_message_background || '#e9ecef'}};
                    color: ${{config.bot_message_color || '#333'}};
                    padding: 12px;
                    border-radius: 12px;
                    margin-bottom: 12px;
                    margin-right: 20px;
                    font-size: ${{config.message_font_size || '14px'}};
                ">${{data.response}}</div>
            `;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            // Text-to-speech if enabled
            if (config.voice_response_enabled && 'speechSynthesis' in window) {{
                const utterance = new SpeechSynthesisUtterance(data.response);
                utterance.voice = speechSynthesis.getVoices().find(voice => 
                    voice.name.includes(config.voice_response_voice || 'en-US')
                );
                speechSynthesis.speak(utterance);
            }}
        }})
        .catch(error => {{
            // Remove typing indicator and show error
            const typingElement = document.getElementById(typingId);
            if (typingElement) typingElement.remove();
            
            messagesDiv.innerHTML += `
                <div style="
                    background: #ffebee;
                    color: #c62828;
                    padding: 12px;
                    border-radius: 12px;
                    margin-bottom: 12px;
                    margin-right: 20px;
                    font-size: ${{config.message_font_size || '14px'}};
                ">Sorry, there was an error processing your request.</div>
            `;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            console.error('AI Error:', error);
        }});
    }}
    
    // Voice Recording Variables
    let isRecording = false;
    let mediaRecorder = null;
    let audioChunks = [];
    let recognition = null;
    
    // Initialize Speech Recognition for live voice
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {{
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = config.voice_transcription_language || 'en-US';
        
        recognition.onresult = function(event) {{
            let finalTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {{
                if (event.results[i].isFinal) {{
                    finalTranscript += event.results[i][0].transcript;
                }}
            }}
            
            if (finalTranscript) {{
                const input = document.getElementById('chat-input');
                input.value = finalTranscript;
                
                // Auto-send if configured
                if (config.auto_send_voice) {{
                    sendMessage();
                }}
            }}
        }};
        
        recognition.onerror = function(event) {{
            console.error('Speech recognition error:', event.error);
            stopVoiceRecording();
        }};
        
        recognition.onend = function() {{
            if (isRecording) {{
                recognition.start(); // Restart for continuous listening
            }}
        }};
    }}
    
    // Toggle voice recording
    window.toggleVoiceRecording = function() {{
        if (!recognition) {{
            alert('Speech recognition not supported in this browser');
            return;
        }}
        
        const voiceBtn = document.getElementById('voice-btn');
        const voiceStatus = document.getElementById('voice-status');
        
        if (isRecording) {{
            stopVoiceRecording();
        }} else {{
            startVoiceRecording();
        }}
    }};
    
    function startVoiceRecording() {{
        if (!recognition) return;
        
        isRecording = true;
        recognition.start();
        
        const voiceBtn = document.getElementById('voice-btn');
        const voiceStatus = document.getElementById('voice-status');
        
        if (voiceBtn) {{
            voiceBtn.style.background = '#ff4444';
            voiceBtn.style.color = 'white';
        }}
        if (voiceStatus) {{
            voiceStatus.textContent = 'Listening...';
        }}
        
        console.log('Voice recording started');
    }}
    
    function stopVoiceRecording() {{
        if (!recognition) return;
        
        isRecording = false;
        recognition.stop();
        
        const voiceBtn = document.getElementById('voice-btn');
        const voiceStatus = document.getElementById('voice-status');
        
        if (voiceBtn) {{
            voiceBtn.style.background = 'none';
            voiceBtn.style.color = '#666';
        }}
        if (voiceStatus) {{
            voiceStatus.textContent = 'Voice';
        }}
        
        console.log('Voice recording stopped');
    }}
    
    // Clipboard image pasting
    document.addEventListener('paste', function(event) {{
        if (!config.image_analysis_enabled) return;
        
        const clipboardItems = event.clipboardData.items;
        for (let item of clipboardItems) {{
            if (item.type.startsWith('image/')) {{
                const file = item.getAsFile();
                if (file) {{
                    handleClipboardImage(file);
                    event.preventDefault();
                }}
            }}
        }}
    }});
    
    function handleClipboardImage(file) {{
        const messagesDiv = document.getElementById('chat-messages');
        messagesDiv.innerHTML += `
            <div style="
                background: ${{config.user_message_background || config.primary_color || '#007bff'}};
                color: ${{config.user_message_color || 'white'}};
                padding: 12px;
                border-radius: 12px;
                margin-bottom: 12px;
                margin-left: 20px;
                font-size: ${{config.message_font_size || '14px'}};
            ">📋 Image pasted from clipboard</div>
        `;
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        
        sendToAI('', null, file);
    }}
    
    // Handle image upload
    window.handleImageUpload = function(event) {{
        const file = event.target.files[0];
        if (file) {{
            const messagesDiv = document.getElementById('chat-messages');
            messagesDiv.innerHTML += `
                <div style="
                    background: ${{config.user_message_background || config.primary_color || '#007bff'}};
                    color: ${{config.user_message_color || 'white'}};
                    padding: 12px;
                    border-radius: 12px;
                    margin-bottom: 12px;
                    margin-left: 20px;
                    font-size: ${{config.message_font_size || '14px'}};
                ">📷 Image uploaded</div>
            `;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            sendToAI('', null, file);
        }}
    }};
    
    // Handle file upload
    window.handleFileUpload = function(event) {{
        const file = event.target.files[0];
        if (file) {{
            const messagesDiv = document.getElementById('chat-messages');
            messagesDiv.innerHTML += `
                <div style="
                    background: ${{config.user_message_background || config.primary_color || '#007bff'}};
                    color: ${{config.user_message_color || 'white'}};
                    padding: 12px;
                    border-radius: 12px;
                    margin-bottom: 12px;
                    margin-left: 20px;
                    font-size: ${{config.message_font_size || '14px'}};
                ">📎 File uploaded: ${{file.name}}</div>
            `;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            // Handle file processing here (could send to backend for analysis)
            console.log('File uploaded:', file);
        }}
    }};
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', initWidget);
    }} else {{
        initWidget();
    }}
    
    // CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
        }}
        @keyframes bounce {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-10px); }}
        }}
        @keyframes shake {{
            0%, 100% {{ transform: translateX(0); }}
            25% {{ transform: translateX(-5px); }}
            75% {{ transform: translateX(5px); }}
        }}
        @keyframes glow {{
            0%, 100% {{ box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
            50% {{ box-shadow: 0 4px 20px rgba(0,123,255,0.4); }}
        }}
    `;
    document.head.appendChild(style);
}})();"""
    
    return HTMLResponse(content=script_content, media_type="application/javascript")


@router.post("/knowledge-base/{client_id}")
async def update_knowledge_base(client_id: str, request: Request):
    """Update knowledge base for a client - accepts both JSON and file uploads"""
    try:
        # Check content type
        content_type = request.headers.get("content-type", "")
        
        if "multipart/form-data" in content_type:
            # Handle file upload - redirect to proper file endpoint
            return {"error": "File uploads should use /api/files/widget-kb/{client_id}", "redirect_to": f"/api/files/widget-kb/{client_id}"}
        
        # Handle JSON data
        kb_data = await request.json()
        knowledge_bases[client_id] = kb_data.get("documents", [])
        
        # Broadcast KB update to all widgets
        await broadcast_to_client(client_id, {
            "type": "knowledge_base_update",
            "data": knowledge_bases[client_id]
        })
        
        return {"message": "Knowledge base updated", "client_id": client_id, "documents": len(knowledge_bases[client_id])}
        
    except Exception as e:
        logger.error(f"Error updating knowledge base for {client_id}: {e}")
        return {"error": f"Failed to update knowledge base: {str(e)}"}


@router.get("/knowledge-base/{client_id}")
async def get_knowledge_base(client_id: str):
    """Get knowledge base for a client"""
    # Get documents from database
    db_documents = widget_service.get_knowledge_base_documents(client_id)
    
    # Also check in-memory storage for backward compatibility
    memory_documents = knowledge_bases.get(client_id, [])
    
    # Combine both sources
    all_documents = db_documents + memory_documents
    
    return {
        "client_id": client_id,
        "documents": all_documents,
        "count": len(all_documents),
        "db_count": len(db_documents),
        "memory_count": len(memory_documents)
    }


@router.delete("/knowledge-base/{client_id}")
async def clear_knowledge_base(client_id: str):
    """Clear knowledge base for a client"""
    knowledge_bases[client_id] = []
    
    # Broadcast KB clear to all widgets
    await broadcast_to_client(client_id, {
        "type": "knowledge_base_update",
        "data": []
    })
    
    return {"message": "Knowledge base cleared", "client_id": client_id}

@router.get("/debug-upload/{client_id}")
async def debug_upload_endpoint(client_id: str, request: Request):
    """Debug endpoint to check upload routing"""
    return {
        "message": "Widget upload debug endpoint reached",
        "client_id": client_id,
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "correct_file_upload_endpoint": f"/api/files/widget/upload/{client_id}",
        "note": "This endpoint exists and routing is working correctly"
    }


@router.post("/analytics")
async def store_analytics_event(event_data: Dict):
    """Store analytics event (HTTP fallback)"""
    try:
        # Add timestamp if not present
        if "timestamp" not in event_data:
            event_data["timestamp"] = datetime.now(timezone.utc)
        
        analytics_events.append(AnalyticsEvent(**event_data))
        
        return {"status": "success", "message": "Analytics event stored"}
    except Exception as e:
        logger.error(f"Analytics storage error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/analytics/detailed/{client_id}")
async def get_detailed_analytics(client_id: str):
    """Get comprehensive real-time analytics for a client"""
    client_events = [event for event in analytics_events if event.client_id == client_id]
    
    # Real-time metrics
    from datetime import timezone
    now = datetime.now(timezone.utc)
    total_events = len(client_events)
    event_breakdown = {}
    hourly_data = {}
    daily_data = {}
    user_sessions = {}
    conversation_analysis = {}
    lead_analysis = {}
    user_demographics = {}
    active_users = set()
    
    # Lead detection keywords
    lead_keywords = [
        "buy", "purchase", "price", "cost", "interested", "contact", "demo", 
        "trial", "quote", "subscribe", "sign up", "book", "schedule", "call",
        "email", "phone", "address", "business", "company"
    ]
    
    for event in client_events:
        # Event type breakdown
        event_breakdown[event.event_type] = event_breakdown.get(event.event_type, 0) + 1
        
        # Time-based analytics
        hour_key = event.timestamp.strftime("%Y-%m-%d %H:00")
        day_key = event.timestamp.strftime("%Y-%m-%d")
        hourly_data[hour_key] = hourly_data.get(hour_key, 0) + 1
        daily_data[day_key] = daily_data.get(day_key, 0) + 1
        
        # Active users (last 30 minutes)
        event_timestamp = event.timestamp
        if not event_timestamp.tzinfo:
            # Make naive datetime timezone-aware
            event_timestamp = event_timestamp.replace(tzinfo=timezone.utc)
        
        if (now - event_timestamp).total_seconds() < 1800:  # 30 minutes
            if event.user_id:
                active_users.add(event.user_id)
        
        # User session analysis
        if event.session_id not in user_sessions:
            # Ensure event timestamp is timezone-aware
            event_timestamp = event.timestamp
            if not event_timestamp.tzinfo:
                event_timestamp = event_timestamp.replace(tzinfo=timezone.utc)
            
            user_sessions[event.session_id] = {
                "user_id": event.user_id,
                "user_info": event.user_info or {},
                "start_time": event_timestamp,
                "last_activity": event_timestamp,
                "events": [],
                "total_events": 0,
                "conversation_length": 0,
                "lead_score": 0.0,
                "sentiment": "neutral",
                "topics": [],
                "device_info": event.device_info or {},
                "location": event.user_location or {}
            }
        
        session = user_sessions[event.session_id]
        
        # Ensure event timestamp is timezone-aware for comparison
        event_timestamp = event.timestamp
        if not event_timestamp.tzinfo:
            event_timestamp = event_timestamp.replace(tzinfo=timezone.utc)
        
        session["events"].append({
            "type": event.event_type,
            "timestamp": event_timestamp,
            "metadata": event.metadata,
            "conversation_data": event.conversation_data or {}
        })
        session["total_events"] += 1
        session["last_activity"] = max(session["last_activity"], event_timestamp)
        
        # Conversation analysis
        if event.conversation_data and "message" in event.conversation_data:
            message = event.conversation_data["message"].lower()
            session["conversation_length"] += len(message.split())
            
            # Lead scoring based on keywords
            lead_score = 0
            for keyword in lead_keywords:
                if keyword in message:
                    lead_score += 0.1
            
            session["lead_score"] = min(session["lead_score"] + lead_score, 1.0)
            
            # Sentiment analysis (simple keyword-based)
            positive_words = ["good", "great", "excellent", "love", "amazing", "perfect", "wonderful"]
            negative_words = ["bad", "terrible", "awful", "hate", "horrible", "worst", "disappointed"]
            
            pos_count = sum(1 for word in positive_words if word in message)
            neg_count = sum(1 for word in negative_words if word in message)
            
            if pos_count > neg_count:
                session["sentiment"] = "positive"
            elif neg_count > pos_count:
                session["sentiment"] = "negative"
        
        # User demographics
        if event.user_info:
            user_key = event.user_id or event.session_id
            user_demographics[user_key] = event.user_info
    
    # Conversation insights
    total_conversations = len([s for s in user_sessions.values() if s["total_events"] > 1])
    avg_conversation_length = sum(s["conversation_length"] for s in user_sessions.values()) / max(len(user_sessions), 1)
    
    # Lead analysis
    high_quality_leads = [s for s in user_sessions.values() if s["lead_score"] > 0.5]
    potential_leads = [s for s in user_sessions.values() if s["lead_score"] > 0.2]
    
    # Response time analysis
    response_times = []
    for session in user_sessions.values():
        events = session["events"]
        for i in range(len(events) - 1):
            if events[i]["type"] == "message_sent" and events[i+1]["type"] == "ai_response":
                time_diff = (events[i+1]["timestamp"] - events[i]["timestamp"]).total_seconds()
                response_times.append(time_diff)
    
    avg_response_time = sum(response_times) / max(len(response_times), 1) if response_times else 0
    
    # Geographic distribution
    geographic_data = {}
    for session in user_sessions.values():
        if session["location"] and "country" in session["location"]:
            country = session["location"]["country"]
            geographic_data[country] = geographic_data.get(country, 0) + 1
    
    # Device analytics
    device_breakdown = {}
    browser_breakdown = {}
    for session in user_sessions.values():
        if session["device_info"]:
            device_type = session["device_info"].get("device_type", "unknown")
            browser = session["device_info"].get("browser", "unknown")
            device_breakdown[device_type] = device_breakdown.get(device_type, 0) + 1
            browser_breakdown[browser] = browser_breakdown.get(browser, 0) + 1
    
    # Real-time metrics
    recent_events = [event.dict() for event in client_events[-50:]]  # Last 50 events
    
    return {
        "client_id": client_id,
        "last_updated": now.isoformat(),
        "summary": {
            "total_events": total_events,
            "unique_sessions": len(user_sessions),
            "active_users_now": len(active_users),
            "total_conversations": total_conversations,
            "avg_conversation_length": round(avg_conversation_length, 1),
            "avg_response_time": round(avg_response_time, 2),
            "event_breakdown": event_breakdown
        },
        "lead_analytics": {
            "high_quality_leads": len(high_quality_leads),
            "potential_leads": len(potential_leads),
            "conversion_rate": round((len(high_quality_leads) / max(len(user_sessions), 1)) * 100, 2),
            "top_leads": [
                {
                    "session_id": s["user_id"] or s["start_time"].strftime("%H:%M"),
                    "lead_score": round(s["lead_score"], 2),
                    "user_info": s["user_info"],
                    "last_activity": s["last_activity"].isoformat(),
                    "conversation_length": s["conversation_length"],
                    "sentiment": s["sentiment"]
                }
                for s in sorted(user_sessions.values(), key=lambda x: x["lead_score"], reverse=True)[:10]
                if s["lead_score"] > 0.1
            ]
        },
        "user_analytics": {
            "demographics": user_demographics,
            "geographic_distribution": geographic_data,
            "device_breakdown": device_breakdown,
            "browser_breakdown": browser_breakdown,
            "sentiment_distribution": {
                "positive": len([s for s in user_sessions.values() if s["sentiment"] == "positive"]),
                "neutral": len([s for s in user_sessions.values() if s["sentiment"] == "neutral"]),
                "negative": len([s for s in user_sessions.values() if s["sentiment"] == "negative"])
            }
        },
        "time_analytics": {
            "hourly_data": dict(sorted(hourly_data.items())[-24:]),  # Last 24 hours
            "daily_data": dict(sorted(daily_data.items())[-7:])  # Last 7 days
        },
        "live_sessions": [
            {
                "session_id": session_id,
                "user_id": session["user_id"],
                "user_info": session["user_info"],
                "start_time": session["start_time"].isoformat(),
                "last_activity": session["last_activity"].isoformat(),
                "events_count": session["total_events"],
                "lead_score": round(session["lead_score"], 2),
                "sentiment": session["sentiment"],
                "is_active": (now - session["last_activity"]).total_seconds() < 300,  # Active in last 5 minutes
                "location": session["location"],
                "device": session["device_info"]
            }
            for session_id, session in sorted(
                user_sessions.items(), 
                key=lambda x: x[1]["last_activity"], 
                reverse=True
            )[:20]  # Show top 20 recent sessions
        ],
        "conversation_insights": {
            "most_common_topics": [],  # Can be enhanced with NLP
            "popular_questions": [],   # Can be enhanced with question detection
            "satisfaction_metrics": {
                "positive_feedback": len([e for e in client_events if e.event_type == "feedback_given" and e.metadata.get("rating", 0) > 3]),
                "negative_feedback": len([e for e in client_events if e.event_type == "feedback_given" and e.metadata.get("rating", 0) <= 2])
            }
        },
        "recent_events": recent_events
    }
async def get_widget_analytics(client_id: str):
    """Get analytics data for a widget"""
    client_events = [event for event in analytics_events if event.client_id == client_id]
    
    # Basic analytics aggregation
    total_events = len(client_events)
    event_types = {}
    for event in client_events:
        event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
    
    return {
        "client_id": client_id,
        "total_events": total_events,
        "event_breakdown": event_types,
        "recent_events": [event.dict() for event in client_events[-10:]]  # Last 10 events
    }

@router.get("/embed/{client_id}")
async def get_embed_code(client_id: str, request: Request):
    """Get HTML embed code for the widget"""
    server_url = f"{request.url.scheme}://{request.url.netloc}"
    
    embed_code = f'''
<!-- AI Knowledge Base Widget -->
<script async src="{server_url}/api/widget/script/{client_id}"></script>
'''
    
    return {
        "client_id": client_id,
        "embed_code": embed_code,
        "instructions": "Copy and paste this code into your website's HTML, preferably before the closing </body> tag."
    }

@router.post("/generate")
async def generate_new_widget(user_email: str = Depends(get_user_email_from_token)):
    """Generate a new widget with unique client_id for authenticated user"""
    client_id = str(uuid.uuid4())
    
    # Create default configuration
    default_config = WidgetConfig(
        client_id=client_id,
        domain="",
        chat_title="AI Assistant",
        welcome_message="Hello! How can I help you today?"
    )
    
    # Save to database with user email
    success = widget_service.save_widget_config(client_id, default_config.dict(), user_email)
    
    if success:
        # Keep in memory cache for immediate use
        widget_configs[client_id] = default_config
        
        return {
            "client_id": client_id,
            "config": default_config.dict(),
            "user_email": user_email,
            "next_steps": [
                "Configure the widget using POST /api/widget/config",
                "Get embed code using GET /api/widget/embed/{client_id}",
                "Add embed code to your website"
            ]
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to create widget")
