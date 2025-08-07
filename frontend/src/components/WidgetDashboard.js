import React, { useState, useEffect, useContext, useRef } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import './WidgetDashboard.css';

const WidgetDashboard = () => {
  const { user, token } = useContext(AuthContext);
  const [widgets, setWidgets] = useState([]);
  const [selectedWidget, setSelectedWidget] = useState(null);
  const [analytics, setAnalytics] = useState({});
  const [ws, setWs] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isLightMode, setIsLightMode] = useState(false);
  const [showThemeNotification, setShowThemeNotification] = useState(false);
  const themeToggleRef = useRef(null);

  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8004';

  // Theme management
  useEffect(() => {
    // Load saved theme preference
    const savedTheme = localStorage.getItem('widgetDashboardTheme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    setIsLightMode(savedTheme === 'light' || (!savedTheme && !prefersDark));

    // Add keyboard shortcut for theme toggle (Ctrl/Cmd + Shift + T)
    const handleKeyboardShortcut = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
        e.preventDefault();
        toggleTheme();
      }
    };

    document.addEventListener('keydown', handleKeyboardShortcut);
    return () => document.removeEventListener('keydown', handleKeyboardShortcut);
  }, []);

  useEffect(() => {
    // Apply theme to widget dashboard
    const widgetDashboard = document.querySelector('.widget-dashboard');
    if (widgetDashboard) {
      if (isLightMode) {
        widgetDashboard.classList.add('light-mode');
      } else {
        widgetDashboard.classList.remove('light-mode');
      }
    }
    
    // Save theme preference
    localStorage.setItem('widgetDashboardTheme', isLightMode ? 'light' : 'dark');
  }, [isLightMode]);

  const toggleTheme = () => {
    const newTheme = !isLightMode;
    setIsLightMode(newTheme);
    
    // Show notification
    setShowThemeNotification(true);
    setTimeout(() => setShowThemeNotification(false), 2000);
    
    // Add animation effect to toggle button
    if (themeToggleRef.current) {
      themeToggleRef.current.classList.add('toggle-active');
      setTimeout(() => {
        themeToggleRef.current?.classList.remove('toggle-active');
      }, 800);
    }

    // Add theme switch effect to entire dashboard
    const widgetDashboard = document.querySelector('.widget-dashboard');
    if (widgetDashboard) {
      widgetDashboard.style.transform = 'scale(0.98)';
      setTimeout(() => {
        widgetDashboard.style.transform = 'scale(1)';
      }, 200);
    }
  };

  // Helper function for authenticated API calls
  const getAuthHeaders = () => {
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  };

  useEffect(() => {
    fetchWidgets();
    connectWebSocket();
    
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    const wsUrl = API_BASE.replace('http', 'ws') + '/api/widget/ws/dashboard';
    const websocket = new WebSocket(wsUrl);
    
    websocket.onopen = () => {
      console.log('Dashboard WebSocket connected');
      setIsConnected(true);
    };
    
    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'analytics_update') {
        updateAnalytics(message.data);
      }
    };
    
    websocket.onclose = () => {
      console.log('Dashboard WebSocket disconnected');
      setIsConnected(false);
      
      // Reconnect after 3 seconds
      setTimeout(connectWebSocket, 3000);
    };
    
    setWs(websocket);
  };

  const fetchWidgets = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/widget/list`, {
        headers: getAuthHeaders()
      });
      const data = await response.json();
      setWidgets(data.widgets || []);
    } catch (error) {
      console.error('Error fetching widgets:', error);
    }
  };

  const createWidget = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/widget/generate`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      const data = await response.json();
      
      if (response.ok) {
        await fetchWidgets();
        alert(`Widget created! Client ID: ${data.client_id}\nUser: ${data.user_email}`);
      }
    } catch (error) {
      console.error('Error creating widget:', error);
    }
  };

  const updateWidgetConfig = async (clientId, config) => {
    try {
      const response = await fetch(`${API_BASE}/api/widget/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...config, client_id: clientId })
      });
      
      if (response.ok) {
        alert('Widget configuration updated and pushed live!');
      }
    } catch (error) {
      console.error('Error updating widget:', error);
    }
  };

  const fetchAnalytics = async (clientId) => {
    try {
      const response = await fetch(`${API_BASE}/api/widget/analytics/detailed/${clientId}`);
      const data = await response.json();
      setAnalytics({ ...analytics, [clientId]: data });
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  const updateAnalytics = (eventData) => {
    const clientId = eventData.client_id;
    setAnalytics(prev => ({
      ...prev,
      [clientId]: {
        ...prev[clientId],
        recent_events: [
          ...(prev[clientId]?.recent_events || []).slice(-19),
          eventData
        ]
      }
    }));
  };

  const uploadKnowledgeBase = async (clientId, files) => {
    const formData = new FormData();
    Array.from(files).forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await fetch(`${API_BASE}/api/files/widget/upload/${clientId}`, {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        alert('Knowledge base updated and pushed live to all widgets!');
      } else {
        const errorData = await response.text();
        console.error('Upload failed:', errorData);
        alert('Failed to upload knowledge base. Check console for details.');
      }
    } catch (error) {
      console.error('Error uploading knowledge base:', error);
      alert('Error uploading knowledge base: ' + error.message);
    }
  };

  const toggleWidgetStatus = async (clientId, currentStatus) => {
    try {
      const newStatus = !currentStatus;
      const response = await fetch(`${API_BASE}/api/widget/toggle/${clientId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: newStatus })
      });
      
      if (response.ok) {
        // Update the widgets list locally
        setWidgets(widgets.map(widget => 
          widget.client_id === clientId 
            ? { ...widget, is_active: newStatus }
            : widget
        ));
        
        // Update selected widget if it's the current one
        if (selectedWidget?.client_id === clientId) {
          setSelectedWidget({ ...selectedWidget, is_active: newStatus });
        }
        
        alert(`Widget ${newStatus ? 'activated' : 'deactivated'} successfully!`);
      }
    } catch (error) {
      console.error('Error toggling widget status:', error);
      alert('Failed to toggle widget status');
    }
  };

  return (
    <div className={`widget-dashboard ${isLightMode ? 'light-mode' : ''}`}>
      {/* Theme Toggle Button */}
      <button 
        ref={themeToggleRef}
        onClick={toggleTheme} 
        className="theme-toggle"
        title={`Switch to ${isLightMode ? 'Dark' : 'Light'} Mode (Ctrl+Shift+T)`}
      >
        <i className={`fas ${isLightMode ? 'fa-moon' : 'fa-sun'}`}></i>
        {isLightMode ? 'Dark Mode' : 'Light Mode'}
      </button>

      {/* Theme Change Notification */}
      {showThemeNotification && (
        <div className="theme-notification">
          <i className={`fas ${isLightMode ? 'fa-sun' : 'fa-moon'}`}></i>
          Switched to {isLightMode ? 'Light' : 'Dark'} Mode
        </div>
      )}

      <header className="dashboard-header">
        <h1>🔧 Widget Dashboard</h1>
        <div className="connection-status">
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '🟢 Live' : '🔴 Disconnected'}
          </span>
        </div>
      </header>

      <div className="dashboard-content">
        <aside className="sidebar">
          <div className="widget-list">
            <div className="section-header">
              <h3>Your Widgets</h3>
              <button onClick={createWidget} className="btn-primary">
                + New Widget
              </button>
            </div>
            
            {widgets.map(widget => (
              <div 
                key={widget.client_id}
                className={`widget-item ${selectedWidget?.client_id === widget.client_id ? 'active' : ''} ${!widget.is_active ? 'inactive' : ''}`}
              >
                <div 
                  className="widget-info"
                  onClick={() => {
                    setSelectedWidget(widget);
                    fetchAnalytics(widget.client_id);
                  }}
                >
                  <h4>{widget.chat_title}</h4>
                  <p className="client-id">{widget.client_id}</p>
                  <span className="widget-domain">{widget.domain || 'No domain'}</span>
                </div>
                
                <div className="widget-controls">
                  <button 
                    className={`toggle-btn ${widget.is_active ? 'active' : 'inactive'}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleWidgetStatus(widget.client_id, widget.is_active);
                    }}
                    title={widget.is_active ? 'Deactivate Widget' : 'Activate Widget'}
                  >
                    {widget.is_active ? '🟢 ON' : '🔴 OFF'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </aside>

        <main className="main-content">
          {selectedWidget ? (
            <WidgetDetailsView 
              widget={selectedWidget}
              analytics={analytics[selectedWidget.client_id]}
              onUpdateConfig={(config) => updateWidgetConfig(selectedWidget.client_id, config)}
              onUploadKB={(files) => uploadKnowledgeBase(selectedWidget.client_id, files)}
              apiBase={API_BASE}
            />
          ) : (
            <div className="no-selection">
              <h2>Select a widget to manage</h2>
              <p>Choose a widget from the sidebar to view analytics and configure settings.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

const WidgetDetailsView = ({ widget, analytics, onUpdateConfig, onUploadKB, apiBase }) => {
  const [config, setConfig] = useState(widget);
  const [activeTab, setActiveTab] = useState('config');

  const handleConfigChange = (field, value) => {
    const newConfig = { ...config, [field]: value };
    setConfig(newConfig);
    onUpdateConfig(newConfig);
  };

  const tabs = [
    { id: 'config', label: '⚙️ Configuration', component: ConfigTab },
    { id: 'analytics', label: '📊 Analytics', component: AnalyticsTab },
    { id: 'knowledge', label: '📚 Knowledge Base', component: KnowledgeBaseTab },
    { id: 'embed', label: '🔗 Embed Code', component: EmbedTab }
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component;

  return (
    <div className="widget-details">
      <div className="widget-header">
        <h2>{config.chat_title}</h2>
        <div className="live-indicator">
          <span className="pulse-dot"></span>
          Live Updates Active
        </div>
      </div>

      <nav className="tab-nav">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <div className="tab-content">
        <ActiveComponent 
          config={config}
          analytics={analytics}
          onConfigChange={handleConfigChange}
          onUploadKB={onUploadKB}
          apiBase={apiBase}
        />
      </div>
    </div>
  );
};

const ConfigTab = ({ config, onConfigChange }) => {
  const [activeSection, setActiveSection] = useState('appearance');

  const sections = [
    { id: 'appearance', label: '🎨 Appearance' },
    { id: 'button', label: '🔘 Button Style' },
    { id: 'chat', label: '💬 Chat Window' },
    { id: 'colors', label: '🌈 Colors' },
    { id: 'text', label: '📝 Text Settings' },
    { id: 'behavior', label: '⚙️ Behavior' },
    { id: 'ai', label: '🤖 AI Configuration' }
  ];

  return (
    <div className="config-tab">
      <div className="config-sidebar">
        {sections.map(section => (
          <button
            key={section.id}
            className={`config-section-btn ${activeSection === section.id ? 'active' : ''}`}
            onClick={() => setActiveSection(section.id)}
          >
            {section.label}
          </button>
        ))}
      </div>

      <div className="config-content">
        {activeSection === 'appearance' && (
          <div className="config-section">
            <h3>🎨 Basic Appearance</h3>
            
            <div className="form-row">
              <div className="form-group">
                <label>Chat Title</label>
                <input
                  type="text"
                  value={config.chat_title || ''}
                  onChange={(e) => onConfigChange('chat_title', e.target.value)}
                  placeholder="AI Assistant"
                />
              </div>
              
              <div className="form-group">
                <label>Position</label>
                <select
                  value={config.position || 'bottom-right'}
                  onChange={(e) => onConfigChange('position', e.target.value)}
                >
                  <option value="bottom-right">Bottom Right</option>
                  <option value="bottom-left">Bottom Left</option>
                  <option value="top-right">Top Right</option>
                  <option value="top-left">Top Left</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label>Welcome Message</label>
              <textarea
                value={config.welcome_message || ''}
                onChange={(e) => onConfigChange('welcome_message', e.target.value)}
                placeholder="Hello! How can I help you today?"
                rows="3"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Font Family</label>
                <select
                  value={config.font_family || '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'}
                  onChange={(e) => onConfigChange('font_family', e.target.value)}
                >
                  <option value="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif">System Default</option>
                  <option value="Arial, sans-serif">Arial</option>
                  <option value="'Times New Roman', serif">Times New Roman</option>
                  <option value="'Courier New', monospace">Courier New</option>
                  <option value="Georgia, serif">Georgia</option>
                </select>
              </div>
              
              <div className="form-group">
                <label>Theme</label>
                <select
                  value={config.theme || 'light'}
                  onChange={(e) => onConfigChange('theme', e.target.value)}
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="auto">Auto</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {activeSection === 'button' && (
          <div className="config-section">
            <h3>🔘 Button Customization</h3>
            
            <div className="form-row">
              <div className="form-group">
                <label>Button Size (px)</label>
                <input
                  type="range"
                  min="40"
                  max="100"
                  value={config.button_size || 60}
                  onChange={(e) => onConfigChange('button_size', parseInt(e.target.value))}
                />
                <span className="range-value">{config.button_size || 60}px</span>
              </div>
              
              <div className="form-group">
                <label>Button Shape</label>
                <select
                  value={config.button_shape || 'circle'}
                  onChange={(e) => onConfigChange('button_shape', e.target.value)}
                >
                  <option value="circle">Circle</option>
                  <option value="square">Square</option>
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Mascot Type</label>
                <select
                  value={config.mascot_type || 'chat'}
                  onChange={(e) => onConfigChange('mascot_type', e.target.value)}
                >
                  <option value="chat">💬 Chat Bubble</option>
                  <option value="robot">🤖 Robot</option>
                  <option value="support">🛠️ Support</option>
                  <option value="question">❓ Question</option>
                  <option value="custom">🎨 Custom</option>
                </select>
              </div>
              
              <div className="form-group">
                <label>Animation</label>
                <select
                  value={config.animation_type || 'none'}
                  onChange={(e) => onConfigChange('animation_type', e.target.value)}
                >
                  <option value="none">None</option>
                  <option value="pulse">Pulse</option>
                  <option value="bounce">Bounce</option>
                  <option value="shake">Shake</option>
                  <option value="glow">Glow</option>
                </select>
              </div>
            </div>

            {config.mascot_type === 'custom' && (
              <div className="form-group">
                <label>Custom Icon (SVG)</label>
                <textarea
                  value={config.custom_icon || ''}
                  onChange={(e) => onConfigChange('custom_icon', e.target.value)}
                  placeholder="Paste SVG code here..."
                  rows="3"
                />
              </div>
            )}

            <div className="form-row">
              <div className="form-group">
                <label>Border Width (px)</label>
                <input
                  type="number"
                  min="0"
                  max="10"
                  value={config.border_width || 0}
                  onChange={(e) => onConfigChange('border_width', parseInt(e.target.value))}
                />
              </div>
              
              <div className="form-group">
                <label>Border Color</label>
                <input
                  type="color"
                  value={config.border_color || '#transparent'}
                  onChange={(e) => onConfigChange('border_color', e.target.value)}
                />
              </div>
            </div>
          </div>
        )}

        {activeSection === 'chat' && (
          <div className="config-section">
            <h3>💬 Chat Window Settings</h3>
            
            <div className="form-row">
              <div className="form-group">
                <label>Chat Width (px)</label>
                <input
                  type="range"
                  min="250"
                  max="500"
                  value={config.chat_width || 350}
                  onChange={(e) => onConfigChange('chat_width', parseInt(e.target.value))}
                />
                <span className="range-value">{config.chat_width || 350}px</span>
              </div>
              
              <div className="form-group">
                <label>Chat Height (px)</label>
                <input
                  type="range"
                  min="300"
                  max="700"
                  value={config.chat_height || 500}
                  onChange={(e) => onConfigChange('chat_height', parseInt(e.target.value))}
                />
                <span className="range-value">{config.chat_height || 500}px</span>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Border Radius (px)</label>
                <input
                  type="range"
                  min="0"
                  max="30"
                  value={config.chat_border_radius || 12}
                  onChange={(e) => onConfigChange('chat_border_radius', parseInt(e.target.value))}
                />
                <span className="range-value">{config.chat_border_radius || 12}px</span>
              </div>
              
              <div className="form-group">
                <label>Chat Background</label>
                <input
                  type="color"
                  value={config.chat_background || '#ffffff'}
                  onChange={(e) => onConfigChange('chat_background', e.target.value)}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Input Placeholder</label>
                <input
                  type="text"
                  value={config.input_placeholder || ''}
                  onChange={(e) => onConfigChange('input_placeholder', e.target.value)}
                  placeholder="Type your message..."
                />
              </div>
              
              <div className="form-group">
                <label>Send Button Text</label>
                <input
                  type="text"
                  value={config.send_button_text || ''}
                  onChange={(e) => onConfigChange('send_button_text', e.target.value)}
                  placeholder="Send"
                />
              </div>
            </div>
          </div>
        )}

        {activeSection === 'colors' && (
          <div className="config-section">
            <h3>🌈 Color Customization</h3>
            
            <div className="color-grid">
              <div className="form-group">
                <label>Primary Color</label>
                <input
                  type="color"
                  value={config.primary_color || '#007bff'}
                  onChange={(e) => onConfigChange('primary_color', e.target.value)}
                />
              </div>
              
              <div className="form-group">
                <label>Header Background</label>
                <input
                  type="color"
                  value={config.header_background || config.primary_color || '#007bff'}
                  onChange={(e) => onConfigChange('header_background', e.target.value)}
                />
              </div>
              
              <div className="form-group">
                <label>Header Text</label>
                <input
                  type="color"
                  value={config.header_text_color || '#ffffff'}
                  onChange={(e) => onConfigChange('header_text_color', e.target.value)}
                />
              </div>
              
              <div className="form-group">
                <label>Messages Background</label>
                <input
                  type="color"
                  value={config.messages_background || '#f8f9fa'}
                  onChange={(e) => onConfigChange('messages_background', e.target.value)}
                />
              </div>
              
              <div className="form-group">
                <label>Bot Message Background</label>
                <input
                  type="color"
                  value={config.bot_message_background || '#e9ecef'}
                  onChange={(e) => onConfigChange('bot_message_background', e.target.value)}
                />
              </div>
              
              <div className="form-group">
                <label>Bot Message Text</label>
                <input
                  type="color"
                  value={config.bot_message_color || '#333333'}
                  onChange={(e) => onConfigChange('bot_message_color', e.target.value)}
                />
              </div>
              
              <div className="form-group">
                <label>User Message Background</label>
                <input
                  type="color"
                  value={config.user_message_background || config.primary_color || '#007bff'}
                  onChange={(e) => onConfigChange('user_message_background', e.target.value)}
                />
              </div>
              
              <div className="form-group">
                <label>User Message Text</label>
                <input
                  type="color"
                  value={config.user_message_color || '#ffffff'}
                  onChange={(e) => onConfigChange('user_message_color', e.target.value)}
                />
              </div>
              
              <div className="form-group">
                <label>Input Background</label>
                <input
                  type="color"
                  value={config.input_background || '#ffffff'}
                  onChange={(e) => onConfigChange('input_background', e.target.value)}
                />
              </div>
              
              <div className="form-group">
                <label>Input Border</label>
                <input
                  type="color"
                  value={config.input_border_color || '#dddddd'}
                  onChange={(e) => onConfigChange('input_border_color', e.target.value)}
                />
              </div>
              
              <div className="form-group">
                <label>Send Button</label>
                <input
                  type="color"
                  value={config.send_button_color || config.primary_color || '#007bff'}
                  onChange={(e) => onConfigChange('send_button_color', e.target.value)}
                />
              </div>
              
              <div className="form-group">
                <label>Send Button Text</label>
                <input
                  type="color"
                  value={config.send_button_text_color || '#ffffff'}
                  onChange={(e) => onConfigChange('send_button_text_color', e.target.value)}
                />
              </div>
            </div>
          </div>
        )}

        {activeSection === 'text' && (
          <div className="config-section">
            <h3>📝 Typography Settings</h3>
            
            <div className="form-row">
              <div className="form-group">
                <label>Header Font Size</label>
                <select
                  value={config.header_font_size || '16px'}
                  onChange={(e) => onConfigChange('header_font_size', e.target.value)}
                >
                  <option value="12px">12px</option>
                  <option value="14px">14px</option>
                  <option value="16px">16px</option>
                  <option value="18px">18px</option>
                  <option value="20px">20px</option>
                </select>
              </div>
              
              <div className="form-group">
                <label>Message Font Size</label>
                <select
                  value={config.message_font_size || '14px'}
                  onChange={(e) => onConfigChange('message_font_size', e.target.value)}
                >
                  <option value="12px">12px</option>
                  <option value="14px">14px</option>
                  <option value="16px">16px</option>
                  <option value="18px">18px</option>
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Input Font Size</label>
                <select
                  value={config.input_font_size || '14px'}
                  onChange={(e) => onConfigChange('input_font_size', e.target.value)}
                >
                  <option value="12px">12px</option>
                  <option value="14px">14px</option>
                  <option value="16px">16px</option>
                  <option value="18px">18px</option>
                </select>
              </div>
              
              <div className="form-group">
                <label>Send Button Font Size</label>
                <select
                  value={config.send_button_font_size || '14px'}
                  onChange={(e) => onConfigChange('send_button_font_size', e.target.value)}
                >
                  <option value="12px">12px</option>
                  <option value="14px">14px</option>
                  <option value="16px">16px</option>
                  <option value="18px">18px</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {activeSection === 'behavior' && (
          <div className="config-section">
            <h3>⚙️ Behavior Settings</h3>
            
            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={config.analytics_enabled || false}
                  onChange={(e) => onConfigChange('analytics_enabled', e.target.checked)}
                />
                Enable Analytics Tracking
              </label>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Rate Limit (messages/hour)</label>
                <input
                  type="number"
                  value={config.rate_limit || 100}
                  onChange={(e) => onConfigChange('rate_limit', parseInt(e.target.value))}
                  min="1"
                  max="1000"
                />
              </div>
              
              <div className="form-group">
                <label>Max File Size (MB)</label>
                <input
                  type="number"
                  value={config.max_file_size || 10}
                  onChange={(e) => onConfigChange('max_file_size', parseInt(e.target.value))}
                  min="1"
                  max="100"
                />
              </div>
            </div>

            <div className="form-group">
              <label>Enabled Features</label>
              <div className="checkbox-group">
                {['chat', 'voice', 'file_upload', 'feedback'].map(feature => (
                  <label key={feature}>
                    <input
                      type="checkbox"
                      checked={(config.enabled_features || []).includes(feature)}
                      onChange={(e) => {
                        const features = config.enabled_features || [];
                        if (e.target.checked) {
                          onConfigChange('enabled_features', [...features, feature]);
                        } else {
                          onConfigChange('enabled_features', features.filter(f => f !== feature));
                        }
                      }}
                    />
                    {feature.replace('_', ' ').toUpperCase()}
                  </label>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeSection === 'ai' && (
          <div className="config-section">
            <h3>🤖 AI Configuration</h3>
            
            {/* Core AI Settings */}
            <div className="config-group">
              <h4>Core AI Settings</h4>
              
              <div className="config-item">
                <label>AI Model</label>
                <select 
                  value={config.ai_model || 'gemini-1.5-flash'} 
                  onChange={(e) => onConfigChange('ai_model', e.target.value)}
                >
                  <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                  <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                  <option value="gpt-4">GPT-4</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                </select>
              </div>

              <div className="config-item">
                <label>AI Personality</label>
                <input
                  type="text"
                  value={config.ai_personality || ''}
                  onChange={(e) => onConfigChange('ai_personality', e.target.value)}
                  placeholder="e.g., Professional, Friendly, Technical, Casual"
                />
              </div>

              <div className="config-item">
                <label>System Prompt</label>
                <textarea
                  value={config.system_prompt || ''}
                  onChange={(e) => onConfigChange('system_prompt', e.target.value)}
                  placeholder="Define how the AI should behave and respond to users..."
                  rows={4}
                />
              </div>

              <div className="config-item">
                <label>Custom Instructions</label>
                <textarea
                  value={config.custom_instructions || ''}
                  onChange={(e) => onConfigChange('custom_instructions', e.target.value)}
                  placeholder="Additional specific instructions for the AI..."
                  rows={3}
                />
              </div>
            </div>

            {/* Voice Settings */}
            <div className="config-group">
              <h4>Voice & Speech</h4>
              
              <div className="config-item">
                <label>
                  <input
                    type="checkbox"
                    checked={config.voice_enabled || false}
                    onChange={(e) => onConfigChange('voice_enabled', e.target.checked)}
                  />
                  Enable Voice Recording
                </label>
              </div>

              <div className="config-item">
                <label>
                  <input
                    type="checkbox"
                    checked={config.auto_send_voice || false}
                    onChange={(e) => onConfigChange('auto_send_voice', e.target.checked)}
                  />
                  Auto-send Voice Messages
                </label>
              </div>

              <div className="config-item">
                <label>Voice Transcription Language</label>
                <select 
                  value={config.voice_transcription_language || 'en-US'} 
                  onChange={(e) => onConfigChange('voice_transcription_language', e.target.value)}
                >
                  <option value="en-US">English (US)</option>
                  <option value="en-GB">English (UK)</option>
                  <option value="es-ES">Spanish</option>
                  <option value="fr-FR">French</option>
                  <option value="de-DE">German</option>
                  <option value="it-IT">Italian</option>
                  <option value="pt-BR">Portuguese (Brazil)</option>
                  <option value="ja-JP">Japanese</option>
                  <option value="ko-KR">Korean</option>
                  <option value="zh-CN">Chinese (Simplified)</option>
                </select>
              </div>
            </div>

            {/* Image Analysis */}
            <div className="config-group">
              <h4>Image Analysis</h4>
              
              <div className="config-item">
                <label>
                  <input
                    type="checkbox"
                    checked={config.image_analysis_enabled || false}
                    onChange={(e) => onConfigChange('image_analysis_enabled', e.target.checked)}
                  />
                  Enable Image Analysis
                </label>
              </div>

              <div className="config-item">
                <label>Image Analysis Instructions</label>
                <textarea
                  value={config.image_analysis_instructions || ''}
                  onChange={(e) => onConfigChange('image_analysis_instructions', e.target.value)}
                  placeholder="Instructions for how to analyze images..."
                  rows={2}
                />
              </div>

              <div className="config-item">
                <label>Max Image Size (MB)</label>
                <input
                  type="number"
                  value={config.max_image_size || 5}
                  onChange={(e) => onConfigChange('max_image_size', parseInt(e.target.value))}
                  min={1}
                  max={20}
                />
              </div>
            </div>

            {/* Response Settings */}
            <div className="config-group">
              <h4>Response Behavior</h4>
              
              <div className="config-item">
                <label>Temperature ({config.temperature || 0.7})</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={config.temperature || 0.7}
                  onChange={(e) => onConfigChange('temperature', parseFloat(e.target.value))}
                />
                <small>Controls randomness in responses (0 = predictable, 1 = creative)</small>
              </div>

              <div className="config-item">
                <label>Max Response Length</label>
                <input
                  type="number"
                  value={config.max_response_length || 500}
                  onChange={(e) => onConfigChange('max_response_length', parseInt(e.target.value))}
                  min={50}
                  max={2000}
                />
              </div>

              <div className="config-item">
                <label>Response Tone</label>
                <select 
                  value={config.response_tone || 'balanced'} 
                  onChange={(e) => onConfigChange('response_tone', e.target.value)}
                >
                  <option value="professional">Professional</option>
                  <option value="friendly">Friendly</option>
                  <option value="casual">Casual</option>
                  <option value="technical">Technical</option>
                  <option value="empathetic">Empathetic</option>
                  <option value="balanced">Balanced</option>
                </select>
              </div>

              <div className="config-item">
                <label>
                  <input
                    type="checkbox"
                    checked={config.include_sources || false}
                    onChange={(e) => onConfigChange('include_sources', e.target.checked)}
                  />
                  Include Knowledge Base Sources
                </label>
              </div>

              <div className="config-item">
                <label>
                  <input
                    type="checkbox"
                    checked={config.enable_follow_up_questions || false}
                    onChange={(e) => onConfigChange('enable_follow_up_questions', e.target.checked)}
                  />
                  Suggest Follow-up Questions
                </label>
              </div>
            </div>

            {/* Conversation Settings */}
            <div className="config-group">
              <h4>Conversation Management</h4>
              
              <div className="config-item">
                <label>Context Memory Length</label>
                <input
                  type="number"
                  value={config.context_memory_length || 10}
                  onChange={(e) => onConfigChange('context_memory_length', parseInt(e.target.value))}
                  min={1}
                  max={50}
                />
                <small>Number of previous messages to remember</small>
              </div>

              <div className="config-item">
                <label>
                  <input
                    type="checkbox"
                    checked={config.enable_conversation_starters || false}
                    onChange={(e) => onConfigChange('enable_conversation_starters', e.target.checked)}
                  />
                  Show Conversation Starters
                </label>
              </div>

              <div className="config-item">
                <label>Fallback Response</label>
                <textarea
                  value={config.fallback_response || ''}
                  onChange={(e) => onConfigChange('fallback_response', e.target.value)}
                  placeholder="Response when AI cannot answer a question..."
                  rows={2}
                />
              </div>
            </div>

            {/* Advanced AI Features */}
            <div className="config-group">
              <h4>Advanced Features</h4>
              
              <div className="config-item">
                <label>
                  <input
                    type="checkbox"
                    checked={config.enable_sentiment_analysis || false}
                    onChange={(e) => onConfigChange('enable_sentiment_analysis', e.target.checked)}
                  />
                  Enable Sentiment Analysis
                </label>
              </div>

              <div className="config-item">
                <label>
                  <input
                    type="checkbox"
                    checked={config.enable_intent_detection || false}
                    onChange={(e) => onConfigChange('enable_intent_detection', e.target.checked)}
                  />
                  Enable Intent Detection
                </label>
              </div>

              <div className="config-item">
                <label>
                  <input
                    type="checkbox"
                    checked={config.enable_auto_translation || false}
                    onChange={(e) => onConfigChange('enable_auto_translation', e.target.checked)}
                  />
                  Enable Auto Translation
                </label>
              </div>

              <div className="config-item">
                <label>Default Language</label>
                <select 
                  value={config.default_language || 'en'} 
                  onChange={(e) => onConfigChange('default_language', e.target.value)}
                >
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                  <option value="it">Italian</option>
                  <option value="pt">Portuguese</option>
                  <option value="ja">Japanese</option>
                  <option value="ko">Korean</option>
                  <option value="zh">Chinese</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const AnalyticsTab = ({ analytics }) => {
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      setRefreshing(true);
      // Trigger refresh - parent component should handle this
      setTimeout(() => setRefreshing(false), 1000);
    }, 30000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  if (!analytics) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading comprehensive analytics...</p>
      </div>
    );
  }

  const formatTime = (isoString) => {
    return new Date(isoString).toLocaleString();
  };

  const getLeadScoreColor = (score) => {
    if (score > 0.7) return '#28a745'; // Green
    if (score > 0.4) return '#ffc107'; // Yellow
    if (score > 0.1) return '#fd7e14'; // Orange
    return '#6c757d'; // Gray
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'positive': return '#28a745';
      case 'negative': return '#dc3545';
      default: return '#6c757d';
    }
  };

  return (
    <div className="analytics-tab-enhanced">
      {/* Header Controls */}
      <div className="analytics-header">
        <div className="analytics-title">
          <h3>📊 Real-Time Analytics Dashboard</h3>
          <div className="last-updated">
            Last updated: {formatTime(analytics.last_updated)}
            {refreshing && <span className="refreshing-indicator">🔄</span>}
          </div>
        </div>
        <div className="analytics-controls">
          <label className="auto-refresh-toggle">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-refresh (30s)
          </label>
        </div>
      </div>

      {/* Real-time Overview Cards */}
      <div className="analytics-overview">
        <div className="metric-card primary">
          <div className="metric-icon">👥</div>
          <div className="metric-content">
            <h4>Active Users</h4>
            <div className="metric-number">{analytics.summary?.active_users_now || 0}</div>
            <small>Currently online</small>
          </div>
        </div>
        
        <div className="metric-card success">
          <div className="metric-icon">🎯</div>
          <div className="metric-content">
            <h4>Potential Leads</h4>
            <div className="metric-number">{analytics.lead_analytics?.potential_leads || 0}</div>
            <small>{analytics.lead_analytics?.conversion_rate || 0}% conversion rate</small>
          </div>
        </div>
        
        <div className="metric-card info">
          <div className="metric-icon">💬</div>
          <div className="metric-content">
            <h4>Conversations</h4>
            <div className="metric-number">{analytics.summary?.total_conversations || 0}</div>
            <small>Avg. {analytics.summary?.avg_conversation_length || 0} words</small>
          </div>
        </div>
        
        <div className="metric-card warning">
          <div className="metric-icon">⚡</div>
          <div className="metric-content">
            <h4>Response Time</h4>
            <div className="metric-number">{analytics.summary?.avg_response_time || 0}s</div>
            <small>Average AI response</small>
          </div>
        </div>
      </div>

      {/* Live Sessions */}
      <div className="analytics-section">
        <h4>🔴 Live User Sessions</h4>
        <div className="live-sessions">
          {(analytics.live_sessions || []).length === 0 ? (
            <div className="no-data">No active sessions right now</div>
          ) : (
            <div className="sessions-grid">
              {analytics.live_sessions.slice(0, 6).map((session) => (
                <div key={session.session_id} className={`session-card ${session.is_active ? 'active' : 'inactive'}`}>
                  <div className="session-header">
                    <div className="user-info">
                      <div className="user-avatar">
                        {session.user_info?.name ? session.user_info.name.charAt(0).toUpperCase() : '?'}
                      </div>
                      <div className="user-details">
                        <div className="user-name">
                          {session.user_info?.name || session.user_info?.email || `User ${session.session_id.substring(0, 8)}`}
                        </div>
                        <div className="user-location">
                          {session.location?.country && session.location?.city 
                            ? `${session.location.city}, ${session.location.country}`
                            : session.location?.country || 'Unknown location'
                          }
                        </div>
                      </div>
                    </div>
                    <div className="session-status">
                      <div className={`status-indicator ${session.is_active ? 'online' : 'offline'}`}></div>
                    </div>
                  </div>
                  
                  <div className="session-metrics">
                    <div className="metric">
                      <span className="metric-label">Lead Score:</span>
                      <span 
                        className="metric-value lead-score" 
                        style={{ color: getLeadScoreColor(session.lead_score) }}
                      >
                        {Math.round(session.lead_score * 100)}%
                      </span>
                    </div>
                    <div className="metric">
                      <span className="metric-label">Sentiment:</span>
                      <span 
                        className="metric-value sentiment"
                        style={{ color: getSentimentColor(session.sentiment) }}
                      >
                        {session.sentiment}
                      </span>
                    </div>
                    <div className="metric">
                      <span className="metric-label">Messages:</span>
                      <span className="metric-value">{session.events_count}</span>
                    </div>
                  </div>
                  
                  <div className="session-footer">
                    <small className="last-activity">
                      Last active: {new Date(session.last_activity).toLocaleTimeString()}
                    </small>
                    {session.device?.device_type && (
                      <small className="device-info">
                        📱 {session.device.device_type} • {session.device.browser}
                      </small>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Lead Analytics */}
      <div className="analytics-section">
        <h4>🎯 Lead Analysis & Potential Customers</h4>
        <div className="lead-analytics">
          <div className="lead-summary">
            <div className="lead-stat">
              <h5>High-Quality Leads</h5>
              <div className="lead-number high-quality">{analytics.lead_analytics?.high_quality_leads || 0}</div>
            </div>
            <div className="lead-stat">
              <h5>Potential Leads</h5>
              <div className="lead-number potential">{analytics.lead_analytics?.potential_leads || 0}</div>
            </div>
            <div className="lead-stat">
              <h5>Conversion Rate</h5>
              <div className="lead-number conversion">{analytics.lead_analytics?.conversion_rate || 0}%</div>
            </div>
          </div>
          
          <div className="top-leads">
            <h5>🏆 Top Potential Leads</h5>
            {(analytics.lead_analytics?.top_leads || []).length === 0 ? (
              <div className="no-data">No potential leads identified yet</div>
            ) : (
              <div className="leads-list">
                {analytics.lead_analytics.top_leads.slice(0, 5).map((lead, index) => (
                  <div key={lead.session_id} className="lead-item">
                    <div className="lead-rank">#{index + 1}</div>
                    <div className="lead-details">
                      <div className="lead-name">
                        {lead.user_info?.name || lead.user_info?.email || `Session ${lead.session_id}`}
                      </div>
                      <div className="lead-meta">
                        <span className="lead-score" style={{ color: getLeadScoreColor(lead.lead_score) }}>
                          Score: {Math.round(lead.lead_score * 100)}%
                        </span>
                        <span className="lead-sentiment" style={{ color: getSentimentColor(lead.sentiment) }}>
                          {lead.sentiment} sentiment
                        </span>
                        <span className="lead-activity">
                          {lead.conversation_length} words exchanged
                        </span>
                      </div>
                      <div className="lead-contact">
                        {lead.user_info?.email && (
                          <span className="contact-info">📧 {lead.user_info.email}</span>
                        )}
                        {lead.user_info?.phone && (
                          <span className="contact-info">📞 {lead.user_info.phone}</span>
                        )}
                      </div>
                    </div>
                    <div className="lead-actions">
                      <small>Last seen: {new Date(lead.last_activity).toLocaleString()}</small>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* User Demographics & Insights */}
      <div className="analytics-section">
        <h4>👥 User Insights & Demographics</h4>
        <div className="user-insights">
          <div className="insight-grid">
            <div className="insight-card">
              <h5>🌍 Geographic Distribution</h5>
              <div className="geographic-data">
                {Object.entries(analytics.user_analytics?.geographic_distribution || {}).map(([country, count]) => (
                  <div key={country} className="geo-item">
                    <span className="country">{country}</span>
                    <span className="count">{count} users</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="insight-card">
              <h5>📱 Device Types</h5>
              <div className="device-breakdown">
                {Object.entries(analytics.user_analytics?.device_breakdown || {}).map(([device, count]) => (
                  <div key={device} className="device-item">
                    <span className="device-type">{device}</span>
                    <span className="device-count">{count}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="insight-card">
              <h5>😊 Sentiment Analysis</h5>
              <div className="sentiment-breakdown">
                <div className="sentiment-item positive">
                  <span>Positive</span>
                  <span>{analytics.user_analytics?.sentiment_distribution?.positive || 0}</span>
                </div>
                <div className="sentiment-item neutral">
                  <span>Neutral</span>
                  <span>{analytics.user_analytics?.sentiment_distribution?.neutral || 0}</span>
                </div>
                <div className="sentiment-item negative">
                  <span>Negative</span>
                  <span>{analytics.user_analytics?.sentiment_distribution?.negative || 0}</span>
                </div>
              </div>
            </div>
            
            <div className="insight-card">
              <h5>🌐 Browser Usage</h5>
              <div className="browser-breakdown">
                {Object.entries(analytics.user_analytics?.browser_breakdown || {}).map(([browser, count]) => (
                  <div key={browser} className="browser-item">
                    <span className="browser-name">{browser}</span>
                    <span className="browser-count">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Event Timeline */}
      <div className="analytics-section">
        <h4>📈 Activity Timeline</h4>
        <div className="activity-timeline">
          <div className="timeline-controls">
            <button className="timeline-btn active">Last 24 Hours</button>
            <button className="timeline-btn">Last 7 Days</button>
          </div>
          
          <div className="hourly-chart">
            {Object.entries(analytics.time_analytics?.hourly_data || {}).map(([hour, count]) => (
              <div key={hour} className="hour-bar">
                <div className="bar" style={{ height: `${(count / Math.max(...Object.values(analytics.time_analytics?.hourly_data || {}))) * 100}%` }}></div>
                <small className="hour-label">{hour.split(' ')[1]}</small>
                <small className="hour-count">{count}</small>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Activity Feed */}
      <div className="analytics-section">
        <h4>🔄 Real-Time Activity Feed</h4>
        <div className="activity-feed">
          {(analytics.recent_events || []).slice(-10).reverse().map((event, index) => (
            <div key={index} className="activity-item">
              <div className="activity-icon">
                {event.event_type === 'chat_start' && '💬'}
                {event.event_type === 'message_sent' && '📝'}
                {event.event_type === 'ai_response' && '🤖'}
                {event.event_type === 'file_uploaded' && '📎'}
                {event.event_type === 'feedback_given' && '⭐'}
                {event.event_type === 'user_joined' && '👋'}
                {event.event_type === 'conversation_lead' && '🎯'}
              </div>
              <div className="activity-content">
                <div className="activity-description">
                  <strong>{event.event_type.replace('_', ' ')}</strong>
                  {event.user_info?.name && <span> by {event.user_info.name}</span>}
                  {event.metadata?.message && <span> - "{event.metadata.message.substring(0, 50)}..."</span>}
                </div>
                <div className="activity-time">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const KnowledgeBaseTab = ({ onUploadKB }) => (
  <div className="knowledge-tab">
    <h3>📚 Knowledge Base Management</h3>
    
    <div className="upload-section">
      <h4>Upload Documents</h4>
      <p>Upload documents to train your AI assistant. Supported formats: PDF, TXT, DOCX, CSV, JSON, JSONL</p>
      
      <div className="file-upload">
        <input
          type="file"
          multiple
          accept=".pdf,.txt,.docx,.csv,.json,.jsonl"
          onChange={(e) => onUploadKB(e.target.files)}
          className="file-input"
        />
        <div className="upload-info">
          <p>Drag and drop files here or click to browse</p>
          <small>📄 Documents: PDF, TXT, DOCX, CSV | 🧠 Knowledge: JSON, JSONL</small>
        </div>
      </div>
    </div>

    <div className="kb-status">
      <h4>Current Knowledge Base</h4>
      <div className="kb-stats">
        <div className="stat">
          <span className="label">Documents:</span>
          <span className="value">15</span>
        </div>
        <div className="stat">
          <span className="label">Total Size:</span>
          <span className="value">2.3 MB</span>
        </div>
        <div className="stat">
          <span className="label">Last Updated:</span>
          <span className="value">2 hours ago</span>
        </div>
      </div>
    </div>
  </div>
);

const EmbedTab = ({ config, apiBase }) => {
  const embedCode = `<!-- AI Knowledge Base Widget -->
<script async src="${apiBase}/api/widget/script/${config.client_id}"></script>`;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(embedCode);
    alert('Embed code copied to clipboard!');
  };

  return (
    <div className="embed-tab">
      <h3>🔗 Embed Your Widget</h3>
      
      <div className="embed-section">
        <p>Copy and paste this code into your website's HTML, preferably before the closing &lt;/body&gt; tag:</p>
        
        <div className="code-block">
          <pre>{embedCode}</pre>
          <button onClick={copyToClipboard} className="copy-btn">
            📋 Copy Code
          </button>
        </div>
      </div>

      <div className="integration-help">
        <h4>Integration Instructions</h4>
        <ol>
          <li>Copy the embed code above</li>
          <li>Paste it into your website's HTML</li>
          <li>The widget will appear automatically</li>
          <li>All changes made here update instantly!</li>
        </ol>
      </div>

      <div className="preview-section">
        <h4>Live Preview</h4>
        <p>Your widget is live at: <strong>{config.domain || 'Configure domain in settings'}</strong></p>
      </div>
    </div>
  );
};

export default WidgetDashboard;
