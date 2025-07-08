import React, { useState, useEffect } from 'react';
import '../pages/KnowledgeBase.css';

type KBEntry = { question: string; answer: string };

export default function KnowledgeBase() {
  const [entries, setEntries] = useState<KBEntry[]>([]);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  useEffect(() => {
    const fetchEntries = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/ask');
        const data = await res.json();
        if (res.ok) {
          setEntries(data); // assuming data is array of { question, answer }
        } else {
          console.error('Failed to load KB:', data.detail || res.statusText);
        }
      } catch (err: any) {
        console.error('Error loading KB:', err.message);
      }
    };

    fetchEntries();
  }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || !answer.trim()) return;

    try {
      const res = await fetch('http://localhost:8000/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, answer }),
      });

      const data = await res.json();
      if (res.ok) {
        setEntries(prev => [...prev, data]);
        setQuestion('');
        setAnswer('');
      } else {
        alert('❌ Failed to add entry: ' + (data.detail || res.statusText));
      }
    } catch (err: any) {
      alert('❌ Network error: ' + err.message);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      setUploadStatus('Uploading...');

      try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('http://localhost:8000/api/files', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const err = await response.json();
          setUploadStatus('Upload failed: ' + (err.detail || response.statusText));
        } else {
          setUploadStatus('✅ Upload successful!');
        }
      } catch (err: any) {
        setUploadStatus('❌ Upload failed: ' + err.message);
      }
    }
  };

  return (
    <div className="kb-layout">
      <h1 className="kb-title">📚 Knowledge Base</h1>

      <div className="kb-card upload-card">
        <h3>Upload Dataset</h3>
        <input type="file" onChange={handleFileUpload} />
        {uploadedFile && <p className="file-info">📂 Selected: {uploadedFile.name}</p>}
        {uploadStatus && <p className="file-info">{uploadStatus}</p>}
      </div>

      <div className="kb-card form-card">
        <h3>Manually Add Q&A</h3>
        <form onSubmit={handleAdd}>
          <label htmlFor="question">Question</label>
          <input
            id="question"
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Type your question..."
            required
          />

          <label htmlFor="answer">Answer</label>
          <textarea
            id="answer"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Type the answer..."
            rows={3}
            required
          />

          <button type="submit">➕ Add Entry</button>
        </form>
      </div>

      <div className="kb-card entries-card">
        <h3>Existing Entries</h3>
        {entries.length === 0 ? (
          <p className="file-info">No entries yet.</p>
        ) : (
          <ul>
            {entries.map((entry, index) => (
              <li key={index}>
                <strong>Q:</strong> {entry.question} <br />
                <strong>A:</strong> {entry.answer}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
