import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  BiBarChartAlt2, BiUser, BiRocket, BiGroup, BiEnvelope,
  BiCog, BiCube, BiLayer, BiChevronRight, BiChevronDown, BiChevronUp, BiMenu, BiX, BiPlug, BiMessageRounded
} from 'react-icons/bi';
import '../pages/Dashboard.css';

const sidebarLinks = [
  { label: 'Dashboard', icon: <BiBarChartAlt2 />, route: '/dashboard' },
  { label: 'Campaigns', icon: <BiRocket />, route: '/campaigns' },
  { label: 'Journeys', icon: <BiLayer />, route: '/Journeys' },
  { label: 'Audience', icon: <BiGroup />, route: '/audience' },
  { label: 'Template', icon: <BiEnvelope />, route: '/template' },
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
  const [showIntegrations, setShowIntegrations] = useState(false);

  const handleSidebarClick = (label: string, route: string) => {
    setActiveSidebar(label);
    if (route) navigate(route);
  };

  const handleIntegrationClick = () => {
    setShowIntegrations(!showIntegrations);
    setActiveSidebar('Integrations');
  };

  const handleSubItemClick = (label: string, route: string) => {
    setActiveSidebar(label);
    navigate(route);
  };

  return (
    <aside className={`sidebar ${sidebarOpen ? 'sidebar-open' : 'sidebar-collapsed'}`}>
      <div className="sidebar-header">
        <div className="logo-wrapper">
          {sidebarOpen ? (
            <>
              <img
                src="/logo192.png"
                alt="AppG Logo"
                className="sidebar-logo"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
              <span className="logo-text">AppG</span>
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

        {/* Integrations as expandable menu with WhatsApp submenu */}
        <li
          className={`sidebar-link ${activeSidebar === 'Integrations' ? 'active' : ''}`}
          onClick={handleIntegrationClick}
          role="button"
          tabIndex={0}
        >
          <span className="sidebar-icon"><BiPlug /></span>
          {sidebarOpen && <span className="sidebar-label">Integrations</span>}
          {sidebarOpen && (
            showIntegrations ? <BiChevronDown className="sidebar-chevron" /> : <BiChevronRight className="sidebar-chevron" />
          )}
        </li>
        {/* WhatsApp submenu, only visible if Integrations expanded */}
        {showIntegrations && sidebarOpen && (
          <li
            className={`sidebar-link ${activeSidebar === 'WhatsApp' ? 'active' : ''}`}
            onClick={() => handleSubItemClick('WhatsApp', '/integrations')}
            role="button"
            tabIndex={0}
            style={{ paddingLeft: 32 }}
          >
            <span className="sidebar-icon"><BiMessageRounded /></span>
            <span className="sidebar-label">WhatsApp</span>
            {activeSidebar === 'WhatsApp' && <BiChevronRight className="sidebar-chevron" />}
          </li>
        )}
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
