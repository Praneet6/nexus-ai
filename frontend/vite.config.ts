import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://backend:8000', // 🔄 Changed from localhost to backend
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://backend:8000', // 🔄 Changed from localhost to backend
        changeOrigin: true,
      },
      '/health': {
        target: 'http://backend:8000', // 🔄 Changed from localhost to backend
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://backend:8000',   // 🔄 Changed from localhost to backend
        ws: true,
        changeOrigin: true,
      },
    },
  },
})