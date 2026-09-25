import React from 'react';
import './ThemeToggle.css';

type ThemeToggleProps = {
  theme: 'light' | 'dark';
  toggleTheme: () => void;
};

export const ThemeToggle: React.FC<ThemeToggleProps> = ({ theme, toggleTheme }) => {
  return (
    <button className="theme-toggle" onClick={toggleTheme} aria-label="Toggle theme">
      Switch to {theme === 'light' ? 'Dark' : 'Light'} Mode
    </button>
  );
};
