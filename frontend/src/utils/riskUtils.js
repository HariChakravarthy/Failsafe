export const riskColor = (level) => {
  if (level === "HIGH") return "var(--risk-high)";
  if (level === "MEDIUM") return "var(--risk-medium)";
  return "var(--risk-low)";
};

export const riskEmoji = (level) => {
  if (level === "HIGH") return "🔴";
  if (level === "MEDIUM") return "🟡";
  return "🟢";
};

export const scoreToPercent = (score) => Math.round(score * 100);
