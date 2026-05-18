import React from "react";

const FEATURE_LABELS = {
  absences: "Absences",
  failures: "Past Failures",
  studytime: "Study Time",
  Walc: "Weekend Alcohol",
  Dalc: "Daily Alcohol",
  famsup: "Family Support",
  health: "Health Status",
  goout: "Goes Out Often",
  romantic: "Relationship",
  internet: "Internet Access",
  age: "Age",
  Medu: "Mother's Education",
  Fedu: "Father's Education",
  higher: "Aims for Higher Edu",
  schoolsup: "School Support",
  activities: "Activities",
  freetime: "Free Time",
  famrel: "Family Relations",
  traveltime: "Travel Time",
};

export default function SHAPChart({ shapValues }) {
  if (!shapValues) return null;

  const entries = Object.entries(shapValues)
    .filter(([, v]) => v !== 0)
    .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
    .slice(0, 10);

  if (entries.length === 0)
    return <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>No SHAP data available.</p>;

  const maxAbs = Math.max(...entries.map(([, v]) => Math.abs(v)));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {entries.map(([feat, val]) => {
        const pct = Math.round((Math.abs(val) / maxAbs) * 100);
        const isPositive = val > 0;
        const label = FEATURE_LABELS[feat] || feat;
        return (
          <div key={feat} className="shap-bar-row">
            <div className="shap-bar-label" title={label}>{label}</div>
            <div className="shap-bar-track">
              <div
                className={`shap-bar-fill ${isPositive ? "positive" : "negative"}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <div className="shap-bar-value" style={{ color: isPositive ? "var(--risk-high)" : "var(--risk-low)" }}>
              {isPositive ? "+" : ""}{val.toFixed(3)}
            </div>
          </div>
        );
      })}
      <div style={{ display: "flex", gap: 20, marginTop: 8, fontSize: "0.75rem", color: "var(--text-secondary)" }}>
        <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
          <span style={{ width: 12, height: 12, background: "var(--risk-high)", borderRadius: 2, display: "inline-block" }} />
          Increases risk
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
          <span style={{ width: 12, height: 12, background: "var(--risk-low)", borderRadius: 2, display: "inline-block" }} />
          Decreases risk
        </span>
      </div>
    </div>
  );
}
