import React from "react";

export default function LoadingSpinner({ size = "md", center = false }) {
  const cls = `spinner${size === "lg" ? " spinner-lg" : ""}`;
  if (center) return <div className="loading-center"><span className={cls} /></div>;
  return <span className={cls} />;
}
