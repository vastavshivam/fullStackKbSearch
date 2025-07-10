import React, { useState } from 'react';
import Sidebar from './Sidebar';

export default function Layout({ children }) {
  const [activeSidebar, setActiveSidebar] = useState('Dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar activeSidebar={activeSidebar} setActiveSidebar={setActiveSidebar} sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
      <main style={{ flex: 1 }}>{children}</main>
    </div>
  );
}
