from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
import uuid
import asyncio
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

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

class AnalyticsEvent(BaseModel):
    client_id: str
    event_type: str  # chat_start, message_sent, file_uploaded, feedback_given
    timestamp: datetime = datetime.now()
    user_id: Optional[str] = None
    session_id: str
    metadata: Optional[Dict] = {}

class ToggleRequest(BaseModel):
    is_active: bool

# In-memory storage (replace with Redis/DB in production)
active_connections: Dict[str, List[WebSocket]] = {}  # Multiple connections per client
widget_configs: Dict[str, WidgetConfig] = {}
analytics_events: List[AnalyticsEvent] = []
knowledge_bases: Dict[str, List[Dict]] = {}  # Client KB data

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
async def list_widgets():
    """Get list of all widgets"""
    widgets_list = []
    for client_id, config in widget_configs.items():
        widgets_list.append({
            **config.dict(),
            "connection_count": len(active_connections.get(client_id, [])),
            "created_at": "2025-01-01"  # Add proper timestamp in production
        })
    
    return {"widgets": widgets_list, "total": len(widgets_list)}

@router.post("/config")
async def create_or_update_widget_config(config: WidgetConfig):
    """Create or update widget configuration"""
    widget_configs[config.client_id] = config
    
    # Broadcast update to connected widgets
    await broadcast_to_client(config.client_id, {
        "type": "config_update",
        "data": config.dict()
    })
    
    return {"message": "Widget configuration updated", "client_id": config.client_id}

@router.get("/config/{client_id}")
async def get_widget_config(client_id: str):
    """Get widget configuration"""
    if client_id not in widget_configs:
        raise HTTPException(status_code=404, detail="Widget configuration not found")
    
    return widget_configs[client_id]

@router.delete("/config/{client_id}")
async def delete_widget_config(client_id: str):
    """Delete widget configuration"""
    if client_id not in widget_configs:
        raise HTTPException(status_code=404, detail="Widget configuration not found")
    
    del widget_configs[client_id]
    
    # Disconnect WebSocket if active
    if client_id in active_connections:
        await active_connections[client_id].close()
        del active_connections[client_id]
    
    return {"message": "Widget configuration deleted"}

@router.patch("/toggle/{client_id}")
async def toggle_widget_status(client_id: str, toggle_request: ToggleRequest):
    """Toggle widget active/inactive status"""
    if client_id not in widget_configs:
        raise HTTPException(status_code=404, detail="Widget configuration not found")
    
    # Update the is_active status
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
    
    # Get client config or use defaults
    config = widget_configs.get(client_id, WidgetConfig(client_id=client_id, domain=""))
    
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
                    <div style="display: flex; gap: 8px;">
                        <input type="text" id="chat-input" placeholder="${{config.input_placeholder || 'Type your message...'}}" style="
                            flex: 1;
                            padding: 12px;
                            border: 1px solid ${{config.input_border_color || '#ddd'}};
                            border-radius: ${{config.input_border_radius || '8px'}};
                            font-size: ${{config.input_font_size || '14px'}};
                            background: ${{config.input_background || 'white'}};
                            color: ${{config.input_text_color || '#333'}};
                        ">
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
        
        // Send to backend via WebSocket
        if (websocket && websocket.readyState === WebSocket.OPEN) {{
            websocket.send(JSON.stringify({{
                type: 'chat_message',
                data: {{
                    message: message,
                    client_id: clientId,
                    timestamp: new Date().toISOString(),
                    session_id: 'session_' + Date.now()
                }}
            }}));
            
            // Send analytics
            websocket.send(JSON.stringify({{
                type: 'analytics',
                data: {{
                    event_type: 'message_sent',
                    client_id: clientId,
                    timestamp: new Date().toISOString(),
                    session_id: 'session_' + Date.now(),
                    metadata: {{
                        message_length: message.length,
                        page_url: window.location.href
                    }}
                }}
            }}));
        }}
        
        // Simulate AI response (replace with actual API call)
        setTimeout(() => {{
            messagesDiv.innerHTML += `
                <div style="
                    background: ${{config.bot_message_background || '#e9ecef'}};
                    color: ${{config.bot_message_color || '#333'}};
                    padding: 12px;
                    border-radius: 12px;
                    margin-bottom: 12px;
                    margin-right: 20px;
                    font-size: ${{config.message_font_size || '14px'}};
                ">Thanks for your message: "${{message}}". How else can I help?</div>
            `;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }}, 1000);
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
async def update_knowledge_base(client_id: str, kb_data: Dict):
    """Update knowledge base for a client"""
    knowledge_bases[client_id] = kb_data.get("documents", [])
    
    # Broadcast KB update to all widgets
    await broadcast_to_client(client_id, {
        "type": "knowledge_base_update",
        "data": knowledge_bases[client_id]
    })
    
    return {"message": "Knowledge base updated", "client_id": client_id, "documents": len(knowledge_bases[client_id])}


