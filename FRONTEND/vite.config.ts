import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    watch: {
      // Necesario en Docker sobre Windows: los eventos de filesystem
      // no se propagan al contenedor, hay que usar polling
      usePolling: true,
      interval: 500,
    },
  },
})
