import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  BiBarChartAlt2, BiRocket, BiGroup, BiEnvelope,
  BiCog, BiCube, BiLayer, BiChevronRight, BiMenu, BiX
} from 'react-icons/bi';
import '../pages/Dashboard.css';

const sidebarLinks = [
  { label: 'Dashboard', icon: <BiBarChartAlt2 />, route: '/dashboard' },
  { label: 'Campaigns', icon: <BiRocket />, route: '/campaigns' },
  { label: 'Journeys', icon: <BiLayer />, route: '/Journeys' },
  { label: 'Audience', icon: <BiGroup />, route: '/audience' },
  { label: 'Templates', icon: <BiEnvelope />, route: '/templates' },
  { label: 'Content', icon: <BiCube />, route: '/content' },
  { label: 'Products', icon: <BiCube />, route: '/products' },
  { label: 'Settings', icon: <BiCog />, route: '/settings' },
];

export default function Sidebar({
  activeSidebar,
  setActiveSidebar,
  sidebarOpen,
  setSidebarOpen
}: {
  activeSidebar: string,
  setActiveSidebar: (label: string) => void,
  sidebarOpen: boolean,
  setSidebarOpen: (open: boolean) => void
}) {
  const navigate = useNavigate();

  const handleSidebarClick = (label: string, route: string) => {
    setActiveSidebar(label);
    if (route) navigate(route);
  };

  return (
    <aside className={`sidebar ${sidebarOpen ? 'sidebar-open' : 'sidebar-collapsed'}`}>
      <div className="sidebar-header">
        <div className="logo-wrapper">
          {sidebarOpen ? (
            <>
              <img
                src="/logo192.png"
                alt="Bird Corp Logo"
                className="sidebar-logo"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
              <span className="logo-text">Bird Corp.</span>
            </>
          ) : (
            <BiRocket size={28} />
          )}
        </div>

        <button
          className="sidebar-toggle"
          onClick={() => setSidebarOpen(!sidebarOpen)}
          title={sidebarOpen ? 'Collapse Sidebar' : 'Expand Sidebar'}
        >
          {sidebarOpen ? <BiX /> : <BiMenu />}
        </button>
      </div>

      <ul className="sidebar-links">
        {sidebarLinks.map((item) => (
          <li
            key={item.label}
            className={`sidebar-link ${activeSidebar === item.label ? 'active' : ''}`}
            onClick={() => handleSidebarClick(item.label, item.route)}
            role="button"
            tabIndex={0}
          >
            <span className="sidebar-icon">{item.icon}</span>
            {sidebarOpen && <span className="sidebar-label">{item.label}</span>}
            {activeSidebar === item.label && sidebarOpen && (
              <BiChevronRight className="sidebar-chevron" />
            )}
          </li>
        ))}
      </ul>

      {sidebarOpen && (
        <div className="sidebar-footer">
          <Link to="/chat" className="action-button blue">Chat</Link>
          <Link to="/knowledge-base" className="action-button gray">Knowledge Base</Link>
          <Link to="/settings" className="action-button purple">Settings</Link>
        </div>
      )}
    </aside>
  );
}
