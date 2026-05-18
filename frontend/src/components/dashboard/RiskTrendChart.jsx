import React from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";

export default function RiskTrendChart({ weeks }) {
  if (!weeks?.length) {
    return (
      <div className="empty-state" style={{ padding: "40px 20px" }}>
        <div className="empty-icon">📈</div>
        <div className="empty-title">No trend data yet</div>
        <div className="empty-sub">Upload data across multiple weeks to see trends</div>
      </div>
    );
  }

  const data = weeks.map((w) => ({
    name: `W${w.week_number}`,
    "Avg Risk %": Math.round(w.avg_risk_score * 100),
    "High Risk": w.high_risk_count,
    "Medium Risk": w.medium_risk_count,
  }));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="name" tick={{ fill: "var(--text-secondary)", fontSize: 12 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: "var(--text-secondary)", fontSize: 12 }} axisLine={false} tickLine={false} />
        <Tooltip
          contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text-primary)" }}
          labelStyle={{ color: "var(--accent)", fontWeight: 600 }}
        />
        <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
        <Line type="monotone" dataKey="Avg Risk %" stroke="#4f8ef7" strokeWidth={2} dot={{ fill: "#4f8ef7", r: 4 }} activeDot={{ r: 6 }} />
        <Line type="monotone" dataKey="High Risk" stroke="#ff4d6d" strokeWidth={2} dot={{ fill: "#ff4d6d", r: 4 }} strokeDasharray="5 3" />
        <Line type="monotone" dataKey="Medium Risk" stroke="#f6a623" strokeWidth={2} dot={{ fill: "#f6a623", r: 4 }} strokeDasharray="3 3" />
      </LineChart>
    </ResponsiveContainer>
  );
}
