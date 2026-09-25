import React from 'react';
import AdminPanel from '../../src/components/AdminPanel/AdminPanel';

export default function App() {
  // Simple wrapper for teacher UI – theme handling can be added later
  const theme = 'light' as const;
  const toggleTheme = () => {};
  return <AdminPanel theme={theme} toggleTheme={toggleTheme} />;
}
