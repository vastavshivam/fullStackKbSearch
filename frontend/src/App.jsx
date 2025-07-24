import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import KnowledgeBase from './pages/KnowledgeBase';
import Login from './pages/Login';
import Register from './pages/Register';
import Settings from './pages/Settings';
import ChatWidget from './components/ChatWidget';
import ChatbotWidget from './components/ChatWidget';  
import { WidgetConfigProvider, useWidgetConfig } from './components/WidgetConfigContext';
import UserDashboard from './pages/UserDashboard';
import Campaigns from './pages/Campaigns';
import Journeys from './pages/Journeys';
import JourneyDetail from './pages/JourneyDetail'; // ✅ New page
import Integrations from './pages/Integrations'; // ✅ New integrations page
import Layout from './components/Layout';
import TemplatePage from './pages/TemplatePage';
import { AuthProvider } from './hooks/useAuth';
// import PrivateRoute from './components/PrivateRoute';

function App() {
  // Helper to render ChatWidget only if enabled
  function ChatWidgetConditional() {
    const { config } = useWidgetConfig();
    return config.enabled ? <ChatWidget /> : null;
  }
  
  return (
    <AuthProvider>
      <WidgetConfigProvider>
        <Router>
          <div className="App">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              {/* Commented out PrivateRoute for now */}
              <Route path="/dashboard" element={<Layout><Dashboard /></Layout>} />
              <Route path="/chat" element={<Layout><Chat /></Layout>} />
              <Route path="/knowledge-base" element={<Layout><KnowledgeBase /></Layout>} />
              <Route path="/user-dashboard" element={<Layout><UserDashboard /></Layout>} />
              <Route path="/campaigns" element={<Layout><Campaigns /></Layout>} />
              <Route path="/journeys" element={<Layout><Journeys /></Layout>} />
              <Route path="/journeys/:id" element={<Layout><JourneyDetail /></Layout>} />
              <Route path="/settings" element={<Layout><Settings /></Layout>} />
              <Route path="/integrations" element={<Layout><Integrations /></Layout>} />
              <Route path="/template" element={<Layout><TemplatePage /></Layout>} />
              <Route path="/" element={<Login />} />
            </Routes>
            <ChatWidgetConditional />
          </div>
        </Router>
      </WidgetConfigProvider>
    </AuthProvider>
  );
}

export default App;
