import { fileURLToPath, URL } from 'node:url';

import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// Em dev o Vite faz proxy de /api para a API (seção 8.1). No container "web" de
// produção quem faz o proxy é o Nginx (seção 10.4). API_PROXY_DESTINO permite
// apontar para o serviço "api" do Compose quando o dev server roda em container.
const destinoApi = process.env.API_PROXY_DESTINO ?? 'http://localhost:8100';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      '/api': {
        target: destinoApi,
        changeOrigin: true,
      },
    },
  },
});
