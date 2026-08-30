import { resolve } from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, "index.html"),
        // The service worker is built as its own entry so it lands at /sw.js
        // rather than under /assets with a content hash -- a hashed worker
        // path would change every build and never be found.
        sw: resolve(__dirname, "src/sw.ts"),
      },
      output: {
        entryFileNames: (chunk) => (chunk.name === "sw" ? "sw.js" : "assets/[name]-[hash].js"),
      },
    },
  },
  server: {
    // Dev proxies to the gateway so the memory-only token and same-origin
    // rules hold in development too. Production is genuinely same-origin: the
    // Python gateway serves dist/ at / and the socket at /ws.
    proxy: {
      "/ws": { target: "ws://127.0.0.1:8444", ws: true },
      "/api": { target: "http://127.0.0.1:8444" },
      "/healthz": { target: "http://127.0.0.1:8444" },
    },
  },
});
