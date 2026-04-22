import { defineConfig } from 'vite'
import tailwindcss from "@tailwindcss/vite";
import react from '@vitejs/plugin-react-swc'

// https://vite.dev/config/
export default defineConfig({
  plugins: [tailwindcss(), react()],
  server: {
    proxy: {
      // Proxy para AI API
      '/api': {
        target: process.env.VITE_APP_AI_API_BASE_URL || 'https://nabu-ai-backend-spelnuireq-uc.a.run.app',
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
      },
      // Proxy para Data API
      '/data-api': {
        target: process.env.VITE_APP_DATA_API_BASE_URL || 'https://nabu-data-backend-spelnuireq-uc.a.run.app',
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path.replace(/^\/data-api/, ''),
      }
    }
  }
})
