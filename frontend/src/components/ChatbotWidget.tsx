import React, { useState, useRef, useEffect } from 'react';
import './ChatWidget.css';

async function getLLMResponse(message: string): Promise<string> {
  try {
    const response = await fetch('/api/qa/static-chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: message })
    });
    if (!response.ok) throw new Error('Network response was not ok');
    const data = await response.json();
    return data.answer;
  } catch {
    return 'Sorry, I could not get a response from the server.';
  }
}

const ChatbotWidget = () => {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hi! I am BirdAI. How can I help you today?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open && bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [messages, open]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setMessages([...messages, { sender: 'user', text: input }]);
    const userInput = input;
    setInput('');
    setLoading(true);
    try {
      const botReply = await getLLMResponse(userInput);
      setMessages(msgs => [...msgs, { sender: 'bot', text: botReply }]);
    } catch (err) {
      setMessages(msgs => [...msgs, { sender: 'bot', text: 'Sorry, I could not get a response from the LLM.' }]);
    }
    setLoading(false);
  };

  return (
    <>
      <button className="chat-widget-fab" onClick={() => setOpen(o => !o)} aria-label="Open chat">
        <svg width="32" height="32" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="14" cy="14" r="14" fill="#fff" />
          <path d="M8 18V10C8 8.89543 8.89543 8 10 8H18C19.1046 8 20 8.89543 20 10V16C20 17.1046 19.1046 18 18 18H10L8 20V18Z" fill="#1da1f2" />
        </svg>
      </button>
      {open && (
        <div className="chat-widget-modal">
          <div className="chat-widget-header">
            BirdAI Chatbot
            <button style={{ background: 'none', border: 'none', color: '#fff', fontSize: 20, cursor: 'pointer' }} onClick={() => setOpen(false)}>&times;</button>
          </div>
          <div className="chat-widget-body" ref={bodyRef}>
            {messages.map((msg, idx) => (
              <div key={idx} className={`chat-widget-message ${msg.sender}`}>
                <div className="chat-widget-bubble">{msg.text}</div>
              </div>
            ))}
            {loading && (
              <div className="chat-widget-message bot">
                <div className="chat-widget-bubble">Thinking...</div>
              </div>
            )}
          </div>
          <form className="chat-widget-input" onSubmit={handleSend}>
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Type your message..."
              autoFocus
              disabled={loading}
            />
            <button type="submit" aria-label="Send" disabled={loading}>➤</button>
          </form>
        </div>
      )}
    </>
  );
};

export default ChatbotWidget; 