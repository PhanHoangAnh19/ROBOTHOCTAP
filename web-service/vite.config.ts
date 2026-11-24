import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'

// Backend FastAPI của nhóm BE (mặc định cổng 8000).
const API = process.env.VITE_API_URL || 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  server: {
    port: 5173,
    // Proxy để trình duyệt gọi cùng origin, không vướng CORS
    proxy: {
      '/events': API,
      '/sensor-event': API,
      '/ask-ai': API,
    },
  },
})
