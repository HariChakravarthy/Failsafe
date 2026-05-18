import React from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

const COLORS = { HIGH: "#ff4d6d", MEDIUM: "#f6a623", LOW: "#2dd4bf" };
const NEEDLE_R = 10;

export default function RiskGauge({ score, level }) {
  const pct = Math.round((score || 0) * 100);

  // Simple arc-style gauge using SVG
  const angle = -135 + (pct / 100) * 270;
  const rad = (angle * Math.PI) / 180;
  const cx = 110, cy = 110, r = 80;
  const nx = cx + r * Math.cos(rad);
  const ny = cy + r * Math.sin(rad);

  const arcColor = COLORS[level] || "#4f8ef7";

  const data = [
    { name: "risk", value: pct },
    { name: "rest", value: 100 - pct },
  ];

  return (
    <div className="gauge-wrapper">
      <div style={{ position: "relative", width: 220, height: 140 }}>
        {/* Background arc */}
        <svg width="220" height="140" viewBox="0 0 220 140" style={{ position: "absolute", top: 0, left: 0 }}>
          {/* Track */}
          <path
            d="M 30 110 A 80 80 0 1 1 190 110"
            fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="18" strokeLinecap="round"
          />
          {/* Filled portion */}
          <path
            d="M 30 110 A 80 80 0 1 1 190 110"
            fill="none"
            stroke={arcColor}
            strokeWidth="18"
            strokeLinecap="round"
            strokeDasharray={`${(pct / 100) * 251} 251`}
            style={{ transition: "stroke-dasharray 0.8s cubic-bezier(0.22,1,0.36,1)", opacity: 0.85 }}
          />
          {/* Needle */}
          <circle cx={nx} cy={ny} r={NEEDLE_R} fill={arcColor} style={{ filter: `drop-shadow(0 0 6px ${arcColor})` }} />
          <circle cx={110} cy={110} r={6} fill="var(--bg-card)" stroke={arcColor} strokeWidth={2} />
        </svg>

        {/* Center text */}
        <div style={{
          position: "absolute", bottom: 0, left: 0, right: 0,
          textAlign: "center", paddingBottom: 8,
        }}>
          <div style={{ fontSize: "2rem", fontWeight: 800, color: arcColor, lineHeight: 1 }}>{pct}%</div>
          <div style={{ fontSize: "0.72rem", color: "var(--text-secondary)", marginTop: 2 }}>Failure Probability</div>
        </div>
      </div>

      <span className={`risk-badge ${level}`} style={{ fontSize: "0.85rem", padding: "5px 16px" }}>
        {level} RISK
      </span>
    </div>
  );
}
