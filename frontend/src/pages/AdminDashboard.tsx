// AdminDashboard.tsx - Widget Configuration Admin Panel
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import WidgetDashboard from '../components/WidgetDashboard';
import './AdminDashboard.css';

const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { logout, user } = useAuth();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <div className="admin-dashboard-wrapper">
      {/* Admin Header */}
      <div className="admin-header">
        <div className="admin-header-content">
          <div className="admin-info">
            <h1>Widget Configuration Dashboard</h1>
            <p>Manage widgets, configurations, and knowledge base</p>
            <div className="admin-user-info">
              <span>Welcome, {user?.email}</span>
              <span className="admin-role-badge">Widget Admin</span>
            </div>
          </div>
          <div className="admin-actions">
            <button className="logout-button" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Widget Dashboard Component */}
      <WidgetDashboard />
    </div>
  );
};

export default AdminDashboard;
