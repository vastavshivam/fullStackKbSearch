import React, { useState, useRef, useEffect } from 'react';
import ChatHistory from '../pages/ChatHistory';
import '../pages/Chat.css';
import axios from 'axios';

/** ─────────── Custom type for what the server sends back ─────────── */
interface ChatResponse {
  answer: string;
}

export default function Chat() {
  const [messages, setMessages] = useState([{ sender: 'bot', text: "Welcome to FishAI! �" }]);
  const [input, setInput] = useState('');
  const [history, setHistory] = useState<string[][]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    setMessages(prev => [...prev, { sender: 'user', text: input }]);
    setHistory(prev => [[input], ...prev]);
    setInput('');
    setMessages(prev => [...prev, { sender: 'bot', text: "Let me get that for you..." }]);

    try {
      // 👇 tell axios what shape we expect
      const res = await axios.post<ChatResponse>('/api/qa/static-chat', { question: input });
      const answer = res.data.answer || "Sorry, I couldn't find an answer.";
      setMessages(prev => {
        const msgs = prev.slice(0, -1); // drop loading
        return [...msgs, { sender: 'bot', text: answer }];
      });
    } catch (err) {
      setMessages(prev => {
        const msgs = prev.slice(0, -1);
        return [...msgs, { sender: 'bot', text: "Sorry, there was an error getting the answer." }];
      });
    }
  };

  const handleNewChat = () => setMessages([{ sender: 'bot', text: "New chat started! 👋" }]);

  useEffect(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), [messages]);

  return (
    <div className="chat-layout">
      <div className="chat-sidebar">
        <ChatHistory history={history} onNewChat={handleNewChat} />
      </div>

      <div className="chat-main">
        <div className="chat-header">FishAI</div>

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
