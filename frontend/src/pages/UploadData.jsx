import React, { useState } from "react";
import Navbar from "../components/common/Navbar";
import CSVUploader from "../components/upload/CSVUploader";
import { studentsApi } from "../api/studentsApi";
import toast from "react-hot-toast";

const REQUIRED_COLS = ["student_code", "absences", "studytime", "failures"];

const PHASES = [
  {
    value: 0,
    label: "Before Term 1",
    icon: "🌱",
    description: "Use this at the start of the semester before any exams. Prediction is based on attendance, study habits, family background, and lifestyle — no grades needed.",
    requiredGrades: [],
    hint: "Earliest possible warning — catch at-risk students before the first exam.",
    color: "var(--risk-low)",
    csvNote: "G1 and G2 columns are not needed.",
  },
  {
    value: 1,
    label: "Between Term 1 & Term 2",
    icon: "📈",
    description: "Use this after Term 1 results are out. Include the Term 1 grade (G1) in your CSV along with behavioural data for a more accurate prediction.",
    requiredGrades: ["G1"],
    hint: "Good time to intervene — students can still recover before Term 2.",
    color: "var(--risk-medium)",
    csvNote: "CSV must include G1 column (Term 1 grade, 0–20).",
  },
  {
    value: 2,
    label: "After Term 2",
    icon: "🎯",
    description: "Use this after Term 2 results are out. Include both G1 and G2 in your CSV. This gives the most accurate prediction before the final exam.",
    requiredGrades: ["G1", "G2"],
    hint: "Most accurate prediction — final window before the end-semester exam.",
    color: "#a855f7",
    csvNote: "CSV must include both G1 (Term 1) and G2 (Term 2) columns (0–20).",
  },
];

