import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiTarget = process.env.VITE_API_PROXY || "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 700,
    rollupOptions: {
      output: {
        manualChunks: {
          echarts: ["echarts"],
          react: ["react", "react-dom"],
          icons: ["lucide-react"]
        }
      }
    }
  },
  server: {
    port: 5173,
    proxy: {
      "/api": apiTarget
    }
  }
});
