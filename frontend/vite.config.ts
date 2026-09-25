import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    headers: {
      "X-Content-Type-Options": "nosniff",
      "X-Frame-Options": "DENY",
      "Referrer-Policy": "strict-origin-when-cross-origin",
      "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
      // Vite's React refresh preamble and dev style injection are inline. The
      // production API applies the strict CSP; this dev policy keeps local
      // development functional without broadening network origins.
      "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' http://127.0.0.1:5177; style-src 'self' 'unsafe-inline'; connect-src 'self' ws://127.0.0.1:5177 http://127.0.0.1:5177; frame-ancestors 'none'; object-src 'none'; base-uri 'self'"
    },
    proxy: {
      "/api": "http://127.0.0.1:8007",
      "/health": "http://127.0.0.1:8007"
    }
  }
  ,test: { exclude: ["e2e/**", "node_modules/**"] }
});
