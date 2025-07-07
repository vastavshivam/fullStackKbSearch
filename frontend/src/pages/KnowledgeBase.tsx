import React, { useState, useEffect } from 'react';
import '../pages/KnowledgeBase.css';

type KBEntry = { question: string; answer: string };

const mockKB: KBEntry[] = [
  { question: 'How to reset my password?', answer: 'Click on Forgot Password on the login page.' },
  { question: 'How to contact support?', answer: 'Email us at support@example.com.' },
];


export default function KnowledgeBase() {
  const [entries, setEntries] = useState<KBEntry[]>(mockKB);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  useEffect(() => {
    console.log('KnowledgeBase.tsx component mounted');
  }, []);

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || !answer.trim()) return;
    setEntries([...entries, { question, answer }]);
    setQuestion('');
    setAnswer('');
  };


  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      setUploadStatus('Uploading...');
      try {
        const formData = new FormData();
        formData.append('file', file);

        // If you need to add auth, add headers here
        const response = await fetch('/api/kb/upload', {
          method: 'POST',
          body: formData,
          // credentials: 'include', // if using cookies for auth
        });
        if (!response.ok) {
          const err = await response.json();
          setUploadStatus('Upload failed: ' + (err.detail || response.statusText));
        } else {
          setUploadStatus('Upload successful!');
        }
      } catch (err: any) {
        setUploadStatus('Upload failed: ' + err.message);
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
