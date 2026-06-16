import React from "react";
import { AlertTriangle, CheckCircle2, Clock3, UsersRound } from "lucide-react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";

const COLORS = {
  "High Risk": "#e24b4b",
  "Medium Risk": "#d9912b",
  "Low Risk": "#169c89",
};

export default function SummaryStats({ summary }) {
  if (!summary) return null;

  const { risk_distribution: rd, intervention_stats: iv, total_students, high_risk_percentage } = summary;

  const pieData = [
    { name: "High Risk", value: rd.high },
    { name: "Medium Risk", value: rd.medium },
    { name: "Low Risk", value: rd.low },
  ].filter((d) => d.value > 0);

  const cards = [
    { label: "Total Students", value: total_students, icon: UsersRound, tone: "navy" },
    { label: "High Risk", value: rd.high, icon: AlertTriangle, tone: "high" },
    { label: "Medium Risk", value: rd.medium, icon: Clock3, tone: "medium" },
    { label: "Low Risk", value: rd.low, icon: CheckCircle2, tone: "low" },
    { label: "Pending Actions", value: iv.pending, icon: Clock3, tone: "peach" },
    { label: "Completed", value: iv.completed, icon: CheckCircle2, tone: "success" },
  ];

  return (
    <div>
      <div className="stats-grid">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.label} className={`stat-card ${card.tone}`}>
              <div className="stat-icon"><Icon size={22} /></div>
              <div className="stat-value">{card.value}</div>
              <div className="stat-label">{card.label}</div>
            </div>
          );
        })}
      </div>

      {pieData.length > 0 && (
        <div className="card risk-distribution-card">
          <div className="card-header">
            <div>
              <div className="card-title">Risk Distribution</div>
              <div className="card-subtitle">Current cohort snapshot</div>
            </div>
            <div className="risk-percentage">{high_risk_percentage}%</div>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={88} paddingAngle={3} dataKey="value">
                {pieData.map((entry) => (
                  <Cell key={entry.name} fill={COLORS[entry.name]} stroke="transparent" />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: "#ffffff", border: "1px solid #d9e2ec", borderRadius: 8, color: "#0b1d3a" }}
                labelStyle={{ color: "#0b1d3a" }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
