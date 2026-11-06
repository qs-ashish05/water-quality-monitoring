import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The dev server proxies /api to the Node backend, so the browser never
// talks to the database and no CORS setup is needed.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // '/api': 'http://localhost:4000',
      "/api": {
        target: "https://wq-backend-sigma.vercel.app/",
        changeOrigin: true,
        secure: true,
      },
    },
  },
});
