
import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function Layout({ children }) {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeSidebar, setActiveSidebar] = useState('Dashboard');

  // Hide sidebar on /user-dashboard
  const hideSidebar = location.pathname === '/user-dashboard';

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {!hideSidebar && (
        <Sidebar
          activeSidebar={activeSidebar}
          setActiveSidebar={setActiveSidebar}
          sidebarOpen={sidebarOpen}
          setSidebarOpen={setSidebarOpen}
        />
      )}
      <main style={{ flex: 1 }}>{children}</main>
    </div>
  );
}
