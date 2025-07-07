import React from 'react';
import { BarChart3, Table } from 'lucide-react';


interface ViewToggleProps {
  currentView: 'chart' | 'table';
  onToggle: () => void;
}

export default function ViewToggle({ currentView, onToggle }: ViewToggleProps) {
  return (
    <button className="toggle-view-btn" onClick={onToggle}>
      {currentView === 'chart' ? <Table size={16} /> : <BarChart3 size={16} />}
      {currentView === 'chart' ? 'Show Table' : 'Show Chart'}
    </button>
  );
}