@router.get("/knowledge-base/{client_id}")
async def get_knowledge_base(client_id: str):
        const wsUrl = serverUrl.replace('http', 'ws') + '/api/widget/ws/' + clientId;
        ws = new WebSocket(wsUrl);
        
        ws.onopen = function() {{
            console.log('Widget WebSocket connected');
            reconnectAttempts = 0;
            
            // Send initial analytics
            sendAnalytics('widget_loaded', {{
                url: window.location.href,
                referrer: document.referrer,
                user_agent: navigator.userAgent
            }});
        }};
        
        ws.onmessage = function(event) {{
            const message = JSON.parse(event.data);
            
            if (message.type === 'config_update') {{
                updateWidgetConfig(message.data);
            }} else if (message.type === 'knowledge_base_update') {{
                updateKnowledgeBase(message.data);
            }} else if (message.type === 'broadcast_message') {{
                addMessage('assistant', message.data.message, true);
            }}
        }};
        
        ws.onclose = function() {{
            console.log('Widget WebSocket disconnected');
            
            // Reconnect with exponential backoff
            if (reconnectAttempts < maxReconnectAttempts) {{
                const delay = Math.pow(2, reconnectAttempts) * 1000;
                setTimeout(() => {{
                    reconnectAttempts++;
                    connectWebSocket();
                }}, delay);
            }}
        }};
        
        ws.onerror = function(error) {{
            console.error('Widget WebSocket error:', error);
        }};
    }}
    
    // Connect WebSocket
    connectWebSocket();
    
    // Event handlers
    const widgetButton = document.getElementById('widget-button');
    const widgetChat = document.getElementById('widget-chat');
    const closeChat = document.getElementById('close-chat');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-message');
    const messagesContainer = document.getElementById('chat-messages');
    
    widgetButton.addEventListener('click', function() {{
        widgetChat.style.display = 'flex';
        widgetButton.style.display = 'none';
        
        // Send analytics event
        sendAnalytics('chat_start', {{}});
    }});
    
    closeChat.addEventListener('click', function() {{
        widgetChat.style.display = 'none';
        widgetButton.style.display = 'flex';
    }});
    
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', function(e) {{
        if (e.key === 'Enter') {{
            sendMessage();
        }}
    }});
    
    function sendMessage() {{
        const message = chatInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessage('user', message);
        chatInput.value = '';
        
        // Send to backend
        fetch(serverUrl + '/api/chat/widget', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json'
            }},
            body: JSON.stringify({{
                message: message,
                client_id: clientId,
                session_id: sessionId
            }})
        }})
        .then(response => response.json())
        .then(data => {{
            addMessage('assistant', data.response);
        }})
        .catch(error => {{
            addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
            console.error('Chat error:', error);
        }});
        
        // Send analytics
        sendAnalytics('message_sent', {{ message_length: message.length }});
    }}
    
    function addMessage(sender, content, isSystemMessage = false) {{
        const messageDiv = document.createElement('div');
        messageDiv.style.cssText = `
            background: ${{sender === 'user' ? config.primary_color : 'white'}};
            color: ${{sender === 'user' ? 'white' : '#333'}};
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 12px;
            ${{sender === 'assistant' ? 'border-left: 4px solid ' + config.primary_color : ''}};
            ${{isSystemMessage ? 'font-style: italic; opacity: 0.8;' : ''}};
        `;
        messageDiv.textContent = content;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Analytics for received messages
        if (sender === 'assistant' && !isSystemMessage) {{
            sendAnalytics('message_received', {{
                response_length: content.length,
                response_time: Date.now()
            }});
        }}
    }}
    
    function sendAnalytics(eventType, metadata = {{}}) {{
        if (!config.analytics_enabled) return;
        
        const analyticsData = {{
            type: 'analytics',
            data: {{
                event_type: eventType,
                session_id: sessionId,
                timestamp: new Date().toISOString(),
                metadata: {{
                    ...metadata,
                    page_url: window.location.href,
                    page_title: document.title,
                    viewport_width: window.innerWidth,
                    viewport_height: window.innerHeight
                }}
            }}
        }};
        
        if (ws && ws.readyState === WebSocket.OPEN) {{
            ws.send(JSON.stringify(analyticsData));
        }}
        
        // Also send to backend via HTTP as fallback
        fetch(serverUrl + '/api/widget/analytics', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(analyticsData.data)
        }}).catch(error => console.error('Analytics error:', error));
    }}
    
    function updateWidgetConfig(newConfig) {{
        console.log('Live config update received:', newConfig);
        
        // Update config object
        Object.assign(config, newConfig);
        
        // Update UI elements dynamically
        const widgetButton = document.getElementById('widget-button');
        const chatHeader = document.querySelector('#widget-chat div');
        const sendButton = document.getElementById('send-message');
        const chatTitle = document.querySelector('#widget-chat div span');
        
        if (widgetButton) {{
            widgetButton.style.background = config.primary_color;
        }}
        
        if (chatHeader) {{
            chatHeader.style.background = config.primary_color;
        }}
        
        if (sendButton) {{
            sendButton.style.background = config.primary_color;
        }}
        
        if (chatTitle) {{
            chatTitle.textContent = config.chat_title;
        }}
        
        // Update position if changed
        const container = document.getElementById('ai-kb-widget-' + clientId);
        if (container) {{
            container.style.cssText = container.style.cssText.replace(
                /(bottom|top|left|right): \d+px;/g, 
                ''
            ) + '{get_position_styles("' + config.position + '")}';
        }}
        
        // Send analytics for config change
        sendAnalytics('config_updated', {{ 
            changes: Object.keys(newConfig),
            new_theme: config.theme,
            new_position: config.position
        }});
    }}
    
    function updateKnowledgeBase(kbData) {{
        console.log('Knowledge base updated:', kbData);
        
        // Update local knowledge base
        config.knowledge_base = kbData;
        
        // Show notification about KB update
        if (kbData && kbData.length > 0) {{
            addMessage('assistant', `✨ Knowledge base updated with ${{kbData.length}} new documents!`, true);
        }}
        
        sendAnalytics('knowledge_base_updated', {{
            document_count: kbData ? kbData.length : 0
        }});
    }}
    
    // Track user interactions
    document.addEventListener('click', function(e) {{
        if (e.target.closest('#ai-kb-widget-' + clientId)) {{
            sendAnalytics('widget_interaction', {{
                element: e.target.id || e.target.className || 'unknown',
                click_x: e.clientX,
                click_y: e.clientY
            }});
        }}
    }});
    
    // Track page visibility changes
    document.addEventListener('visibilitychange', function() {{
        sendAnalytics('page_visibility', {{
            hidden: document.hidden
        }});
    }});
    
    // Track when user leaves page
    window.addEventListener('beforeunload', function() {{
        sendAnalytics('session_end', {{
            session_duration: Date.now() - sessionStartTime
        }});
    }});
    
    const sessionStartTime = Date.now();
}})();
"""
    
    return HTMLResponse(content=script_content, media_type="application/javascript")

@router.post("/knowledge-base/{client_id}")
async def update_knowledge_base(client_id: str, kb_data: Dict):
    """Update knowledge base for a client"""
    knowledge_bases[client_id] = kb_data.get("documents", [])
    
    # Broadcast KB update to all widgets
    await broadcast_to_client(client_id, {
        "type": "knowledge_base_update",
        "data": knowledge_bases[client_id]
    })
    
    return {"message": "Knowledge base updated", "client_id": client_id, "documents": len(knowledge_bases[client_id])}

@router.get("/knowledge-base/{client_id}")
async def get_knowledge_base(client_id: str):
    """Get knowledge base for a client"""
    return {
        "client_id": client_id,
        "documents": knowledge_bases.get(client_id, []),
        "count": len(knowledge_bases.get(client_id, []))
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

@router.post("/analytics")
async def store_analytics_event(event_data: Dict):
    """Store analytics event (HTTP fallback)"""
    try:
        # Add timestamp if not present
        if "timestamp" not in event_data:
            event_data["timestamp"] = datetime.now()
        
        analytics_events.append(AnalyticsEvent(**event_data))
        
        return {"status": "success", "message": "Analytics event stored"}
    except Exception as e:
        logger.error(f"Analytics storage error: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/analytics/detailed/{client_id}")
async def get_detailed_analytics(client_id: str):
    """Get detailed analytics for a client"""
    client_events = [event for event in analytics_events if event.client_id == client_id]
    
    # Detailed analytics processing
    total_events = len(client_events)
    event_breakdown = {}
    hourly_data = {}
    user_sessions = {}
    
    for event in client_events:
        # Event type breakdown
        event_breakdown[event.event_type] = event_breakdown.get(event.event_type, 0) + 1
        
        # Hourly breakdown
        hour_key = event.timestamp.strftime("%Y-%m-%d %H:00")
        hourly_data[hour_key] = hourly_data.get(hour_key, 0) + 1
        
        # User sessions
        if event.session_id not in user_sessions:
            user_sessions[event.session_id] = {
                "start_time": event.timestamp,
                "events": [],
                "total_events": 0
            }
        user_sessions[event.session_id]["events"].append({
            "type": event.event_type,
            "timestamp": event.timestamp,
            "metadata": event.metadata
        })
        user_sessions[event.session_id]["total_events"] += 1
    
    return {
        "client_id": client_id,
        "summary": {
            "total_events": total_events,
            "unique_sessions": len(user_sessions),
            "event_breakdown": event_breakdown
        },
        "hourly_data": hourly_data,
        "sessions": user_sessions,
        "recent_events": [event.dict() for event in client_events[-20:]]
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
async def generate_new_widget():
    """Generate a new widget with unique client_id"""
    client_id = str(uuid.uuid4())
    
    # Create default configuration
    default_config = WidgetConfig(
        client_id=client_id,
        domain="",
        chat_title="AI Assistant",
        welcome_message="Hello! How can I help you today?"
    )
    
    widget_configs[client_id] = default_config
    
    return {
        "client_id": client_id,
        "config": default_config.dict(),
        "next_steps": [
            "Configure the widget using POST /api/widget/config",
            "Get embed code using GET /api/widget/embed/{client_id}",
            "Add embed code to your website"
        ]
    }
