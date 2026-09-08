import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import { ThemeProvider } from "./contexts/ThemeContext"; // ✅ Import the ThemeProvider

// --- GLOBAL FETCH OVERRIDE FOR PRODUCTION DEPLOYMENT ---
const backendUrl = (import.meta.env.VITE_BACKEND_URL || "").replace(/\/+$/, "");

if (backendUrl) {
  const originalFetch = window.fetch;
  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    if (typeof input === "string") {
      if (input.startsWith("/api") || input.startsWith("/auth")) {
        input = `${backendUrl}${input}`;
      }
    } else if (input instanceof URL) {
      if (input.pathname.startsWith("/api") || input.pathname.startsWith("/auth")) {
        input = new URL(`${backendUrl}${input.pathname}${input.search}`);
      }
    } else if (input instanceof Request) {
      const url = new URL(input.url);
      if (url.pathname.startsWith("/api") || url.pathname.startsWith("/auth")) {
        const newUrl = `${backendUrl}${url.pathname}${url.search}`;
        input = new Request(newUrl, input);
      }
    }
    return originalFetch(input, init);
  };
}
// ------------------------------------------------------

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider>
      <App />
    </ThemeProvider>
  </React.StrictMode>
);

