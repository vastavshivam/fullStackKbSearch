import React, { useState, useEffect } from "react";
import ChatbotWidget from '../components/ChatWidget';

const UserDashboard = () => {
  const [analytics, setAnalytics] = useState<any>(null);
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  useEffect(() => {
    // Fetch analytics from backend
    fetch('http://localhost:8000/chat/analytics/1')
      .then(res => res.json())
      .then(data => setAnalytics(data));
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] || null);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user', '1'); // Replace with actual user id
    try {
      const res = await fetch('http://localhost:8000/kb/upload-knowledge-base', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      alert(data.message);
    } catch (err) {
      alert('Upload failed');
    }
    setUploading(false);
  };

  return (
    <div style={{ padding: 32 }}>
      <h1>User Dashboard</h1>
      <div style={{ marginBottom: 24 }}>
        <h2>Analytics</h2>
        {analytics ? (
          <pre>{JSON.stringify(analytics, null, 2)}</pre>
        ) : (
          <p>Loading analytics...</p>
        )}
      </div>
      <div style={{ marginBottom: 24 }}>
        <h2>Upload Knowledge Base</h2>
        <input type="file" onChange={handleFileChange} />
        <button onClick={handleUpload} disabled={uploading}>
          {uploading ? 'Uploading...' : 'Upload'}
        </button>
      </div>
      <ChatbotWidget />
    </div>
  );
};

export default UserDashboard; 