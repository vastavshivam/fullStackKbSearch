// components/ConfirmModal.tsx
import React from 'react';
import './ConfirmModal.css'; // Optional styling

type ConfirmModalProps = {
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
};

export default function ConfirmModal({ message, onConfirm, onCancel }: ConfirmModalProps) {
  return (
    <div className="confirm-modal-backdrop">
      <div className="confirm-modal">
        <p>{message}</p>
        <div className="modal-buttons">
          <button onClick={onConfirm} className="confirm-btn">✅ Yes</button>
          <button onClick={onCancel} className="cancel-btn">❌ Cancel</button>
        </div>
      </div>
    </div>
  );
}
