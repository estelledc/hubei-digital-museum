import tailwindcss from '@tailwindcss/postcss';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import { fileURLToPath } from 'node:url';
const base = process.env.MUSEUM_BASE_PATH || '';
export default defineConfig({
  base: `${base}/`,
  css: { postcss: { plugins: [tailwindcss()] } },
  resolve: { alias: { '@': fileURLToPath(new URL('.', import.meta.url)) } },
  define: { 'process.env.NEXT_PUBLIC_BASE_PATH': JSON.stringify(base) },
  plugins: [react()],
  build: { outDir: 'dist/client' },
});
