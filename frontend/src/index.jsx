import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#141b2d",
            color: "#e8edf5",
            border: "1px solid rgba(255,255,255,0.08)",
            fontFamily: "Inter, sans-serif",
            fontSize: "0.875rem",
          },
          success: { iconTheme: { primary: "#22c55e", secondary: "#141b2d" } },
          error: { iconTheme: { primary: "#ff4d6d", secondary: "#141b2d" } },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
);
