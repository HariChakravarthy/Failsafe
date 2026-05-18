import React from "react";

export default function RiskBadge({ level }) {
  if (!level) return null;
  return <span className={`risk-badge ${level}`}>{level}</span>;
}
