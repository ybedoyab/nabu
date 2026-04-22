import { defineConfig } from 'vite'
import tailwindcss from "@tailwindcss/vite";
import react from '@vitejs/plugin-react-swc'

const ensureIpv4Loopback = (target: string) =>
  target.replace("://localhost", "://127.0.0.1");

// https://vite.dev/config/
export default defineConfig({
  plugins: [tailwindcss(), react()],
  server: {
    proxy: {
      // Proxy para AI API
      '/api': {
        target: ensureIpv4Loopback(process.env.VITE_APP_AI_API_BASE_URL || 'http://localhost:8000'),
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
      },
      // Proxy para Data API
      '/data-api': {
        target: ensureIpv4Loopback(process.env.VITE_APP_DATA_API_BASE_URL || 'http://localhost:8081'),
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/data-api/, ''),
      }
    }
  }
})
