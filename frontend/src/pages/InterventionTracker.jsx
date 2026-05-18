import React, { useEffect, useState } from "react";
import Navbar from "../components/common/Navbar";
import LoadingSpinner from "../components/common/LoadingSpinner";
import { interventionsApi } from "../api/interventionsApi";
import { fmtDate } from "../utils/formatters";
import toast from "react-hot-toast";
import { useNavigate } from "react-router-dom";

const COLUMNS = [
  { key: "PENDING", label: "Pending", color: "var(--text-secondary)" },
  { key: "IN_PROGRESS", label: "In Progress", color: "var(--accent)" },
  { key: "COMPLETED", label: "Completed", color: "var(--success)" },
];

const PRIORITY_DOT = { URGENT: "var(--risk-high)", HIGH: "var(--risk-medium)", MEDIUM: "var(--accent)", LOW: "var(--text-muted)" };

export default function InterventionTracker() {
  const [allItems, setAllItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [priorityFilter, setPriorityFilter] = useState("ALL");
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    try {
      const data = await interventionsApi.list({ size: 100 });
      setAllItems(data.items || []);
    } catch {
      toast.error("Failed to load interventions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const filtered = priorityFilter === "ALL"
    ? allItems
    : allItems.filter((iv) => iv.priority === priorityFilter);

  const getCol = (status) => filtered.filter((iv) => iv.status === status);

  const updateStatus = async (id, status) => {
    try {
      await interventionsApi.updateStatus(id, status);
      toast.success(`Moved to ${status.replace("_", " ")}`);
      load();
    } catch {
      toast.error("Update failed");
    }
  };

  return (
    <>
      <Navbar title="Intervention Tracker" />
      <div className="page fade-in">
        <div className="section-header" style={{ marginBottom: 24 }}>
          <div>
            <h1 style={{ fontSize: "1.6rem", fontWeight: 800, marginBottom: 4 }}>Intervention Tracker</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
              Kanban-style board — drag statuses to update progress
            </p>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={load}>↻ Refresh</button>
        </div>

        {/* Priority filter */}
        <div className="filter-row">
          {["ALL", "URGENT", "HIGH", "MEDIUM", "LOW"].map((p) => (
            <button
              key={p}
              id={`priority-filter-${p.toLowerCase()}`}
              className={`btn btn-sm ${priorityFilter === p ? "btn-primary" : "btn-ghost"}`}
              onClick={() => setPriorityFilter(p)}
            >
              {p !== "ALL" && <span style={{ color: PRIORITY_DOT[p] }}>●</span>} {p}
            </button>
          ))}
          <span style={{ marginLeft: "auto", color: "var(--text-secondary)", fontSize: "0.8rem" }}>
            {filtered.length} interventions
          </span>
        </div>

        {loading ? (
          <LoadingSpinner center size="lg" />
        ) : (
          <div className="kanban-board">
            {COLUMNS.map((col) => {
              const items = getCol(col.key);
              return (
                <div key={col.key} className="kanban-col">
                  <div className="kanban-col-header" style={{ color: col.color }}>
                    {col.label}
                    <span className="kanban-count">{items.length}</span>
                  </div>
                  {items.length === 0 && (
                    <div style={{ textAlign: "center", padding: "20px", color: "var(--text-muted)", fontSize: "0.8rem" }}>
                      Empty
                    </div>
                  )}
                  {items.map((iv) => (
                    <div
                      key={iv.id}
                      className="kanban-card"
                      id={`kanban-card-${iv.id}`}
                      style={{ borderLeft: `3px solid ${PRIORITY_DOT[iv.priority] || "var(--border)"}` }}
                    >
                      <div className="kanban-card-title">{iv.title}</div>
                      <div className="kanban-card-student" style={{ cursor: "pointer" }}
                        onClick={() => navigate(`/students/${iv.student_id}`)}>
                        👤 View student →
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: 8 }}>
                        Due: {fmtDate(iv.due_date)}
                      </div>
                      <div className="kanban-card-footer">
                        <span style={{ fontSize: "0.7rem", color: PRIORITY_DOT[iv.priority], fontWeight: 700, textTransform: "uppercase" }}>
                          {iv.priority}
                        </span>
                        <div style={{ display: "flex", gap: 4 }}>
                          {col.key !== "IN_PROGRESS" && col.key !== "COMPLETED" && (
                            <button className="btn btn-ghost btn-sm" style={{ padding: "3px 8px", fontSize: "0.72rem" }}
                              onClick={() => updateStatus(iv.id, "IN_PROGRESS")}>
                              ▶
                            </button>
                          )}
                          {col.key !== "COMPLETED" && (
                            <button className="btn btn-primary btn-sm" style={{ padding: "3px 8px", fontSize: "0.72rem" }}
                              onClick={() => updateStatus(iv.id, "COMPLETED")}>
                              ✓
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </>
  );
}
