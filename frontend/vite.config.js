import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  base: '/static/dist/',
  plugins: [react(), tailwindcss()],
  build: {
    outDir: '../static/dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'src/main.jsx'),
      },
      output: {
        entryFileNames: 'aras.[name].js',
        chunkFileNames: 'aras.[name].[hash].js',
        assetFileNames: 'aras.[name][extname]',
      },
    },
  },
  server: {
    proxy: {
      '/api': 'http://localhost:5000',
      '/admin': 'http://localhost:5000',
    },
  },
})
