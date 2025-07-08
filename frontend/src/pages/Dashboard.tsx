// src/pages/Dashboard.tsx
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  BiBarChartAlt2, BiUser, BiRocket, BiGroup, BiEnvelope,
  BiCog, BiCube, BiLayer, BiChevronRight, BiCheckCircle,
  BiErrorCircle, BiTimeFive, BiMenu, BiX, BiMoon, BiSun
} from "react-icons/bi";

import ChartPanel from "./ChartPanel.tsx";
import "./Dashboard.css";
import InsightCards from "../components/InsightCards.tsx";

const kpiData = [
  { label: "Campaigns", value: "25", icon: <BiRocket /> },
  { label: "Recipients", value: "72,910", icon: <BiUser /> },
  { label: "Sent", value: "56,910", icon: <BiEnvelope /> },
  { label: "Delivery rate", value: "74.5%", icon: <BiCheckCircle /> },
  { label: "Click through rate", value: "24.5%", icon: <BiBarChartAlt2 /> },
];

const summaryData = [
  { title: "Total revenue", value: "$512,375", change: "+2.5%" },
  { title: "Attributed revenue", value: "$486,375", change: "+10.5%" },
  { title: "Per recipient", value: "$121.36" },
  { title: "Email", value: "$61.28 / 46.84%" },
  { title: "SMS", value: "$15.21 / 12.33%" },
  { title: "WhatsApp", value: "$2.12 / 2.21%" },
];

const campaignRows = [
  { name: "Bird promotional offers", status: "Sent", type: "WhatsApp", delivers: "99.6%", revenue: "$10,235.11" },
  { name: "Festive Fiesta Frenzy", status: "Sent", type: "WhatsApp", delivers: "85.8%", revenue: "$12,894.36" },
  { name: "Celebrate with a Splash", status: "Failed", type: "Email", delivers: "—", revenue: "—" },
  { name: "Winter Wonderland Bonanza", status: "Draft", type: "Email", delivers: "—", revenue: "—" },
  { name: "Autumn Adventure Awaits", status: "Sent", type: "WhatsApp", delivers: "92.2%", revenue: "$2,645.99" },
];

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<"Overview" | "Analytics">("Overview");
  const [darkMode, setDarkMode] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const storedTheme = localStorage.getItem("darkMode");
    setDarkMode(storedTheme === "true");
  }, []);

  useEffect(() => {
    document.body.className = darkMode ? "dark-mode" : "";
    localStorage.setItem("darkMode", String(darkMode));
  }, [darkMode]);

  return (
    <div className="dashboard-layout">
      <main className="main-dashboard">
        <header className="dashboard-header">
          <h1>Dashboard</h1>
          <div className="header-actions">
            <button onClick={() => setDarkMode(!darkMode)} title="Toggle Dark Mode">
              {darkMode ? <BiSun /> : <BiMoon />}
            </button>
            <div className="tabs">
              <button
                className={activeTab === "Overview" ? "active" : ""}
                onClick={() => setActiveTab("Overview")}
              >
                Overview
              </button>
              <button
                className={activeTab === "Analytics" ? "active" : ""}
                onClick={() => setActiveTab("Analytics")}
              >
                Analytics
              </button>
            </div>
          </div>
        </header>

        {activeTab === "Overview" && (
          <>
            <section className="kpi-cards">
              {kpiData.map((kpi) => (
                <KPI key={kpi.label} label={kpi.label} value={kpi.value} icon={kpi.icon} />
              ))}
            </section>

            <section className="insight-section">
              <InsightCards />
            </section>

            <section className="summary-section">
              <div className="insight-header">
                <h2 className="insight-heading">Business Performance Summary</h2>
              </div>
              <div className="summary-grid insight-grid">
                {summaryData.map((item) => (
                  <div className="insight-card" key={item.title}>
                    <div className="insight-details">
                      <h4>{item.title}</h4>
                      <p>{item.value}</p>
                      {item.change && <p className="summary-change">({item.change})</p>}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="campaign-table">
              <h3>Top performing campaigns</h3>
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Status</th>
                    <th>Type</th>
                    <th>Delivers</th>
                    <th>Revenue</th>
                  </tr>
                </thead>
                <tbody>
                  {campaignRows.map((row) => (
                    <tr key={row.name}>
                      <td>{row.name}</td>
                      <td>
                        <span className={`status ${row.status.toLowerCase()}`}>
                          {row.status === "Sent" && <BiCheckCircle />}
                          {row.status === "Failed" && <BiErrorCircle />}
                          {row.status === "Draft" && <BiTimeFive />}
                          {row.status}
                        </span>
                      </td>
                      <td>{row.type}</td>
                      <td>{row.delivers}</td>
                      <td>{row.revenue}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </>
        )}

        {activeTab === "Analytics" && (
          <section className="analytics-section">
            <h2>Analytics</h2>
            <ChartPanel />
          </section>
        )}
      </main>
    </div>
  );
}

function KPI({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="kpi-card glass">
      <div className="kpi-icon">{icon}</div>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
    </div>
  );
}
