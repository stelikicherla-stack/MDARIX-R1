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
      "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'"
    },
    proxy: {
      "/api": "http://127.0.0.1:8007",
      "/health": "http://127.0.0.1:8007"
    }
  }
  ,test: { exclude: ["e2e/**", "node_modules/**"] }
});
