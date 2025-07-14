import React, { useState, useEffect } from 'react';
import ConfirmModal from '../components/ConfirmModal';
import { uploadFile } from '../services/api';

// Dashboard stats
const stats = [
  { label: 'Total Messages', value: 0 },
  { label: 'Sessions', value: 0 },
  { label: 'Avg Response', value: '1.2s' },
  { label: 'Satisfaction', value: '4.2/5' },
];

const tabs = [
  'Widget Settings',
  'Knowledge Base',
  'Analytics',
  'Installation',
];

// --- Settings State ---
const defaultUserProfile = {
  name: 'John Doe',
  email: 'john.doe@birdcorp.com',
  phone: '+1 (555) 123-4567',
  role: 'Administrator',
  avatar: '/logo192.png'
};
const defaultNotifications = {
  emailNotifications: true,
  pushNotifications: true,
  smsNotifications: false,
  campaignUpdates: true,
  systemAlerts: true
};
const defaultSystemSettings = {
  theme: 'light',
  language: 'en',
  timezone: 'UTC-5',
  autoSave: true,
  dataRetention: 30
};
const defaultAIConfig = {
  geminiApiKey: '',
  openAiApiKey: '',
  autoApprovalLimit: 10000,
  aiResponseSpeed: 'fast',
  autoQuoteGeneration: true,
  smartPricing: true,
  apiProvider: 'openai',
  widgetColor: '#6A5ACD',
  widgetName: 'AI Assistant',
  greeting: 'Hello! How can I help you today?',
  profileMascot: '/mascot.png',
  widgetPosition: 'bottomRight',
  widgetFont: 'Inter',
  enabled: true
};

// --- Knowledge Base State ---
type KBEntry = {
  id: number;
  question: string;
  answer: string;
  created_at?: string;
};

type AIConfig = {
  geminiApiKey: string;
  openAiApiKey: string;
  autoApprovalLimit: number;
  aiResponseSpeed: string;
  autoQuoteGeneration: boolean;
  smartPricing: boolean;
  apiProvider: string;
  widgetColor: string;
  widgetName: string;
  greeting: string;
  profileMascot: string;
  widgetPosition: string;
  widgetFont: string;
  enabled: boolean;
};


const UserDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState(3); // Default to Installation tab
  const [copied, setCopied] = useState(false);

  // Settings states
  const [userProfile, setUserProfile] = useState(defaultUserProfile);
  const [notifications, setNotifications] = useState(defaultNotifications);
  const [systemSettings, setSystemSettings] = useState(defaultSystemSettings);
  const [aiConfigurations, setAiConfigurations] = useState(defaultAIConfig);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');

  // Knowledge base states
  const [entries, setEntries] = useState<KBEntry[]>([]);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [kbLoading, setKbLoading] = useState(false);
  const [editingEntry, setEditingEntry] = useState<KBEntry | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);

  // Simulate KB load
  useEffect(() => {
    if (activeTab === 1) {
      setKbLoading(true);
      setTimeout(() => {
        setEntries([
          { id: 1, question: 'How to reset my password?', answer: 'Go to settings > security > change password.', created_at: '2025-07-01' },
          { id: 2, question: 'How to install the widget?', answer: 'See the Installation tab for step-by-step instructions.', created_at: '2025-07-02' }
        ]);
        setKbLoading(false);
      }, 800);
    }
  }, [activeTab]);

  // Settings logic
  const handleSave = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setIsEditing(false);
      setSaveMessage('Settings saved successfully!');
      setTimeout(() => setSaveMessage(''), 3000);
    }, 1000);
  };
  const handleCancel = () => setIsEditing(false);

  // Knowledge base logic
  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || !answer.trim()) return;
    setKbLoading(true);
    setTimeout(() => {
      if (editingEntry) {
        setEntries(entries.map(entry => entry.id === editingEntry.id ? { ...entry, question, answer } : entry));
        setEditingEntry(null);
        setUploadStatus('Entry updated successfully!');
      } else {
        setEntries([...entries, { id: Date.now(), question, answer }]);
        setUploadStatus('Entry added successfully!');
      }
      setQuestion('');
      setAnswer('');
      setKbLoading(false);
      setTimeout(() => setUploadStatus(null), 3000);
    }, 800);
  };
  const handleEdit = (entry: KBEntry) => {
    setEditingEntry(entry);
    setQuestion(entry.question);
    setAnswer(entry.answer);
  };
  const handleDelete = (id: number) => {
    setKbLoading(true);
    setTimeout(() => {
      setEntries(entries.filter(entry => entry.id !== id));
      setUploadStatus('Entry deleted successfully!');
      setKbLoading(false);
      setConfirmDeleteId(null);
      setTimeout(() => setUploadStatus(null), 3000);
    }, 800);
  };
  const cancelEdit = () => {
    setEditingEntry(null);
    setQuestion('');
    setAnswer('');
  };

  // Installation tab logic
  const installInstructions = [
    'Enable the Widget: Toggle the "Enable Widget" switch in the Widget Settings tab to activate your chatbot.',
    'Copy the Installation Script: Use the Copy Script button below to copy the full installation code to your clipboard.',
    'Open Your Website’s HTML: In your website’s codebase, open the main HTML file (usually index.html or your main template file).',
    'Paste the Script: Paste the copied script just before the closing </body> tag of your HTML file. This ensures the chatbot loads after your page content.',
    'Save & Deploy: Save your changes and deploy your website. The chatbot widget will now appear on all pages where the script is included.',
    'Optional - Test the Widget: Visit your website and verify the chatbot appears in the selected position. You can further customize the widget settings from your dashboard at any time.',
    'Need Help? If you face any issues, contact support or refer to the documentation for troubleshooting tips.',
  ];
  const installScript = `<!-- AppDialog Chatbot Widget -->\n<script>\nwindow.AppDialogWidget = {\n  "enabled": true,\n  "name": "AI Assistant",\n  "greeting": "Hello! How can I help you today?",\n  "color": "#8ad2f0",\n  "position": "bottom-right",\n  "font": "Inter",\n  "mascot": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",\n  "hasKnowledgeBase": true,\n};\n</script>\n<script src=\"https://cdn.jsdelivr.net/gh/maheshghilall/cdnlinks/mistral_finetune_data.js\"></script>\n<script src=\"https://cdn.jsdelivr.net/gh/maheshghilall/cdnlinks/widget.js\"></script>`;
  const handleCopy = () => {
    navigator.clipboard.writeText(installScript);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // File upload handler
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      setUploadStatus('Uploading...');
      setKbLoading(true);
      try {
        const formData = new FormData();
        formData.append('file', file);
        const response = await uploadFile(formData);
        if (response.data) {
          setUploadStatus(`✅ ${response.data.message}`);
        } else {
          setUploadStatus('Upload failed: Unknown error');
        }
      } catch (error: any) {
        console.error('Upload error:', error);
        const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
        setUploadStatus(`❌ Upload failed: ${errorMessage}`);
      } finally {
        setKbLoading(false);
        setTimeout(() => setUploadStatus(null), 5000);
      }
    }
  };

  // Tab content renderers
  const renderWidgetSettings = () => (
    <div style={{ background: '#fff', borderRadius: 16, boxShadow: '0 2px 8px #eee', padding: 32, marginBottom: 32, maxWidth: 1200, marginLeft: 'auto', marginRight: 'auto' }}>
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24, display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ fontSize: 22, marginRight: 8 }}>⚙️</span> Widget Configuration
      </h2>
      <div style={{ display: 'flex', alignItems: 'center', gap: 24, marginBottom: 24 }}>
        <div style={{ fontWeight: 600, fontSize: 18 }}>Enable Widget</div>
        <span style={{ color: '#888' }}>Turn your chatbot widget on or off</span>
        <label style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
          <input type="checkbox" checked={aiConfigurations.enabled ?? true} onChange={e => setAiConfigurations(prev => ({ ...prev, enabled: e.target.checked }))} style={{ width: 32, height: 32 }} />
        </label>
      </div>
      <hr style={{ margin: '24px 0', border: 'none', borderTop: '1px solid #eee' }} />
      <form style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 32 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <label style={{ fontWeight: 500 }}>Bot Name
            <input type="text" value={aiConfigurations.widgetName} onChange={e => setAiConfigurations(prev => ({ ...prev, widgetName: e.target.value }))} style={{ width: '100%', marginTop: 6, padding: 10, borderRadius: 8, border: '1px solid #e0e0e0', fontSize: 16 }} />
          </label>
          <label style={{ fontWeight: 500 }}>Greeting Message
            <textarea value={aiConfigurations.greeting ?? 'Hello! How can I help you today?'} onChange={e => setAiConfigurations(prev => ({ ...prev, greeting: e.target.value }))} style={{ width: '100%', marginTop: 6, padding: 10, borderRadius: 8, border: '1px solid #e0e0e0', fontSize: 16, resize: 'vertical', minHeight: 48 }} />
          </label>
          <label style={{ fontWeight: 500 }}>Theme Color
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 6 }}>
              <input type="color" value={aiConfigurations.widgetColor} onChange={e => setAiConfigurations(prev => ({ ...prev, widgetColor: e.target.value }))} style={{ width: 40, height: 40, border: 'none', borderRadius: 8 }} />
              <input type="text" value={aiConfigurations.widgetColor} onChange={e => setAiConfigurations(prev => ({ ...prev, widgetColor: e.target.value }))} style={{ width: 120, padding: 8, borderRadius: 8, border: '1px solid #e0e0e0', fontSize: 16 }} />
            </div>
          </label>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <label style={{ fontWeight: 500 }}>Position
            <select value={aiConfigurations.widgetPosition} onChange={e => setAiConfigurations(prev => ({ ...prev, widgetPosition: e.target.value }))} style={{ width: '100%', marginTop: 6, padding: 10, borderRadius: 8, border: '1px solid #e0e0e0', fontSize: 16 }}>
              <option value="bottomRight">Bottom Right</option>
              <option value="bottomLeft">Bottom Left</option>
              <option value="topRight">Top Right</option>
              <option value="topLeft">Top Left</option>
            </select>
          </label>
          <label style={{ fontWeight: 500 }}>Font Family
            <select value={aiConfigurations.widgetFont} onChange={e => setAiConfigurations(prev => ({ ...prev, widgetFont: e.target.value }))} style={{ width: '100%', marginTop: 6, padding: 10, borderRadius: 8, border: '1px solid #e0e0e0', fontSize: 16 }}>
              <option value="Inter">Inter</option>
              <option value="Arial">Arial</option>
              <option value="Roboto">Roboto</option>
              <option value="Open Sans">Open Sans</option>
            </select>
          </label>
          <label style={{ fontWeight: 500 }}>Mascot (Upload Image)
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 6 }}>
              <input type="file" id="mascot-upload" style={{ display: 'none' }} onChange={e => {
                if (e.target.files && e.target.files[0]) {
                  setAiConfigurations(prev => ({ ...prev, profileMascot: URL.createObjectURL(e.target.files[0]) }));
                }
              }} />
              <label htmlFor="mascot-upload" style={{ background: '#e3f2fd', color: '#1976d2', borderRadius: 6, padding: '8px 16px', cursor: 'pointer', fontWeight: 600 }}>Choose File</label>
              <span style={{ color: '#888' }}>{aiConfigurations.profileMascot ? 'File chosen' : 'No file chosen'}</span>
              {aiConfigurations.profileMascot && (
                <img src={aiConfigurations.profileMascot} alt="mascot" style={{ width: 40, height: 40, borderRadius: '50%', objectFit: 'cover', border: '1px solid #eee' }} />
              )}
            </div>
          </label>
        </div>
      </form>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 32 }}>
        <button onClick={handleSave} style={{ background: '#1976d2', color: '#fff', border: 'none', borderRadius: 8, padding: '12px 32px', fontWeight: 600, fontSize: 18, boxShadow: '0 2px 8px #e3f2fd', cursor: 'pointer' }} disabled={loading}>
          {loading ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
      {saveMessage && <div style={{ marginTop: 16, color: '#1976d2', fontWeight: 600 }}>{saveMessage}</div>}
    </div>
  );

  const renderKnowledgeBase = () => (
    <div style={{ background: '#fff', borderRadius: 12, boxShadow: '0 2px 8px #eee', padding: 32, marginBottom: 32 }}>
      <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 16 }}>Knowledge Base Management</h2>
      <div style={{ border: '2px dashed #ddd', borderRadius: 12, padding: 32, textAlign: 'center', marginBottom: 32 }}>
        <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>Upload Any Data File</h3>
        <p style={{ color: '#6b7280', marginBottom: 16 }}>
          Upload any file format - PDF, Excel, Word, CSV, JSON, TXT, and more!<br />
          Our AI will automatically extract and structure the data for your chatbot.
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <i className="bi bi-file-earmark-pdf" style={{ fontSize: 24, color: '#d32f2f' }}></i>
            <span>PDF</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <i className="bi bi-file-earmark-excel" style={{ fontSize: 24, color: '#388e3c' }}></i>
            <span>Excel</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <i className="bi bi-file-earmark-word" style={{ fontSize: 24, color: '#1976d2' }}></i>
            <span>Word</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <i className="bi bi-filetype-csv" style={{ fontSize: 24, color: '#fbc02d' }}></i>
            <span>CSV</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <i className="bi bi-file-earmark-code" style={{ fontSize: 24, color: '#6a1b9a' }}></i>
            <span>JSON</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <i className="bi bi-file-earmark-text" style={{ fontSize: 24, color: '#616161' }}></i>
            <span>TXT</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <i className="bi bi-file-earmark-image" style={{ fontSize: 24, color: '#0288d1' }}></i>
            <span>Images</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <i className="bi bi-plus-circle" style={{ fontSize: 24, color: '#757575' }}></i>
            <span>More</span>
          </div>
        </div>
        <input
          type="file"
          id="kb-file-upload"
          style={{ display: 'none' }}
          onChange={handleFileUpload}
          accept=".csv,.json,.xlsx,.txt,.pdf,.jpg,.jpeg,.png,.gif,.bmp"
          disabled={kbLoading}
        />
        <label htmlFor="kb-file-upload">
          <button
            style={{ background: '#1976d2', color: '#fff', border: 'none', borderRadius: 8, padding: '12px 32px', fontWeight: 600, cursor: kbLoading ? 'not-allowed' : 'pointer' }}
            disabled={kbLoading}
          >
            {kbLoading ? 'Uploading...' : 'Select File to Upload'}
          </button>
        </label>
        {uploadedFile && <p style={{ marginTop: 8 }}>Selected: {uploadedFile.name}</p>}
        <p style={{ color: '#6b7280', marginTop: 16 }}>
          Max file size: 50MB • All formats supported • Data is processed securely
        </p>
      </div>
      {uploadStatus && (
        <div style={{ color: uploadStatus.includes('❌') ? '#f44336' : '#1976d2', marginBottom: 16 }}>{uploadStatus}</div>
      )}
      <div style={{ marginBottom: 24 }}>
        <h3>{editingEntry ? 'Edit Q&A' : 'Manually Add Q&A'}</h3>
        <form onSubmit={handleAdd} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <input type="text" value={question} onChange={e => setQuestion(e.target.value)} placeholder="Type your question..." required disabled={kbLoading} />
          <textarea value={answer} onChange={e => setAnswer(e.target.value)} placeholder="Type the answer..." rows={3} required disabled={kbLoading} />
          <div style={{ display: 'flex', gap: 8 }}>
            <button type="submit" disabled={kbLoading || !question.trim() || !answer.trim()}>{kbLoading ? 'Saving...' : editingEntry ? 'Update Entry' : 'Add Entry'}</button>
            {editingEntry && <button type="button" onClick={cancelEdit} disabled={kbLoading}>Cancel</button>}
          </div>
        </form>
      </div>
      <div>
        <h3>Existing Entries ({entries.length})</h3>
        {kbLoading && entries.length === 0 ? (
          <p>Loading entries...</p>
        ) : entries.length === 0 ? (
          <p>No entries yet. Add some Q&A pairs or upload a dataset!</p>
        ) : (
          <div>
            {entries.map(entry => (
              <div key={entry.id} style={{ border: '1px solid #eee', borderRadius: 8, padding: 12, marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div><strong>Q:</strong> {entry.question}</div>
                  <div><strong>A:</strong> {entry.answer}</div>
                  {entry.created_at && <div style={{ color: '#888', fontSize: 12 }}>Added: {new Date(entry.created_at).toLocaleDateString()}</div>}
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button onClick={() => handleEdit(entry)} disabled={kbLoading}>Edit</button>
                  <button onClick={() => setConfirmDeleteId(entry.id)} disabled={kbLoading}>Delete</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      {confirmDeleteId !== null && (
        <ConfirmModal
          message="Are you sure you want to delete this entry?"
          onConfirm={() => handleDelete(confirmDeleteId)}
          onCancel={() => setConfirmDeleteId(null)}
        />
      )}
    </div>
  );

  const renderAnalytics = () => (
    <div style={{ background: '#fff', borderRadius: 12, boxShadow: '0 2px 8px #eee', padding: 32, marginBottom: 32, maxWidth: 900, marginLeft: 'auto', marginRight: 'auto' }}>
      <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 16 }}>Analytics</h2>
      <div style={{ display: 'flex', gap: 32, marginBottom: 32 }}>
        <div style={{ flex: 1, background: '#f7f8fa', borderRadius: 8, padding: 24, textAlign: 'center' }}>
          <div style={{ fontSize: 18, color: '#1976d2', marginBottom: 8 }}>Total Messages</div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>0</div>
        </div>
        <div style={{ flex: 1, background: '#f7f8fa', borderRadius: 8, padding: 24, textAlign: 'center' }}>
          <div style={{ fontSize: 18, color: '#388e3c', marginBottom: 8 }}>Sessions</div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>0</div>
        </div>
        <div style={{ flex: 1, background: '#f7f8fa', borderRadius: 8, padding: 24, textAlign: 'center' }}>
          <div style={{ fontSize: 18, color: '#f57c00', marginBottom: 8 }}>Avg Response</div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>1.2s</div>
        </div>
        <div style={{ flex: 1, background: '#f7f8fa', borderRadius: 8, padding: 24, textAlign: 'center' }}>
          <div style={{ fontSize: 18, color: '#8e24aa', marginBottom: 8 }}>Satisfaction</div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>4.2/5</div>
        </div>
      </div>
      <div style={{ marginBottom: 32 }}>
        <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>Message Activity (Last 7 Days)</h3>
        <div style={{ width: '100%', height: 220, background: '#f7f8fa', borderRadius: 8, display: 'flex', alignItems: 'flex-end', gap: 12, padding: '24px 16px' }}>
          {[2, 4, 1, 5, 3, 6, 2].map((val, idx) => (
            <div key={idx} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div style={{ height: val * 25, width: 24, background: '#1976d2', borderRadius: 6, marginBottom: 8 }}></div>
              <span style={{ fontSize: 14, color: '#888' }}>{['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][idx]}</span>
            </div>
          ))}
        </div>
      </div>
      <div>
        <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>Recent Sessions</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', background: '#fff', borderRadius: 8, overflow: 'hidden' }}>
          <thead>
            <tr style={{ background: '#f7f8fa', color: '#1976d2', fontWeight: 600 }}>
              <th style={{ padding: '12px 8px', textAlign: 'left' }}>Session ID</th>
              <th style={{ padding: '12px 8px', textAlign: 'left' }}>User</th>
              <th style={{ padding: '12px 8px', textAlign: 'left' }}>Messages</th>
              <th style={{ padding: '12px 8px', textAlign: 'left' }}>Satisfaction</th>
              <th style={{ padding: '12px 8px', textAlign: 'left' }}>Date</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={{ padding: '12px 8px' }}>#1001</td>
              <td style={{ padding: '12px 8px' }}>John Doe</td>
              <td style={{ padding: '12px 8px' }}>5</td>
              <td style={{ padding: '12px 8px' }}>4/5</td>
              <td style={{ padding: '12px 8px' }}>2025-07-10</td>
            </tr>
            <tr>
              <td style={{ padding: '12px 8px' }}>#1002</td>
              <td style={{ padding: '12px 8px' }}>Jane Smith</td>
              <td style={{ padding: '12px 8px' }}>3</td>
              <td style={{ padding: '12px 8px' }}>5/5</td>
              <td style={{ padding: '12px 8px' }}>2025-07-09</td>
            </tr>
            <tr>
              <td style={{ padding: '12px 8px' }}>#1003</td>
              <td style={{ padding: '12px 8px' }}>Alex Lee</td>
              <td style={{ padding: '12px 8px' }}>2</td>
              <td style={{ padding: '12px 8px' }}>3/5</td>
              <td style={{ padding: '12px 8px' }}>2025-07-08</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderInstallation = () => (
    <div style={{ background: '#fff', borderRadius: 12, boxShadow: '0 2px 8px #eee', padding: 32, marginBottom: 32 }}>
      <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 16 }}>Install Widget</h2>
      <div style={{ background: '#f7f8fa', borderRadius: 8, padding: 24, marginBottom: 24 }}>
        <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12 }}>Installation Instructions</h3>
        <div style={{ color: '#333', fontSize: 16, marginBottom: 16 }}>
          <b>Step-by-Step Installation Guide</b>
          <ol style={{ margin: '12px 0 0 20px', padding: 0 }}>
            {installInstructions.map((step, idx) => (
              <li key={idx} style={{ marginBottom: 8 }}>{step}</li>
            ))}
          </ol>
          <div style={{ color: '#6b7280', fontSize: 14, marginTop: 16 }}>
            Note: You can install the widget on any website platform (HTML, WordPress, Shopify, React, etc.) by following these steps. For advanced integration, see the developer documentation.
          </div>
        </div>
        <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12 }}>Installation Script</h3>
        <div style={{ background: '#fff', borderRadius: 8, padding: 16, fontFamily: 'monospace', fontSize: 14, color: '#333', marginBottom: 16, overflowX: 'auto' }}>
          <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{installScript}</pre>
        </div>
        <button onClick={handleCopy} style={{ background: '#1976d2', color: '#fff', border: 'none', borderRadius: 6, padding: '8px 16px', cursor: 'pointer', fontWeight: 600 }}>
          {copied ? 'Copied!' : 'Copy Script'}
        </button>
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 0:
        return renderWidgetSettings();
      case 1:
        return renderKnowledgeBase();
      case 2:
        return renderAnalytics();
      case 3:
        return renderInstallation();
      default:
        return null;
    }
  };

  return (
    <div style={{ background: '#f7f8fa', minHeight: '100vh', padding: '24px' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        <h1 style={{ fontSize: 32, fontWeight: 700, marginBottom: 16 }}>Chatbot Dashboard</h1>
        <p style={{ color: '#6b7280', marginBottom: 32 }}>Configure and monitor your AI assistant</p>
        <div style={{ display: 'flex', gap: 16, marginBottom: 32 }}>
          {stats.map((stat, idx) => (
            <div key={idx} style={{ flex: 1, background: '#fff', borderRadius: 12, boxShadow: '0 2px 8px #eee', padding: 24, textAlign: 'center' }}>
              <div style={{ fontSize: 18, color: '#6b7280', marginBottom: 8 }}>{stat.label}</div>
              <div style={{ fontSize: 28, fontWeight: 700 }}>{stat.value}</div>
            </div>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
          {tabs.map((tab, idx) => (
            <button
              key={tab}
              onClick={() => setActiveTab(idx)}
              style={{
                background: activeTab === idx ? '#1976d2' : '#fff',
                color: activeTab === idx ? '#fff' : '#333',
                border: '1px solid #ddd',
                borderRadius: 8,
                padding: '12px 24px',
                fontWeight: 600,
                cursor: 'pointer',
                fontSize: 16,
              }}
            >
              {tab}
            </button>
          ))}
        </div>
        <div style={{ background: '#fff', borderRadius: 12, boxShadow: '0 2px 8px #eee', padding: 24 }}>
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
};

export default UserDashboard;