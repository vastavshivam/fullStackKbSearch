import React from 'react';
import saveAs from 'file-saver';
import jsPDF from 'jspdf';

const dummyData = [
  ['Date', 'Email', 'SMS', 'WhatsApp'],
  ['2025-07-01', '400', '200', '300'],
  ['2025-07-02', '450', '220', '280'],
  ['2025-07-03', '470', '180', '310'],
];

export default function ExportButtons() {
  const exportCSV = () => {
    const csv = dummyData.map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    saveAs(blob, 'analytics.csv');
  };

  const exportPDF = () => {
    const doc = new jsPDF();
    doc.text('Analytics Data', 20, 20);
    dummyData.forEach((row, i) => {
      doc.text(row.join(' | '), 20, 30 + i * 10);
    });
    doc.save('analytics.pdf');
  };

  return (
    <div className="export-buttons">
      <button onClick={exportCSV}>Export CSV</button>
      <button onClick={exportPDF}>Export PDF</button>
    </div>
  );
}