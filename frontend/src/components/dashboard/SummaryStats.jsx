import React from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";

const COLORS = ["#ff4d6d", "#f6a623", "#2dd4bf"];

export default function SummaryStats({ summary }) {
  if (!summary) return null;

  const { risk_distribution: rd, intervention_stats: iv, total_students, high_risk_percentage } = summary;

  const pieData = [
    { name: "High Risk", value: rd.high },
    { name: "Medium Risk", value: rd.medium },
    { name: "Low Risk", value: rd.low },
  ].filter((d) => d.value > 0);

  return (
    <div>
      <div className="stats-grid" style={{ marginBottom: 24 }}>
        <div className="stat-card">
          <div className="stat-value">{total_students}</div>
          <div className="stat-label">Total Students</div>
          <div className="stat-icon">🎓</div>
        </div>
        <div className="stat-card high">
          <div className="stat-value" style={{ color: "var(--risk-high)" }}>{rd.high}</div>
          <div className="stat-label">High Risk</div>
          <div className="stat-icon">🔴</div>
        </div>
        <div className="stat-card medium">
          <div className="stat-value" style={{ color: "var(--risk-medium)" }}>{rd.medium}</div>
          <div className="stat-label">Medium Risk</div>
          <div className="stat-icon">🟡</div>
        </div>
        <div className="stat-card low">
          <div className="stat-value" style={{ color: "var(--risk-low)" }}>{rd.low}</div>
          <div className="stat-label">Low Risk</div>
          <div className="stat-icon">🟢</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: "var(--warning)" }}>{iv.pending}</div>
          <div className="stat-label">Interventions Pending</div>
          <div className="stat-icon">⏳</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: "var(--success)" }}>{iv.completed}</div>
          <div className="stat-label">Completed</div>
          <div className="stat-icon">✅</div>
        </div>
      </div>

      {pieData.length > 0 && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Risk Distribution</div>
              <div className="card-subtitle">Current cohort snapshot</div>
            </div>
            <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "var(--risk-high)" }}>
              {high_risk_percentage}% at-risk
            </div>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={4} dataKey="value">
                {pieData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i]} stroke="transparent" />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8 }}
                labelStyle={{ color: "var(--text-primary)" }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
