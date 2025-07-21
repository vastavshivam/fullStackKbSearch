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
import PrivateRoute from './components/PrivateRoute';

function App() {
  // Helper to render ChatWidget only if enabled
  function ChatWidgetConditional() {
    const { config } = useWidgetConfig();
    return config.enabled ? <ChatWidget /> : null;
  }
  
  return (
    <WidgetConfigProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route  
              path="/dashboard"
              element={
                <PrivateRoute>
                  <Layout>
                    <Dashboard />
                  </Layout>
                </PrivateRoute>
              }
            />
            <Route
              path="/chat"
              element={
                <PrivateRoute>
                  <Layout>
                    <Chat />
                  </Layout>
                </PrivateRoute>
              }
            />
            <Route
              path="/knowledge-base"
              element={
                <PrivateRoute>
                  <Layout>
                    <KnowledgeBase />
                  </Layout>
                </PrivateRoute>
              }
            />
            <Route
              path="/user-dashboard"
              element={
                <PrivateRoute>
                  <Layout>
                    <UserDashboard />
                  </Layout>
                </PrivateRoute>
              }
            />
            <Route
              path="/campaigns"
              element={
                <PrivateRoute>
                  <Layout>
                    <Campaigns />
                  </Layout>
                </PrivateRoute>
              }
            />
            <Route
              path="/journeys"
              element={
                <PrivateRoute>
                  <Layout>
                    <Journeys />
                  </Layout>
                </PrivateRoute>
              }
            />
            <Route
              path="/journeys/:id"
              element={
                <PrivateRoute>
                  <Layout>
                    <JourneyDetail />
                  </Layout>
                </PrivateRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <PrivateRoute>
                  <Layout>
                    <Settings />
                  </Layout>
                </PrivateRoute>
              }
            />
            <Route
              path="/integrations"
              element={
                <PrivateRoute>
                  <Layout>
                    <Integrations />
                  </Layout>
                </PrivateRoute>
              }
            />
            <Route
              path="/template"
              element={
                <PrivateRoute>
                  <Layout>
                    <TemplatePage />
                  </Layout>
                </PrivateRoute>
              }
            />
            <Route path="/" element={<Login />} />
          </Routes>
          <ChatWidgetConditional />
        </div>
      </Router>
    </WidgetConfigProvider>
  );
}

export default App;
