import React, { useEffect, useState } from 'react';
import AdminPanel from '../../frontend/src/components/AdminPanel/AdminPanel';
import { ThemeToggle } from "../../frontend/src/components/ThemeToggle/ThemeToggle";

export default function App() {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const saved = localStorage.getItem('theme') as 'light' | 'dark' | null;
    return saved || 'dark';
  });

  const toggleTheme = () => {
    setTheme(prev => {
      const newTheme = prev === 'dark' ? 'light' : 'dark';
      localStorage.setItem('theme', newTheme);
      return newTheme;
    });
  };

  useEffect(() => {
    document.body.dataset.theme = theme;
  }, [theme]);

  return <>
    <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
    <AdminPanel theme={theme} toggleTheme={toggleTheme} />
  </>;
}
