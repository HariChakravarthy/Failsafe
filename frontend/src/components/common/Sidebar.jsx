import React from "react";
import { NavLink } from "react-router-dom";
import { ClipboardList, LayoutDashboard, UploadCloud, Users } from "lucide-react";

const links = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/students", icon: Users, label: "Students" },
  { to: "/upload", icon: UploadCloud, label: "Upload Data" },
  { to: "/interventions", icon: ClipboardList, label: "Interventions" },
];

export default function Sidebar() {
  return (
    <aside className="sidebar" aria-label="Primary navigation">
      <nav className="sidebar-nav">
        {links.map((link) => {
          const Icon = link.icon;
          return (
            <NavLink
              key={link.to}
              to={link.to}
              title={link.label}
              className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
            >
              <span className="nav-icon"><Icon size={21} /></span>
              <span className="nav-label">{link.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
