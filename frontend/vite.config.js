import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  // Multi-page app configuration
  build: {
    rollupOptions: {
      input: {
        login: resolve(__dirname, "index.html"),
        register: resolve(__dirname, "register.html"),
        main: resolve(__dirname, "main.html"),
      },
    },
    outDir: "dist",
  },
  server: {
    port: 3000,
    open: true, // auto-open browser on dev start
    // Proxy API calls to the local Flask backend during development.
    // In production the frontend uses the full API Gateway URL directly.
    proxy: {
      "/api": {
        target: "https://imum9rqox0.execute-api.us-east-1.amazonaws.com/prod",
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
