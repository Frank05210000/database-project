import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 前端所有 /api 請求轉給 FastAPI 後端（docker compose 中為 http://backend:8000）
const target = process.env.VITE_PROXY_TARGET || 'http://localhost:8001'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: { '/api': { target, changeOrigin: true } },
  },
})
