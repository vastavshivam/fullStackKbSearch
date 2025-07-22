import React from 'react';

interface ChatHistoryProps {
  history: {messages: any[], summary: string}[];
  onNewChat: () => void;
}

export default function ChatHistory({ history, onNewChat }: ChatHistoryProps) {
  return (
    <div className="chat-history">
      <button className="new-chat" onClick={onNewChat}>+ New Chat</button>
      <h4>History</h4>
      {history.length === 0 ? (
        <p className="no-history">No chats yet</p>
      ) : (
        <ul>
          {history.map((item, index) => (
            <li key={index}>{item.summary}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
