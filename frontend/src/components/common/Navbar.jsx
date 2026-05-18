import React from "react";

export default function Navbar({ title }) {
  return (
    <header className="navbar">
      <span className="navbar-title">{title}</span>
      <div className="navbar-actions">
        <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
          {new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" })}
        </span>
      </div>
    </header>
  );
}
