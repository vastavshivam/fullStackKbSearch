import React, { useState, useEffect } from 'react';
import ConfirmModal from '../components/ConfirmModal';
import { useWidgetConfig, WidgetFont, WidgetPosition } from '../components/WidgetConfigContext';
import { uploadFile } from '../services/api';

// Dashboard stats

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

const UserDashboard: React.FC = () => {
  const { config, setConfig } = useWidgetConfig();
  // State for tab switching
  const [activeTab, setActiveTab] = useState(0);
  // State for copy button
  const [copied, setCopied] = useState(false);

  // Installation instructions and script
  const installInstructions = [
    'Copy the installation script below.',
    'Paste it just before the </body> tag of your website.',
    'Save and deploy your website.',
    'The AI widget will appear on your site automatically.'
  ];
  const installScript = `<script src="https://cdn.example.com/ai-widget.js" data-api-key="YOUR_API_KEY"></script>`;

  // Copy script handler
  const handleCopy = () => {
    navigator.clipboard.writeText(installScript);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  // Dummy renderWidgetSettings and renderKnowledgeBase
  // Modern modular widget settings UI
  const [mascotFile, setMascotFile] = useState<File | null>(null);
  const [mascotPreview, setMascotPreview] = useState<string | null>(config.profileMascot);
  const handleMascotChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setMascotFile(file);
      const reader = new FileReader();
      reader.onload = ev => setMascotPreview(ev.target?.result as string);
      reader.readAsDataURL(file);
    }
  };
  const handleSaveConfig = () => {
    setConfig(cfg => ({
      ...cfg,
      profileMascot: mascotPreview,
    }));
  };
  const renderWidgetSettings = () => (
    <div style={{ padding: 32, borderRadius: 16, background: '#fff', boxShadow: '0 2px 8px #eee', maxWidth: 900, margin: '0 auto' }}>
      <h2 style={{ fontSize: 28, fontWeight: 800, marginBottom: 28, letterSpacing: -1 }}>Widget Settings</h2>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 32, alignItems: 'center', marginBottom: 32 }}>
        <div style={{ minWidth: 180 }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Widget Status</div>
          <button
            onClick={() => setConfig(cfg => ({ ...cfg, enabled: !cfg.enabled }))}
            style={{
              background: config.enabled ? '#22c55e' : '#ef4444',
              color: '#fff',
              border: 'none',
              borderRadius: 8,
              padding: '10px 22px',
              fontWeight: 700,
              fontSize: 16,
              cursor: 'pointer',
              marginBottom: 8,
              transition: 'background 0.2s',
              boxShadow: '0 2px 8px #eee',
            }}
          >
            {config.enabled ? 'Deactivate' : 'Activate'}
          </button>
        </div>
        <div style={{ minWidth: 180 }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Widget Color</div>
          <input
            type="color"
            value={config.widgetColor}
            onChange={e => setConfig(cfg => ({ ...cfg, widgetColor: e.target.value }))}
            style={{ width: 48, height: 48, border: 'none', borderRadius: 8, boxShadow: '0 2px 8px #eee', cursor: 'pointer' }}
          />
        </div>
        <div style={{ minWidth: 220 }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Widget Name</div>
          <input
            type="text"
            value={config.widgetName}
            onChange={e => setConfig(cfg => ({ ...cfg, widgetName: e.target.value }))}
            style={{ width: 160, padding: '10px 14px', borderRadius: 8, border: '1px solid #ddd', fontSize: 16, fontWeight: 500 }}
          />
        </div>
        <div style={{ minWidth: 180 }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Widget Font</div>
          <select
            value={config.widgetFont}
            onChange={e => setConfig(cfg => ({ ...cfg, widgetFont: e.target.value as WidgetFont }))}
            style={{ width: 140, padding: '10px 14px', borderRadius: 8, border: '1px solid #ddd', fontSize: 16, fontWeight: 500 }}
          >
            {['Inter','Roboto','Montserrat','Lato','Poppins','Open Sans','Nunito','Oswald','Raleway','Merriweather'].map(font => (
              <option key={font} value={font} style={{ fontFamily: font }}>{font}</option>
            ))}
          </select>
        </div>
        <div style={{ minWidth: 180 }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Widget Position</div>
          <select
            value={config.widgetPosition}
            onChange={e => setConfig(cfg => ({ ...cfg, widgetPosition: e.target.value as WidgetPosition }))}
            style={{ width: 140, padding: '10px 14px', borderRadius: 8, border: '1px solid #ddd', fontSize: 16, fontWeight: 500 }}
          >
            <option value="bottomRight">Bottom Right</option>
            <option value="bottomLeft">Bottom Left</option>
            <option value="topRight">Top Right</option>
            <option value="topLeft">Top Left</option>
          </select>
        </div>
        <div style={{ minWidth: 220 }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Profile Mascot (Upload Image)</div>
          <input type="file" accept="image/*" onChange={handleMascotChange} />
          {mascotPreview && (
            <img src={mascotPreview} alt="Mascot Preview" style={{ width: 48, height: 48, borderRadius: '50%', marginTop: 8, boxShadow: '0 2px 8px #eee' }} />
          )}
        </div>
      </div>
      <button
        onClick={handleSaveConfig}
        style={{ background: '#1976d2', color: '#fff', border: 'none', borderRadius: 8, padding: '14px 38px', fontWeight: 700, fontSize: 18, cursor: 'pointer', marginTop: 8, boxShadow: '0 2px 8px #eee', letterSpacing: 0.5 }}
      >
        Save Widget Configuration
      </button>
    </div>
  );
  const renderKnowledgeBase = () => (
    <div style={{ padding: 24 }}>
      <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 16 }}>Knowledge Base</h2>
      <div style={{ color: '#888' }}>Knowledge base content goes here.</div>
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