import React, { useState, useRef, useEffect } from 'react';
import ChatHistory from '../pages/ChatHistory';
import '../pages/Chat.css';
import { connectWebSocketChat, configureWhatsApp, sendWhatsAppMessage, createChatSession, storeChatMessage, getChatHistory, askStaticChat, chatWithImage } from '../services/api';

function generateSummary(messages) {
  const userMsg = messages.find(m => m.sender === 'user');
  const botMsg = messages.slice().reverse().find(m => m.sender === 'bot');
  if (!userMsg || !botMsg) return 'New Chat';
  return `${userMsg.text.slice(0, 40)} → ${botMsg.text.slice(0, 40)}`;
}

interface Message {
  sender: 'user' | 'bot';
  text: string;
  image?: string;
}

export default function Chat() {
  const [sessionId, setSessionId] = useState('');
  const [messages, setMessages] = useState<Message[]>([{ sender: 'bot', text: "Welcome to AppGallop! ✨" }]);
  const [input, setInput] = useState('');
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [history, setHistory] = useState<{messages: any[], summary: string}[]>([]);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const initSession = async () => {
      try {
        const res = await createChatSession('anonymous');
        setSessionId(res.data.session_id);
        
        // Try to get chat history with better error handling
        try {
          const histRes = await getChatHistory(res.data.session_id);
          if (histRes.data && histRes.data.length > 0) {
            setMessages(histRes.data.map((m: any) => ({ sender: m.sender, text: m.message })));
          }
        } catch (histErr) {
          console.warn('Failed to load chat history:', histErr);
          // Continue without history - not critical
        }
      } catch (err: any) {
        console.error('Failed to create session:', err);
        if (err.code === 'ERR_NETWORK' || err.message?.includes('CORS')) {
          setMessages([{ sender: 'bot', text: "⚠️ Connection issue detected. Please check if the backend server is running on http://localhost:8004" }]);
        } else {
          setSessionId(''); // Chat will still work without session
          setMessages([{ sender: 'bot', text: "Welcome to AppGallop! ✨ (Session creation failed, but you can still chat)" }]);
        }
      }
    }
    initSession();
    
    try {
      const ws = connectWebSocketChat();
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setMessages((prev) => [...prev, { sender: 'bot', text: data.message }]);
      };
      return () => ws.close();
    } catch (err) {
      console.error('WebSocket connection failed:', err);
    }
  }, []);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() && !selectedImage) return;
    
    setIsLoading(true);
    const userMessage = input || '📷 Shared an image';
    
    // Add user message
    const userMsg: Message = {
      sender: 'user',
      text: userMessage,
      image: imagePreview || undefined
    };
    setMessages(prev => [...prev, userMsg]);
    
    const originalInput = input;
    setInput('');
    
    // Clear image after sending
    const originalImage = selectedImage;
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    
    // Show loading message
    const loadingMsg: Message = { sender: 'bot', text: "Let me analyze that for you..." };
    setMessages(prev => [...prev, loadingMsg]);
    
    try {
      // Store user message if session exists
      if (sessionId) {
        await storeChatMessage(sessionId, 'user', userMessage);
      }
      
      let res;
      if (originalImage) {
        // Send image with optional text
        res = await chatWithImage(originalInput, originalImage);
      } else {
        // Send text only
        res = await askStaticChat(originalInput);
      }
      
      const answer = (res.data as any)?.answer || "Sorry, I couldn't process your request.";
      
      // Store bot response if session exists
      if (sessionId) {
        await storeChatMessage(sessionId, 'bot', answer);
      }
      
      setMessages(prev => {
        const msgs = prev.slice(0, -1); // Remove loading message
        const newMsgs = [...msgs, { sender: 'bot' as const, text: answer }];
        setHistory(h => [{ messages: newMsgs, summary: generateSummary(newMsgs) }, ...h]);
        return newMsgs;
      });
    } catch (err: any) {
      console.error('Chat error:', err);
      
      let errorMessage = "Sorry, there was an error processing your request.";
      
      // Provide more specific error messages
      if (err.code === 'NETWORK_ERROR' || err.message?.includes('CORS')) {
        errorMessage = "Connection error. Please check if the server is running.";
      } else if (err.response?.status === 500) {
        errorMessage = "Server error. Please try again in a moment.";
      } else if (err.response?.status === 413) {
        errorMessage = "Image too large. Please try a smaller image.";
      } else if (err.message?.includes('timeout')) {
        errorMessage = "Request timed out. Please try again with a smaller image.";
      } else if (originalImage && err.response?.status >= 400) {
        errorMessage = "Error processing image. Please try a different image or text only.";
      }
      
      setMessages(prev => {
        const msgs = prev.slice(0, -1); // Remove loading message
        const newMsgs = [...msgs, { sender: 'bot' as const, text: errorMessage }];
        setHistory(h => [{ messages: newMsgs, summary: generateSummary(newMsgs) }, ...h]);
        return newMsgs;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        alert('Please select an image file.');
        return;
      }
      
      // Validate file size (10MB limit)
      if (file.size > 10 * 1024 * 1024) {
        alert('Image file too large. Maximum size is 10MB.');
        return;
      }
      
      setSelectedImage(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const clearImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleNewChat = async () => {
    const userId = localStorage.getItem('userId') || 'guest';
    try {
      const res = await createChatSession(userId);
      setSessionId(res.data.session_id);
      setMessages([{ sender: 'bot', text: "New chat started! 👋" }]);
    } catch (err) {
      setSessionId('');
      setMessages([{ sender: 'bot', text: "New chat started! 👋" }]);
    }
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sessionId]);

  return (
    <div className="chat-layout">
      <div className={`chat-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <ChatHistory 
          history={history} 
          onNewChat={handleNewChat} 
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
      </div>
      <div className="chat-main">
        <div className="chat-header">
          <img src="/AppgallopLG.png" alt="AppGallop Logo" className="header-logo" />
          AppGallop Assistant
        </div>
        <div className="chat-body">
          {messages.map((msg, i) => (
            <div key={i} className={`chat-bubble ${msg.sender}`}>
              {msg.image && (
                <img 
                  src={msg.image} 
                  alt="Shared image" 
                  style={{ 
                    maxWidth: '300px', 
                    maxHeight: '300px', 
                    borderRadius: '8px', 
                    marginBottom: '8px',
                    display: 'block'
                  }} 
                />
              )}
              {msg.text}
              {isLoading && msg.text.includes("Let me analyze") && (
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              )}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
        
        {/* Image preview section */}
        {imagePreview && (
          <div className="image-preview-section">
            <div className="image-preview-container">
              <img 
                src={imagePreview} 
                alt="Preview" 
                className="image-preview"
              />
              <span className="image-preview-text">Image selected</span>
              <button 
                type="button"
                onClick={clearImage}
                className="image-preview-close"
              >
                ×
              </button>
            </div>
          </div>
        )}
        
        <form className="chat-input" onSubmit={handleSend}>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageSelect}
            style={{ display: 'none' }}
          />
          <button 
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="image-upload-btn"
            disabled={isLoading}
            title="Upload image"
          >
            📷
          </button>
          <input
            type="text"
            placeholder={selectedImage ? "Ask about your image..." : "Send a message..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend(e);
              }
            }}
          />
          <button 
            type="submit" 
            disabled={isLoading || (!input.trim() && !selectedImage)}
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  );
}
