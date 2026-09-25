import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3001,
    fs: {
      // Allow Vite to serve files from the parent directory to import shared components
      allow: ['..']
    }
  },
  build: { outDir: '../dist-teacher' },
});
