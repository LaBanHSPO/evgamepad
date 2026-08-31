import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    // Dev only. Production is same-origin: the Python gateway serves the built bundle at `/`
    // and the socket at `/ws`, so the memory-only token holds with no CORS carve-out.
    proxy: {
      "/ws": { target: "ws://127.0.0.1:8444", ws: true },
      "/api": { target: "http://127.0.0.1:8444" },
      "/healthz": { target: "http://127.0.0.1:8444" },
    },
  },
  build: {
    rollupOptions: {
      input: {
        main: "index.html",
        // The worker needs a stable, unhashed name at the site root, or its scope is wrong and
        // a new deploy cannot replace it.
        sw: "src/sw.ts",
      },
      output: {
        entryFileNames: (chunk) => (chunk.name === "sw" ? "sw.js" : "assets/[name]-[hash].js"),
      },
    },
  },
});
