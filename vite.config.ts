import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// Porquê porta fixa em dev: o sidecar (core/api) libera CORS só para
// http://localhost:5173 — ver ORIGENS_DEV_PERMITIDAS em core/api/app.py.
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    strictPort: true,
  },
});
