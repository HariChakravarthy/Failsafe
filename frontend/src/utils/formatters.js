export const fmtDate = (iso) =>
  iso ? new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" }) : "—";

export const fmtTime = (iso) =>
  iso ? new Date(iso).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }) : "—";

export const fmtPercent = (val) => `${Math.round(val * 100)}%`;

export const truncate = (str, n = 60) =>
  str && str.length > n ? str.slice(0, n) + "…" : str;
