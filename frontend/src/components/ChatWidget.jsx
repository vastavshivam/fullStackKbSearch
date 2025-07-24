import React from 'react';

const ChatWidget = ({ messages }) => {
  return (
    <div className="chat-widget">
      {messages.map((msg, index) => (
        <div key={index} className={`message ${msg.sender}`}>
          {msg.text}
        </div>
      ))}
    </div>
  );
};

export default ChatWidget;
