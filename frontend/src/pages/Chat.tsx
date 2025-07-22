import React, { useState, useRef, useEffect } from 'react';
import ChatHistory from '../pages/ChatHistory';
import '../pages/Chat.css';
import axios from 'axios';
import { connectWebSocketChat, configureWhatsApp, sendWhatsAppMessage } from '../services/api'; // Corrected import path

// Simple summary function for demo (replace with backend call for advanced)
function generateSummary(messages) {
  // Use first user question and last bot answer for summary
  const userMsg = messages.find(m => m.sender === 'user');
  const botMsg = messages.slice().reverse().find(m => m.sender === 'bot');
  if (!userMsg || !botMsg) return 'New Chat';
  return `${userMsg.text.slice(0, 40)} → ${botMsg.text.slice(0, 40)}`;
}

/** ─────────── Custom type for what the server sends back ─────────── */
interface ChatResponse {
  answer: string;
}

export default function Chat() {
  const [messages, setMessages] = useState([{ sender: 'bot', text: "Welcome to AppG! ✨" }]);
  const [input, setInput] = useState('');
  // History now stores {messages, summary}
  const [history, setHistory] = useState<{messages: any[], summary: string}[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    setMessages(prev => [...prev, { sender: 'user', text: input }]);
    setInput('');
    setMessages(prev => [...prev, { sender: 'bot', text: "Let me get that for you..." }]);

    try {
      const res = await axios.post<ChatResponse>('/api/qa/static-chat', { question: input });
      const answer = res.data.answer || "Sorry, I couldn't find an answer.";
      setMessages(prev => {
        const msgs = prev.slice(0, -1); // drop loading
        // Update history with summary
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

  const handleNewChat = () => setMessages([{ sender: 'bot', text: "New chat started! 👋" }]);

  useEffect(() => {
    const ws = connectWebSocketChat();
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages((prev) => [...prev, { sender: 'bot', text: data.message }]);
    };
    return () => ws.close();
  }, []);

  const handleWhatsAppConfig = async (config) => {
    try {
      await configureWhatsApp(config);
      alert('WhatsApp configured successfully!');
    } catch (error) {
      console.error('Error configuring WhatsApp:', error);
    }
  };

  const handleSendWhatsAppMessage = async (message) => {
    try {
      await sendWhatsAppMessage(message);
      alert('Message sent successfully!');
    } catch (error) {
      console.error('Error sending WhatsApp message:', error);
    }
  };

  useEffect(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), [messages]);

  return (
    <div className="chat-layout">
      <div className="chat-sidebar">
        <ChatHistory history={history} onNewChat={handleNewChat} />
      </div>

      <div className="chat-main">
        <div className="chat-header">AppG Assistant</div>

        <div className="chat-body">
          {messages.map((msg, i) => (
            <div key={i} className={`chat-bubble ${msg.sender}`}>
              {msg.text}
            </div>
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
