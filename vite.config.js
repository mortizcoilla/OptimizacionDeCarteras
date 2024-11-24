import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    open: true, // Abrir automáticamente en el navegador
  },
  build: {
    outDir: 'dist', // Directorio de salida
  },
});
