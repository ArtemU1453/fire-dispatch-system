import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  server: {
    port: 5173,
    proxy: {
      // Proxy API calls to the backend in development (configurable).
      "/api": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: true,
    exclude: ["e2e/**", "node_modules/**"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/**/*.test.{ts,tsx}",
        "src/**/index.ts",
        "src/**/types/**",
        "src/test/**",
        "src/main.tsx",
        "src/vite-env.d.ts",
        // OpenLayers maps cannot render under jsdom; covered by manual QA.
        "src/features/**/components/OperationalMap.tsx",
        "src/features/**/components/RegistrationMap.tsx",
      ],
    },
  },
});
