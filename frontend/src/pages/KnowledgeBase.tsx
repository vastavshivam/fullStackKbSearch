import React, { useState, useEffect } from 'react';
import { uploadFile, getKBEntries, createKBEntry, deleteKBEntry, updateKBEntry } from '../services/api';
import '../pages/KnowledgeBase.css';

<<<<<<< HEAD
type KBEntry = { 
  id: number;
  question: string; 
  answer: string;
  created_at?: string;
};
=======
type KBEntry = { question: string; answer: string };
>>>>>>> a7f144ce309495948fcfdbb83e555d79871546d4

export default function KnowledgeBase() {
  const [entries, setEntries] = useState<KBEntry[]>([]);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [editingEntry, setEditingEntry] = useState<KBEntry | null>(null);

  // Load KB entries on component mount
  useEffect(() => {
<<<<<<< HEAD
    loadKBEntries();
  }, []);

  const loadKBEntries = async () => {
    try {
      setLoading(true);
      const response = await getKBEntries();
      setEntries(response.data.entries);
    } catch (error) {
      console.error('Error loading KB entries:', error);
      setUploadStatus('Error loading entries');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || !answer.trim()) return;
    
    try {
      setLoading(true);
      if (editingEntry) {
        // Update existing entry
        await updateKBEntry(editingEntry.id, question, answer);
        setEditingEntry(null);
        setUploadStatus('Entry updated successfully!');
      } else {
        // Create new entry
        await createKBEntry(question, answer);
        setUploadStatus('Entry added successfully!');
      }
      
      setQuestion('');
      setAnswer('');
      await loadKBEntries(); // Refresh the list
    } catch (error) {
      console.error('Error saving entry:', error);
      setUploadStatus('Error saving entry');
    } finally {
      setLoading(false);
      setTimeout(() => setUploadStatus(null), 3000);
    }
  };

  const handleEdit = (entry: KBEntry) => {
    setEditingEntry(entry);
    setQuestion(entry.question);
    setAnswer(entry.answer);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this entry?')) return;
    
    try {
      setLoading(true);
      await deleteKBEntry(id);
      setUploadStatus('Entry deleted successfully!');
      await loadKBEntries(); // Refresh the list
    } catch (error) {
      console.error('Error deleting entry:', error);
      setUploadStatus('Error deleting entry');
    } finally {
      setLoading(false);
      setTimeout(() => setUploadStatus(null), 3000);
    }
  };

  const cancelEdit = () => {
    setEditingEntry(null);
    setQuestion('');
    setAnswer('');
  };

=======
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

>>>>>>> a7f144ce309495948fcfdbb83e555d79871546d4
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      setUploadStatus('Uploading...');

      try {
        const formData = new FormData();
        formData.append('file', file);

<<<<<<< HEAD
        const response = await uploadFile(formData);
        
        if (response.data) {
          setUploadStatus(`✅ ${response.data.message}`);
          // Refresh KB entries after successful upload
          await loadKBEntries();
        } else {
          setUploadStatus('Upload failed: Unknown error');
        }
      } catch (error: any) {
        console.error('Upload error:', error);
        const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
        setUploadStatus(`❌ Upload failed: ${errorMessage}`);
      } finally {
        setTimeout(() => setUploadStatus(null), 5000);
=======
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
>>>>>>> a7f144ce309495948fcfdbb83e555d79871546d4
      }
    }
  };

  return (
    <div className="kb-layout">
      <h1 className="kb-title">📚 Knowledge Base</h1>

<<<<<<< HEAD
      {uploadStatus && (
        <div className={`status-message ${uploadStatus.includes('❌') ? 'error' : 'success'}`}>
          {uploadStatus}
        </div>
      )}

=======
>>>>>>> a7f144ce309495948fcfdbb83e555d79871546d4
      <div className="kb-card upload-card">
        <h3>📤 Upload Dataset</h3>
        <p className="card-description">Upload CSV, JSON, TXT, PDF, or Excel files to automatically populate the knowledge base</p>
        <input 
          type="file" 
          onChange={handleFileUpload} 
          accept=".csv,.json,.xlsx,.txt,.pdf,.jpg,.jpeg,.png,.gif,.bmp"
          disabled={loading}
        />
        {uploadedFile && <p className="file-info">📂 Selected: {uploadedFile.name}</p>}
      </div>

      <div className="kb-card form-card">
        <h3>{editingEntry ? '✏️ Edit Q&A' : '➕ Manually Add Q&A'}</h3>
        <form onSubmit={handleAdd}>
          <label htmlFor="question">Question</label>
          <input
            id="question"
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Type your question..."
            required
            disabled={loading}
          />

          <label htmlFor="answer">Answer</label>
          <textarea
            id="answer"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Type the answer..."
            rows={3}
            required
            disabled={loading}
          />

          <div className="form-buttons">
            <button type="submit" disabled={loading || (!question.trim() || !answer.trim())}>
              {loading ? '⏳ Saving...' : editingEntry ? '💾 Update Entry' : '➕ Add Entry'}
            </button>
            {editingEntry && (
              <button type="button" onClick={cancelEdit} className="cancel-btn" disabled={loading}>
                ❌ Cancel
              </button>
            )}
          </div>
        </form>
      </div>

      <div className="kb-card entries-card">
        <h3>📋 Existing Entries ({entries.length})</h3>
        {loading && entries.length === 0 ? (
          <p className="file-info">⏳ Loading entries...</p>
        ) : entries.length === 0 ? (
          <p className="file-info">No entries yet. Add some Q&A pairs or upload a dataset!</p>
        ) : (
          <div className="entries-list">
            {entries.map((entry) => (
              <div key={entry.id} className="entry-item">
                <div className="entry-content">
                  <div className="entry-question">
                    <strong>Q:</strong> {entry.question}
                  </div>
                  <div className="entry-answer">
                    <strong>A:</strong> {entry.answer}
                  </div>
                  {entry.created_at && (
                    <div className="entry-date">
                      📅 Added: {new Date(entry.created_at).toLocaleDateString()}
                    </div>
                  )}
                </div>
                <div className="entry-actions">
                  <button 
                    onClick={() => handleEdit(entry)} 
                    className="edit-btn"
                    disabled={loading}
                    title="Edit entry"
                  >
                    ✏️
                  </button>
                  <button 
                    onClick={() => handleDelete(entry.id)} 
                    className="delete-btn"
                    disabled={loading}
                    title="Delete entry"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
