// ModernWidgetDashboard.tsx - Modern Widget Management Platform
import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import './ModernWidgetDashboard.css';

interface Widget {
  client_id: string;
  domain: string;
  position: string;
  theme: string;
  primary_color: string;
  chat_title: string;
  welcome_message: string;
  connection_count: number;
  created_at: string;
  user_email: string;
}

const ModernWidgetDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user, token, logout } = useContext(AuthContext);
  const [widgets, setWidgets] = useState<Widget[]>([]);
  const [selectedWidget, setSelectedWidget] = useState<Widget | null>(null);
  const [activeSection, setActiveSection] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [analytics, setAnalytics] = useState<any>({});
  const [knowledgeBase, setKnowledgeBase] = useState<File | null>(null);

  const API_BASE = process.env.REACT_APP_API_URL || 'https://4tgzh3l5-8004.inc1.devtunnels.ms';

  // Helper function for authenticated API calls
  const getAuthHeaders = () => {
    const headers: any = { 'Content-Type': 'application/json' };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  };

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    fetchWidgets();
  }, [user, navigate]);

  const fetchWidgets = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/widget/list`, {
        headers: getAuthHeaders()
      });
      const data = await response.json();
      setWidgets(data.widgets || []);
      if (data.widgets && data.widgets.length > 0 && !selectedWidget) {
        setSelectedWidget(data.widgets[0]);
      }
    } catch (error) {
      console.error('Error fetching widgets:', error);
    } finally {
      setLoading(false);
    }
  };

  const createWidget = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/widget/generate`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      const data = await response.json();
      
      if (response.ok) {
        await fetchWidgets();
        alert(`Widget created successfully!\nClient ID: ${data.client_id}`);
      }
    } catch (error) {
      console.error('Error creating widget:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateWidgetConfig = async (config: any) => {
    if (!selectedWidget) return;
    
    try {
      const response = await fetch(`${API_BASE}/api/widget/config`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ ...config, client_id: selectedWidget.client_id })
      });
      
      if (response.ok) {
        await fetchWidgets();
        alert('Widget configuration updated successfully!');
      }
    } catch (error) {
      console.error('Error updating widget:', error);
    }
  };

  const uploadKnowledgeBase = async (file: File) => {
    if (!selectedWidget || !file) return;

    try {
      setLoading(true);
      const formData = new FormData();
      formData.append('files', file);

      const response = await fetch(`${API_BASE}/api/files/widget-kb/${selectedWidget.client_id}`, {
        method: 'POST',
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: formData
      });

      if (response.ok) {
        alert('Knowledge base uploaded successfully!');
        setKnowledgeBase(null);
      } else {
        alert('Failed to upload knowledge base');
      }
    } catch (error) {
      console.error('Error uploading knowledge base:', error);
      alert('Error uploading knowledge base');
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    if (!selectedWidget) return;

    try {
      const response = await fetch(`${API_BASE}/api/widget/analytics/detailed/${selectedWidget.client_id}`);
      const data = await response.json();
      setAnalytics(data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  useEffect(() => {
    if (selectedWidget && activeSection === 'analytics') {
      fetchAnalytics();
    }
  }, [selectedWidget, activeSection]);

  const sections = [
    { id: 'overview', name: 'Overview', icon: '🏠' },
    { id: 'widgets', name: 'Widget Management', icon: '⚙️' },
    { id: 'customization', name: 'Customization', icon: '🎨' },
    { id: 'knowledge', name: 'Knowledge Base', icon: '📚' },
    { id: 'analytics', name: 'Analytics', icon: '📊' },
    { id: 'integration', name: 'Integration', icon: '🔗' }
  ];

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
  };

  return (
    <div className="modern-dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <div className="header-left">
            <h1 className="dashboard-title">
              <span className="gradient-text">Widget Studio</span>
            </h1>
            <p className="dashboard-subtitle">
              Create, customize, and manage your AI-powered widgets
            </p>
          </div>
          <div className="header-right">
            <div className="user-info">
              <div className="user-avatar">
                {user?.email?.charAt(0).toUpperCase()}
              </div>
              <div className="user-details">
                <span className="user-name">{user?.email}</span>
                <span className="user-role">{user?.role || 'User'}</span>
              </div>
            </div>
            <button 
              onClick={logout}
              className="logout-btn"
              title="Logout"
            >
              <i className="icon">🚪</i>
            </button>
          </div>
        </div>
      </header>

      <div className="dashboard-container">
        {/* Sidebar Navigation */}
        <nav className="dashboard-sidebar">
          <div className="sidebar-content">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`sidebar-item ${activeSection === section.id ? 'active' : ''}`}
              >
                <span className="sidebar-icon">{section.icon}</span>
                <span className="sidebar-label">{section.name}</span>
              </button>
            ))}
          </div>
        </nav>

        {/* Main Content */}
        <main className="dashboard-main">
          {loading && (
            <div className="loading-overlay">
              <div className="loading-spinner"></div>
              <p>Loading...</p>
            </div>
          )}

          {/* Overview Section */}
          {activeSection === 'overview' && (
            <div className="section overview-section">
              <div className="section-header">
                <h2>Welcome to Widget Studio</h2>
                <p>Manage your AI-powered widgets with ease</p>
              </div>
              
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-icon">🎯</div>
                  <div className="stat-content">
                    <h3>{widgets.length}</h3>
                    <p>Active Widgets</p>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon">💬</div>
                  <div className="stat-content">
                    <h3>{analytics.total_conversations || 0}</h3>
                    <p>Total Conversations</p>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon">👥</div>
                  <div className="stat-content">
                    <h3>{analytics.active_users || 0}</h3>
                    <p>Active Users</p>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon">⚡</div>
                  <div className="stat-content">
                    <h3>99.9%</h3>
                    <p>Uptime</p>
                  </div>
                </div>
              </div>

              <div className="quick-actions">
                <h3>Quick Actions</h3>
                <div className="action-buttons">
                  <button 
                    onClick={createWidget}
                    className="action-btn primary"
                  >
                    <span className="btn-icon">➕</span>
                    Create New Widget
                  </button>
                  <button 
                    onClick={() => setActiveSection('customization')}
                    className="action-btn secondary"
                  >
                    <span className="btn-icon">🎨</span>
                    Customize Widgets
                  </button>
                  <button 
                    onClick={() => setActiveSection('analytics')}
                    className="action-btn secondary"
                  >
                    <span className="btn-icon">📊</span>
                    View Analytics
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Widget Management Section */}
          {activeSection === 'widgets' && (
            <div className="section widgets-section">
              <div className="section-header">
                <h2>Widget Management</h2>
                <button onClick={createWidget} className="create-widget-btn">
                  <span>➕</span> Create New Widget
                </button>
              </div>

              <div className="widgets-grid">
                {widgets.map((widget) => (
                  <div 
                    key={widget.client_id}
                    className={`widget-card ${selectedWidget?.client_id === widget.client_id ? 'selected' : ''}`}
                    onClick={() => setSelectedWidget(widget)}
                  >
                    <div className="widget-header">
                      <h3>{widget.chat_title}</h3>
                      <div className="widget-status">
                        <span className="status-dot active"></span>
                        <span>Active</span>
                      </div>
                    </div>
                    <div className="widget-info">
                      <p><strong>Domain:</strong> {widget.domain || 'Not set'}</p>
                      <p><strong>Position:</strong> {widget.position}</p>
                      <p><strong>Theme:</strong> {widget.theme}</p>
                      <p><strong>Connections:</strong> {widget.connection_count}</p>
                    </div>
                    <div className="widget-actions">
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          copyToClipboard(`<script async src="${API_BASE}/api/widget/script/${widget.client_id}"></script>`);
                        }}
                        className="action-btn-small"
                      >
                        📋 Copy Code
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Customization Section */}
          {activeSection === 'customization' && selectedWidget && (
            <div className="section customization-section">
              <div className="section-header">
                <h2>Customize Widget</h2>
                <p>Personalize the appearance and behavior of your widget</p>
              </div>

              <div className="customization-grid">
                <div className="customization-card">
                  <h3>Basic Settings</h3>
                  <div className="form-group">
                    <label>Chat Title</label>
                    <input 
                      type="text"
                      value={selectedWidget.chat_title}
                      onChange={(e) => updateWidgetConfig({ ...selectedWidget, chat_title: e.target.value })}
                      className="form-input"
                    />
                  </div>
                  <div className="form-group">
                    <label>Welcome Message</label>
                    <textarea 
                      value={selectedWidget.welcome_message}
                      onChange={(e) => updateWidgetConfig({ ...selectedWidget, welcome_message: e.target.value })}
                      className="form-textarea"
                      rows={3}
                    />
                  </div>
                  <div className="form-group">
                    <label>Domain</label>
                    <input 
                      type="text"
                      value={selectedWidget.domain}
                      onChange={(e) => updateWidgetConfig({ ...selectedWidget, domain: e.target.value })}
                      className="form-input"
                      placeholder="https://your-website.com"
                    />
                  </div>
                </div>

                <div className="customization-card">
                  <h3>Appearance</h3>
                  <div className="form-group">
                    <label>Primary Color</label>
                    <input 
                      type="color"
                      value={selectedWidget.primary_color}
                      onChange={(e) => updateWidgetConfig({ ...selectedWidget, primary_color: e.target.value })}
                      className="form-color"
                    />
                  </div>
                  <div className="form-group">
                    <label>Position</label>
                    <select 
                      value={selectedWidget.position}
                      onChange={(e) => updateWidgetConfig({ ...selectedWidget, position: e.target.value })}
                      className="form-select"
                    >
                      <option value="bottom-right">Bottom Right</option>
                      <option value="bottom-left">Bottom Left</option>
                      <option value="top-right">Top Right</option>
                      <option value="top-left">Top Left</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Theme</label>
                    <select 
                      value={selectedWidget.theme}
                      onChange={(e) => updateWidgetConfig({ ...selectedWidget, theme: e.target.value })}
                      className="form-select"
                    >
                      <option value="light">Light</option>
                      <option value="dark">Dark</option>
                      <option value="auto">Auto</option>
                    </select>
                  </div>
                </div>

                <div className="customization-card preview-card">
                  <h3>Preview</h3>
                  <div className="widget-preview">
                    <div 
                      className="preview-widget"
                      style={{ 
                        backgroundColor: selectedWidget.primary_color,
                        position: 'relative'
                      }}
                    >
                      <div className="preview-header">
                        {selectedWidget.chat_title}
                      </div>
                      <div className="preview-message">
                        {selectedWidget.welcome_message}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Knowledge Base Section */}
          {activeSection === 'knowledge' && (
            <div className="section knowledge-section">
              <div className="section-header">
                <h2>Knowledge Base</h2>
                <p>Upload files to train your AI assistant</p>
              </div>

              <div className="knowledge-upload">
                <div className="upload-area">
                  <input
                    type="file"
                    id="knowledge-file"
                    accept=".pdf,.txt,.docx,.csv,.json,.jsonl"
                    onChange={(e) => setKnowledgeBase(e.target.files?.[0] || null)}
                    className="file-input"
                    style={{ display: 'none' }}
                  />
                  <label htmlFor="knowledge-file" className="upload-label">
                    <div className="upload-icon">📁</div>
                    <h3>Upload Knowledge Base</h3>
                    <p>Drag and drop files or click to browse</p>
                    <p className="upload-formats">Supported: PDF, TXT, DOCX, CSV, JSON, JSONL</p>
                  </label>
                </div>

                {knowledgeBase && (
                  <div className="selected-file">
                    <div className="file-info">
                      <span className="file-name">{knowledgeBase.name}</span>
                      <span className="file-size">{(knowledgeBase.size / 1024 / 1024).toFixed(2)} MB</span>
                    </div>
                    <button 
                      onClick={() => uploadKnowledgeBase(knowledgeBase)}
                      className="upload-btn"
                      disabled={loading}
                    >
                      {loading ? 'Uploading...' : 'Upload'}
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Analytics Section */}
          {activeSection === 'analytics' && (
            <div className="section analytics-section">
              <div className="section-header">
                <h2>Analytics</h2>
                <p>Monitor your widget performance and user engagement</p>
              </div>

              <div className="analytics-grid">
                <div className="analytics-card">
                  <h3>Usage Statistics</h3>
                  <div className="stat-item">
                    <span>Total Messages:</span>
                    <span>{analytics.total_messages || 0}</span>
                  </div>
                  <div className="stat-item">
                    <span>Active Sessions:</span>
                    <span>{analytics.active_sessions || 0}</span>
                  </div>
                  <div className="stat-item">
                    <span>Response Time:</span>
                    <span>{analytics.avg_response_time || '0'}ms</span>
                  </div>
                </div>

                <div className="analytics-card">
                  <h3>User Engagement</h3>
                  <div className="stat-item">
                    <span>Active Users:</span>
                    <span>{analytics.active_users || 0}</span>
                  </div>
                  <div className="stat-item">
                    <span>Satisfaction:</span>
                    <span>{analytics.satisfaction_score || 'N/A'}</span>
                  </div>
                  <div className="stat-item">
                    <span>Conversion Rate:</span>
                    <span>{analytics.conversion_rate || '0'}%</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Integration Section */}
          {activeSection === 'integration' && selectedWidget && (
            <div className="section integration-section">
              <div className="section-header">
                <h2>Integration</h2>
                <p>Embed your widget on your website</p>
              </div>

              <div className="integration-steps">
                <div className="step">
                  <div className="step-number">1</div>
                  <div className="step-content">
                    <h3>Copy the embed code</h3>
                    <div className="code-block">
                      <code>{`<script async src="${API_BASE}/api/widget/script/${selectedWidget.client_id}"></script>`}</code>
                      <button 
                        onClick={() => copyToClipboard(`<script async src="${API_BASE}/api/widget/script/${selectedWidget.client_id}"></script>`)}
                        className="copy-btn"
                      >
                        📋 Copy
                      </button>
                    </div>
                  </div>
                </div>

                <div className="step">
                  <div className="step-number">2</div>
                  <div className="step-content">
                    <h3>Paste before closing &lt;/body&gt; tag</h3>
                    <p>Add the script tag to your website's HTML, just before the closing &lt;/body&gt; tag.</p>
                  </div>
                </div>

                <div className="step">
                  <div className="step-number">3</div>
                  <div className="step-content">
                    <h3>Your widget is live!</h3>
                    <p>The AI assistant widget will appear on your website and start helping your visitors.</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default ModernWidgetDashboard;
