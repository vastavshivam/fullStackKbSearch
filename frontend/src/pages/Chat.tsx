import React, { useState, useRef, useEffect } from 'react';
import ChatHistory from '../pages/ChatHistory';
import '../pages/Chat.css';

export default function Chat() {
  const [messages, setMessages] = useState([{ sender: 'bot', text: "Welcome to Bird AI! 🐦" }]);
  const [input, setInput] = useState('');
  const [history, setHistory] = useState<string[][]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const newMessages = [...messages, { sender: 'user', text: input }];
    setMessages(newMessages);
    setHistory(prev => [[input], ...prev]);
    setInput('');

    setTimeout(() => {
      setMessages(prev => [...prev, { sender: 'bot', text: "Let me get that for you..." }]);
    }, 1000);
  };

  const handleNewChat = () => {
    setMessages([{ sender: 'bot', text: "New chat started! 👋" }]);
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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
