import React, { useState } from "react";
import { CalendarDays, ChevronDown, LogOut, ShieldCheck } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const initials = user?.name
    ? user.name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
    : "U";

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="navbar">
      <div className="navbar-brand">
        <div className="brand-mark"><ShieldCheck size={20} /></div>
        <div>
          <div className="brand-name">FAILSAFE</div>
          <div className="brand-subtitle">Academic early warning</div>
        </div>
      </div>

      <div className="navbar-actions">
        <span className="nav-date">
          <CalendarDays size={16} />
          {new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" })}
        </span>

        <div className="user-menu">
          <button className="user-menu-trigger" onClick={() => setOpen((v) => !v)}>
            <span className="user-avatar">{initials}</span>
            <span className="user-menu-copy">
              <span className="user-name">{user?.name || "User"}</span>
              <span className="user-role">{user?.role || "faculty"}</span>
            </span>
            <ChevronDown size={16} />
          </button>

          {open && (
            <div className="user-menu-popover">
              <button onClick={handleLogout}>
                <LogOut size={16} />
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
