import React, { useState, useRef, useEffect } from 'react';
import ChatHistory from './ChatHistory';
import '../pages/Chat.css';

type Message = {
  sender: 'user' | 'bot';
  text: string;
};

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    { sender: 'bot', text: "Welcome to Bird AI! 🐦" }
  ]);
  const [input, setInput] = useState('');
  const [history, setHistory] = useState<string[][]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const ws = useRef<WebSocket | null>(null);

  // Open WebSocket connection
  useEffect(() => {
    ws.current = new WebSocket('ws://localhost:8000/ws/chat');

    ws.current.onopen = () => {
      console.log('✅ WebSocket connected');
    };

    ws.current.onmessage = (e: MessageEvent) => {
      setMessages(prev => [...prev, { sender: 'bot', text: e.data }]);
    };

    ws.current.onerror = (e) => {
      console.error("WebSocket error:", e);
    };

    ws.current.onclose = () => {
      console.log('❌ WebSocket disconnected');
    };

    return () => {
      ws.current?.close();
    };
  }, []);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Send to WebSocket server
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(input);
    }

    const newMessages = [...messages, { sender: 'user', text: input }];
    setMessages(newMessages);
    setHistory(prev => [[input], ...prev]);
    setInput('');
  };

  const handleNewChat = () => {
    setMessages([{ sender: 'bot', text: "New chat started! 👋" }]);
  };

  return (
    <div className="chat-layout">
      <div className="chat-sidebar">
        <ChatHistory history={history} onNewChat={handleNewChat} />
      </div>

      <div className="chat-main">
        <div className="chat-header">Bird AI</div>

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