export default function UploadData() {
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState(null);
  const [week, setWeek]       = useState(1);
  const [phase, setPhase]     = useState(0);

  const selectedPhase = PHASES[phase];

  const handleFile = async (file) => {
    setLoading(true);
    setResult(null);
    try {
      const summary = await studentsApi.upload(file, week, phase);
      setResult(summary);
      if (summary.errors?.length) {
        toast(`Upload complete with ${summary.errors.length} row errors`, { icon: "⚠️" });
      } else {
        toast.success(`✅ ${summary.total_uploaded} students processed (Phase ${phase})`);
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar title="Upload Data" />
      <div className="page fade-in" style={{ maxWidth: 860 }}>
        <div style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: "1.6rem", fontWeight: 800, marginBottom: 6 }}>Upload Student Data</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
            Upload a CSV with student features to trigger batch risk prediction. Choose the prediction
            phase that matches where you are in the semester.
          </p>
        </div>

        {/* Phase Selector */}
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-header">
            <div className="card-title">⚙️ Prediction Phase</div>
          </div>
          <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginBottom: 16 }}>
            Select which phase you are in. The system uses a different trained model per phase —
            adding grade data progressively improves accuracy while keeping behavioural signals as the core.
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
            {PHASES.map((p) => (
              <button
                key={p.value}
                onClick={() => setPhase(p.value)}
                style={{
                  background: phase === p.value ? "var(--bg-card-hover)" : "var(--bg-card)",
                  border: `2px solid ${phase === p.value ? p.color : "var(--border)"}`,
                  borderRadius: 12,
                  padding: "16px 14px",
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "all 0.2s ease",
                  boxShadow: phase === p.value ? `0 0 0 3px ${p.color}22` : "none",
                }}
              >
                <div style={{ fontSize: "1.5rem", marginBottom: 6 }}>{p.icon}</div>
                <div style={{ fontWeight: 700, fontSize: "0.88rem", color: "var(--text-primary)", marginBottom: 6 }}>
                  {p.label}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: 1.55, marginBottom: 8 }}>
                  {p.description}
                </div>
                <div style={{ fontSize: "0.72rem", color: p.color, fontWeight: 600, fontStyle: "italic" }}>
                  {p.hint}
                </div>
              </button>
            ))}
          </div>

          {/* Selected phase detail strip */}
          <div style={{
            marginTop: 16, padding: "10px 14px",
            background: "var(--bg-elevated)", borderRadius: 8,
            fontSize: "0.8rem", display: "flex", alignItems: "center", gap: 10,
            border: `1px solid ${selectedPhase.color}44`,
          }}>
            <span style={{ fontSize: "1.1rem" }}>{selectedPhase.icon}</span>
            <span style={{ color: "var(--text-secondary)" }}>
              <strong style={{ color: "var(--text-primary)" }}>Selected:</strong>{" "}
              {selectedPhase.label} — {selectedPhase.csvNote}
              {selectedPhase.requiredGrades.length > 0 && (
                <span style={{ marginLeft: 8, color: selectedPhase.color, fontWeight: 600 }}>
                  Required in CSV: {selectedPhase.requiredGrades.join(", ")}
                </span>
              )}
              {selectedPhase.requiredGrades.length === 0 && (
                <span style={{ marginLeft: 8, color: selectedPhase.color, fontWeight: 600 }}>
                  No grade columns needed
                </span>
              )}
            </span>
          </div>
        </div>

        {/* Upload card */}
        <div className="card" style={{ marginBottom: 20 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 20 }}>
            <div className="form-group" style={{ margin: 0, minWidth: 160 }}>
              <label className="form-label" htmlFor="week-select">Upload Week</label>
              <select
                id="week-select"
                className="form-select"
                value={week}
                onChange={(e) => setWeek(Number(e.target.value))}
              >
                {Array.from({ length: 16 }, (_, i) => (
                  <option key={i + 1} value={i + 1}>Week {i + 1}</option>
                ))}
              </select>
            </div>
            <div style={{ flex: 1, paddingTop: 20, fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
              <strong style={{ color: "var(--text-primary)" }}>What is this?</strong> Each upload is stamped with a week number.
              The dashboard uses these stamps to plot how cohort risk changes week by week — so you can see if interventions are working.
            </div>
          </div>
          <CSVUploader onFile={handleFile} loading={loading} />
        </div>

        {/* CSV Format Guide */}
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-header">
            <div className="card-title">📋 CSV Format</div>
          </div>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Column</th>
                  <th>Type</th>
                  <th>Phase 0</th>
                  <th>Phase 1</th>
                  <th>Phase 2</th>
                  <th>Example</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ["student_code", "string",         "✅", "✅", "✅", "S1042"],
                  ["absences",     "integer",         "✅", "✅", "✅", "14"],
                  ["studytime",    "integer (1–4)",   "✅", "✅", "✅", "2"],
                  ["failures",     "integer",         "✅", "✅", "✅", "1"],
                  ["Walc",         "integer (1–5)",   "—",  "—",  "—",  "3"],
                  ["famsup",       "yes / no",        "—",  "—",  "—",  "yes"],
                  ["G1",           "integer (0–20)",  "ignored", "✅", "✅", "12"],
                  ["G2",           "integer (0–20)",  "ignored", "ignored", "✅", "10"],
                ].map(([col, type, p0, p1, p2, ex]) => (
                  <tr key={col}>
                    <td style={{ fontFamily: "var(--font-mono)", color: "var(--accent)", fontSize: "0.82rem" }}>{col}</td>
                    <td style={{ color: "var(--text-secondary)", fontSize: "0.82rem" }}>{type}</td>
                    <td style={{ textAlign: "center", fontSize: "0.8rem" }}>{p0}</td>
                    <td style={{ textAlign: "center", fontSize: "0.8rem" }}>{p1}</td>
                    <td style={{ textAlign: "center", fontSize: "0.8rem" }}>{p2}</td>
                    <td style={{ color: "var(--text-secondary)", fontSize: "0.82rem" }}>{ex}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Result */}
        {result && (
          <div className="card fade-in" style={{ marginTop: 20, borderColor: "var(--border-accent)" }}>
            <div className="card-title" style={{ marginBottom: 16 }}>
              📊 Upload Summary — Week {week} · {selectedPhase.icon} {selectedPhase.label}
              <span style={{ fontSize: "0.75rem", fontWeight: 400, color: "var(--text-secondary)", marginLeft: 10 }}>
                (predictions stored in DB)
              </span>
            </div>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-value">{result.total_uploaded}</div>
                <div className="stat-label">Students Processed</div>
              </div>
              <div className="stat-card high">
                <div className="stat-value" style={{ color: "var(--risk-high)" }}>{result.high_risk}</div>
                <div className="stat-label">High Risk</div>
              </div>
              <div className="stat-card medium">
                <div className="stat-value" style={{ color: "var(--risk-medium)" }}>{result.medium_risk}</div>
                <div className="stat-label">Medium Risk</div>
              </div>
              <div className="stat-card low">
                <div className="stat-value" style={{ color: "var(--risk-low)" }}>{result.low_risk}</div>
                <div className="stat-label">Low Risk</div>
              </div>
            </div>
            {result.errors?.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--risk-high)", marginBottom: 8 }}>
                  ⚠️ {result.errors.length} Row Errors
                </div>
                {result.errors.map((e, i) => (
                  <div key={i} style={{ fontSize: "0.78rem", color: "var(--text-secondary)", fontFamily: "var(--font-mono)", paddingBottom: 4 }}>
                    {e}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}
