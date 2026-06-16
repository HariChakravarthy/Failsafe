import React from "react";
import { LineChart as LineChartIcon } from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";

export default function RiskTrendChart({ weeks }) {
  if (!weeks?.length) {
    return (
      <div className="empty-state compact">
        <div className="empty-icon"><LineChartIcon size={36} /></div>
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
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e8edf3" />
        <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} />
        <Tooltip
          contentStyle={{ background: "#ffffff", border: "1px solid #d9e2ec", borderRadius: 8, color: "#0b1d3a" }}
          labelStyle={{ color: "#2563eb", fontWeight: 700 }}
        />
        <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
        <Line type="monotone" dataKey="Avg Risk %" stroke="#2563eb" strokeWidth={2} dot={{ fill: "#2563eb", r: 4 }} activeDot={{ r: 6 }} />
        <Line type="monotone" dataKey="High Risk" stroke="#e24b4b" strokeWidth={2} dot={{ fill: "#e24b4b", r: 4 }} strokeDasharray="5 3" />
        <Line type="monotone" dataKey="Medium Risk" stroke="#d9912b" strokeWidth={2} dot={{ fill: "#d9912b", r: 4 }} strokeDasharray="3 3" />
      </LineChart>
    </ResponsiveContainer>
  );
}
