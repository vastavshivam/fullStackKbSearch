// src/pages/ChartPanel.tsx
import React, { useState } from 'react';
import {
  Chart as ChartJS,
  LineElement,
  ArcElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend
} from 'chart.js';
import { Line, Pie } from 'react-chartjs-2';
import './ChartPanel.css';

ChartJS.register(
  LineElement,
  ArcElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend
);

const revenueLineData = {
  labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
  datasets: [
    {
      label: 'Revenue',
      data: [12000, 19000, 30000, 25000, 32000, 37000],
      fill: true,
      backgroundColor: 'rgba(29, 161, 242, 0.2)',
      borderColor: '#1DA1F2',
      tension: 0.3,
    },
  ],
};

const campaignPieData = {
  labels: ['Email', 'SMS', 'WhatsApp'],
  datasets: [
    {
      label: 'Channels',
      data: [45, 25, 30],
      backgroundColor: ['#4db5ff', '#ff9f40', '#36a2eb'],
      borderColor: ['#fff', '#fff', '#fff'],
      borderWidth: 1,
    },
  ],
};

const audienceLineData = {
  labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
  datasets: [
    {
      label: 'Audience Growth',
      data: [800, 1200, 1800, 2400, 2900, 3600],
      fill: false,
      borderColor: '#00C49F',
      tension: 0.3,
    },
  ],
};

const clickRatePieData = {
  labels: ['Clicked', 'Not Clicked'],
  datasets: [
    {
      label: 'Click Rate',
      data: [60, 40],
      backgroundColor: ['#845EC2', '#D5D5D5'],
      borderColor: ['#fff', '#fff'],
      borderWidth: 1,
    },
  ],
};

export default function ChartPanel() {
  return (
    <div className="chart-grid">
      <div className="chart-box">
        <h4>Monthly Revenue</h4>
        <Line data={revenueLineData} />
      </div>

      <div className="chart-box">
        <h4>Campaign Distribution</h4>
        <Pie data={campaignPieData} />
      </div>

      <div className="chart-box">
        <h4>Audience Growth</h4>
        <Line data={audienceLineData} />
      </div>

      <div className="chart-box">
        <h4>Click Rate</h4>
        <Pie data={clickRatePieData} />
      </div>
    </div>
  );
}
