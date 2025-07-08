import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

import Dashboard from './pages/Dashboard.tsx';
import Chat from './pages/Chat.tsx';
import KnowledgeBase from './pages/KnowledgeBase.tsx';
import Login from './pages/Login.tsx';
import Register from './pages/Register.tsx';
import ChatWidget from './components/ChatWidget';
import ChatbotWidget from './components/ChatbotWidget.tsx';
import UserDashboard from './pages/UserDashboard.tsx';
import Campaigns from './pages/Campaigns.tsx';
import Journeys from './pages/Journeys.tsx';
import JourneyDetail from './pages/JourneyDetail.tsx'; // ✅ New page
import Layout from './components/Layout.tsx';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route  
            path="/dashboard"
            element={
              <Layout>
                <Dashboard />
              </Layout>
            }
          />
          <Route
            path="/chat"
            element={
              <Layout>
                <Chat />
              </Layout>
            }
          />
          <Route
            path="/knowledge-base"
            element={
              <Layout>
                <KnowledgeBase />
              </Layout>
            }
          />
          <Route
            path="/user-dashboard"
            element={
              <Layout>
                <UserDashboard />
              </Layout>
            }
          />
          <Route
            path="/campaigns"
            element={
              <Layout>
                <Campaigns />
              </Layout>
            }
          />
          <Route
            path="/journeys"
            element={
              <Layout>
                <Journeys />
              </Layout>
            }
          />
          <Route
            path="/journeys/:id"
            element={
              <Layout>
                <JourneyDetail />
              </Layout>
            }
          />
          <Route path="/" element={<Login />} />
        </Routes>
        <ChatWidget />
        <ChatbotWidget />
      </div>
    </Router>
  );
}

export default App;
