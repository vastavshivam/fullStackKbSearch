import React, { useState, useRef, useEffect } from 'react';
import ChatHistory from '../pages/ChatHistory';
import '../pages/Chat.css';
import axios from 'axios';
import { useAuth } from '../hooks/useAuth';
import { connectWebSocketChat, configureWhatsApp, sendWhatsAppMessage, createChatSession, storeChatMessage, getChatHistory } from '../services/api';

function generateSummary(messages) {
  const userMsg = messages.find(m => m.sender === 'user');
  const botMsg = messages.slice().reverse().find(m => m.sender === 'bot');
  if (!userMsg || !botMsg) return 'New Chat';
  return `${userMsg.text.slice(0, 40)} → ${botMsg.text.slice(0, 40)}`;
}

export default function Chat() {
  const { user } = useAuth();
  const [sessionId, setSessionId] = useState('');
  const [messages, setMessages] = useState([{ sender: 'bot', text: "Welcome to AppGallop! ✨" }]);
  const [input, setInput] = useState('');
  const [history, setHistory] = useState<{messages: any[], summary: string}[]>([]);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function initSession() {
      const userId = user?.id || 'guest';
      try {
        const res = await createChatSession(userId);
        setSessionId(res.data.session_id);
        const histRes = await getChatHistory(res.data.session_id);
        if (histRes.data.history && histRes.data.history.length > 0) {
          setMessages(histRes.data.history.map(m => ({ sender: m.sender, text: m.message })));
        }
      } catch (err) {
        console.error('Failed to initialize chat session:', err);
        setSessionId('');
        setMessages([{ sender: 'bot', text: "Welcome to AppGallop! ✨" }]);
      }
    }
    
    if (user) {
      initSession();
    }
    
    const ws = connectWebSocketChat();
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages((prev) => [...prev, { sender: 'bot', text: data.message }]);
    };
    return () => ws.close();
  }, [user]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !sessionId) return;
    setMessages(prev => [...prev, { sender: 'user', text: input }]);
    setInput('');
    setMessages(prev => [...prev, { sender: 'bot', text: "Let me get that for you..." }]);
    try {
      await storeChatMessage(sessionId, 'user', input);
      const res = await axios.post('/api/qa/static-chat', { question: input });
      const answer = (res.data as any)?.answer || "Sorry, I couldn't find an answer.";
      await storeChatMessage(sessionId, 'bot', answer);
      setMessages(prev => {
        const msgs = prev.slice(0, -1);
        const newMsgs = [...msgs, { sender: 'bot', text: answer }];
        setHistory(h => [{ messages: newMsgs, summary: generateSummary(newMsgs) }, ...h]);
        return newMsgs;
      });
    } catch (err) {
      setMessages(prev => {
        const msgs = prev.slice(0, -1);
        const newMsgs = [...msgs, { sender: 'bot', text: "Sorry, there was an error getting the answer." }];
        setHistory(h => [{ messages: newMsgs, summary: generateSummary(newMsgs) }, ...h]);
        return newMsgs;
      });
    }
  };

  const handleNewChat = async () => {
    const userId = user?.id || 'guest';
    try {
      const res = await createChatSession(userId);
      setSessionId(res.data.session_id);
      setMessages([{ sender: 'bot', text: "New chat started! 👋" }]);
    } catch (err) {
      console.error('Failed to create new chat session:', err);
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
            <div key={i} className={`chat-bubble ${msg.sender}`}>{msg.text}</div>
          ))}
          <div ref={bottomRef} />
        </div>
        <form className="chat-input" onSubmit={handleSend}>
          <input
            type="text"
            placeholder="Send a message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button type="submit">Send</button>
        </form>
      </div>
    </div>
  );
}
