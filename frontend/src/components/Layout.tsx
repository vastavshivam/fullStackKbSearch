import React from 'react';

export default function Layout({ children }) {
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <main style={{ flex: 1 }}>{children}</main>
    </div>
  );
}
