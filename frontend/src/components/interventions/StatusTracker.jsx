import React from "react";
import { fmtDate } from "../../utils/formatters";

const STEPS = ["PENDING", "IN_PROGRESS", "COMPLETED"];
const STEP_LABELS = { PENDING: "Pending", IN_PROGRESS: "In Progress", COMPLETED: "Completed" };

export default function StatusTracker({ interventions }) {
  if (!interventions?.length) return null;

  const counts = { PENDING: 0, IN_PROGRESS: 0, COMPLETED: 0, DISMISSED: 0 };
  interventions.forEach((iv) => { counts[iv.status] = (counts[iv.status] || 0) + 1; });
  const total = interventions.length;
  const completedPct = Math.round(((counts.COMPLETED + counts.DISMISSED) / total) * 100);

  return (
    <div>
      {/* Progress bar */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem", marginBottom: 6 }}>
          <span style={{ color: "var(--text-secondary)" }}>Overall Progress</span>
          <span style={{ fontWeight: 700, color: "var(--success)" }}>{completedPct}%</span>
        </div>
        <div style={{ height: 8, background: "var(--bg-secondary)", borderRadius: 4, overflow: "hidden" }}>
          <div style={{
            height: "100%", borderRadius: 4,
            width: `${completedPct}%`,
            background: "linear-gradient(90deg, var(--accent), var(--success))",
            transition: "width 0.6s ease",
          }} />
        </div>
      </div>

      {/* Step indicators */}
      <div style={{ display: "flex", gap: 0, marginBottom: 20 }}>
        {STEPS.map((step, i) => {
          const done = counts[step] > 0;
          return (
            <div key={step} style={{ display: "flex", alignItems: "center", flex: 1 }}>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                <div style={{
                  width: 32, height: 32, borderRadius: "50%", display: "flex", alignItems: "center",
                  justifyContent: "center", fontSize: "0.85rem", fontWeight: 700,
                  background: done ? "var(--accent-glow)" : "var(--bg-secondary)",
                  border: `2px solid ${done ? "var(--accent)" : "var(--border)"}`,
                  color: done ? "var(--accent)" : "var(--text-muted)",
                  transition: "all 0.3s",
                }}>
                  {counts[step] || i + 1}
                </div>
                <div style={{ fontSize: "0.7rem", color: "var(--text-secondary)", marginTop: 4, whiteSpace: "nowrap" }}>
                  {STEP_LABELS[step]}
                </div>
              </div>
              {i < STEPS.length - 1 && (
                <div style={{ flex: 1, height: 2, background: done ? "var(--accent)" : "var(--border)", margin: "0 4px", marginBottom: 18 }} />
              )}
            </div>
          );
        })}
      </div>

      {/* Mini list */}
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {interventions.slice(0, 4).map((iv) => (
          <div key={iv.id} style={{
            display: "flex", alignItems: "center", justifyContent: "space-between",
            padding: "8px 12px", background: "var(--bg-secondary)", borderRadius: "var(--radius-sm)",
            fontSize: "0.8rem",
          }}>
            <span style={{ fontWeight: 600, flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {iv.title}
            </span>
            <span className={`status-badge ${iv.status}`} style={{ marginLeft: 8 }}>
              {iv.status.replace("_", " ")}
            </span>
          </div>
        ))}
        {interventions.length > 4 && (
          <div style={{ fontSize: "0.78rem", color: "var(--text-secondary)", textAlign: "center", paddingTop: 4 }}>
            +{interventions.length - 4} more interventions
          </div>
        )}
      </div>
    </div>
  );
}
