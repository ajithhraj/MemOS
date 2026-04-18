import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks: {
          graph: ["react-force-graph-2d"],
          charts: ["recharts"],
        },
      },
    },
  },
});
