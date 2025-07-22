import React, { useState, useRef, useEffect } from 'react';
import './ChatWidget.css';
import { useWidgetConfig } from './WidgetConfigContext';


const initialMessages = [
  { sender: 'bot', text: 'Hi! I am AppG Assistant. How can I help you today?' }
];

const ChatWidget: React.FC = () => {

  const { config } = useWidgetConfig();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState('');
  const bodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) {
      const fetchHistory = async () => {
        try {
          const res = await fetch('/api/qa/static-chat/history', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: '123' }) // Replace with dynamic user ID
          });
          if (!res.ok) throw new Error('Failed to fetch history');
          const data = await res.json();
          setMessages(data.conversation_history || []);
        } catch (err) {
          console.error('Error fetching conversation history:', err);
        }
      };
      fetchHistory();
    }
  }, [open]);

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
    try {
      const res = await fetch('/api/qa/static-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userInput, user_id: '123' }) // Replace with dynamic user ID
      });
      if (!res.ok) throw new Error('Network response was not ok');
      const data = await res.json();
      setMessages(msgs => [...msgs, { sender: 'bot', text: data.answer || 'Sorry, I could not get a response from the server.' }]);
    } catch (err) {
      setMessages(msgs => [...msgs, { sender: 'bot', text: 'Sorry, I could not get a response from the server.' }]);
    }
  };

  return (
    <>
      <button
        className="chat-widget-fab"
        onClick={() => setOpen(o => !o)}
        aria-label="Open chat"
        style={{
          background: config.widgetColor,
          position: 'fixed',
          zIndex: 9999,
          ...(config.widgetPosition === 'bottomRight' ? { right: 32, bottom: 32 } : {}),
          ...(config.widgetPosition === 'bottomLeft' ? { left: 32, bottom: 32 } : {}),
          ...(config.widgetPosition === 'topRight' ? { right: 32, top: 32 } : {}),
          ...(config.widgetPosition === 'topLeft' ? { left: 32, top: 32 } : {}),
        }}
      >
        {config.profileMascot ? (
          <img src={config.profileMascot} alt="Mascot" style={{ width: 32, height: 32, borderRadius: '50%' }} />
        ) : (
          <svg width="32" height="32" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="14" cy="14" r="14" fill="#fff" />
            <path d="M8 18V10C8 8.89543 8.89543 8 10 8H18C19.1046 8 20 8.89543 20 10V16C20 17.1046 19.1046 18 18 18H10L8 20V18Z" fill={config.widgetColor} />
          </svg>
        )}
      </button>
      {open && (
        <div
          className="chat-widget-modal"
          style={{
            fontFamily: config.widgetFont,
            position: 'fixed',
            zIndex: 10000,
            width: 350,
            height: 480,
            background: '#fff',
            borderRadius: 16,
            boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            // Consistent offset for all corners
            ...(config.widgetPosition === 'bottomRight' ? { right: 32, bottom: 32 } : {}),
            ...(config.widgetPosition === 'bottomLeft' ? { left: 32, bottom: 32 } : {}),
            ...(config.widgetPosition === 'topRight' ? { right: 32, top: 32 } : {}),
            ...(config.widgetPosition === 'topLeft' ? { left: 32, top: 32 } : {}),
          }}
        >
          <div
            className="chat-widget-header"
            style={{ background: config.widgetColor }}
          >
            {config.profileMascot && (
              <img src={config.profileMascot} alt="Mascot" style={{ width: 32, height: 32, borderRadius: '50%', marginRight: 8 }} />
            )}
            {config.widgetName}
            <button style={{ background: 'none', border: 'none', color: '#fff', fontSize: 20, cursor: 'pointer', marginLeft: 'auto' }} onClick={() => setOpen(false)}>&times;</button>
          </div>
          <div className="chat-widget-body" ref={bodyRef}>
            {messages.map((msg, idx) => (
              <div key={idx} className={`chat-widget-message ${msg.sender}`}>
                <div className="chat-widget-bubble">{msg.text}</div>
              </div>
            ))}
          </div>
          <form className="chat-widget-input" onSubmit={handleSend}>
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Type your message..."
              autoFocus
              style={{ fontFamily: config.widgetFont }}
            />
            <button type="submit" aria-label="Send" style={{ background: config.widgetColor }}>
              ➤
            </button>
          </form>
        </div>
      )}
    </>
  );
};

export default ChatWidget;
