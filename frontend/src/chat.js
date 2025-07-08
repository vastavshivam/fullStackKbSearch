// src/Chat.js
import React, { useEffect, useRef, useState } from "react";

function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const ws = useRef(null);

  useEffect(() => {
    ws.current = new WebSocket("ws://localhost:8000/ws/chat");

    ws.current.onmessage = (e) => {
      setMessages((prev) => [...prev, { sender: "bot", text: e.data }]);
    };

    ws.current.onopen = () => {
      console.log("✅ WebSocket connected");
    };

    return () => ws.current.close();
  }, []);

  const send = () => {
    ws.current.send(input);
    setMessages((prev) => [...prev, { sender: "user", text: input }]);
    setInput("");
  };

  return (
    <div>
      <h2>WebSocket Chat</h2>
      <div style={{ border: "1px solid #ccc", padding: 10 }}>
        {messages.map((m, i) => (
          <p key={i}>
            <b>{m.sender}:</b> {m.text}
          </p>
        ))}
      </div>
      <input value={input} onChange={(e) => setInput(e.target.value)} />
      <button onClick={send}>Send</button>
    </div>
  );
}

export default Chat;
