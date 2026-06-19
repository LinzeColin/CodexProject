import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

const appDir = fileURLToPath(new URL(".", import.meta.url));
const atlasDataDir = fileURLToPath(new URL("../../data/derived/visualization", import.meta.url));

export default defineConfig({
  plugins: [react()],
  publicDir: atlasDataDir,
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    fs: {
      allow: [appDir, atlasDataDir],
    },
  },
  build: {
    sourcemap: process.env.VITE_SOURCEMAP === "1",
  },
});
