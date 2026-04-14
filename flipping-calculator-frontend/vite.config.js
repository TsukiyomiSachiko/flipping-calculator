/* eslint-disable no-undef */
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// API target: set VITE_API_TARGET env var to override (e.g. when backend runs on Windows host)
const apiTarget = process.env.VITE_API_TARGET || 'http://127.0.0.1:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true, // Listen on all addresses
    watch: {
      usePolling: true, // Enable if running in Docker/WSL or having issues
    },
    hmr: {
      overlay: true, // Show errors in browser overlay
    },
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
        secure: false,
      },
    },
  },
})