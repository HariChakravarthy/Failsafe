import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

const links = [
  { to: "/dashboard", icon: "📊", label: "Dashboard" },
  { to: "/students", icon: "👥", label: "Students" },
  { to: "/upload", icon: "📤", label: "Upload Data" },
  { to: "/interventions", icon: "🎯", label: "Interventions" },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const initials = user?.name
    ? user.name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
    : "U";

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon">🛡️</div>
        <div>
          <div className="logo-text">FAILSAFE</div>
          <div className="logo-sub">Early Detection</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
          >
            <span className="nav-icon">{l.icon}</span>
            {l.label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="user-card">
          <div className="user-avatar">{initials}</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="user-name" style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {user?.name || "User"}
            </div>
            <div className="user-role">{user?.role || "faculty"}</div>
          </div>
          <button
            onClick={handleLogout}
            title="Logout"
            style={{ background: "none", border: "none", cursor: "pointer", fontSize: "1rem", color: "var(--text-secondary)" }}
          >
            🚪
          </button>
        </div>
      </div>
    </aside>
  );
}
