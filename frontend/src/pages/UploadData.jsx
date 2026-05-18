import React, { useState } from "react";
import Navbar from "../components/common/Navbar";
import CSVUploader from "../components/upload/CSVUploader";
import { studentsApi } from "../api/studentsApi";
import toast from "react-hot-toast";

const REQUIRED_COLS = ["student_code", "absences", "studytime", "failures"];

export default function UploadData() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [week, setWeek] = useState(1);

  const handleFile = async (file) => {
    setLoading(true);
    setResult(null);
    try {
      const summary = await studentsApi.upload(file, week);
      setResult(summary);
      if (summary.errors?.length) {
        toast(`Upload complete with ${summary.errors.length} row errors`, { icon: "⚠️" });
      } else {
        toast.success(`✅ ${summary.total_uploaded} students processed successfully`);
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
      <div className="page fade-in" style={{ maxWidth: 800 }}>
        <div style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: "1.6rem", fontWeight: 800, marginBottom: 6 }}>Upload Student Data</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
            Upload a CSV file with student features to trigger batch risk prediction.
            Required columns: <code style={{ fontFamily: "var(--font-mono)", color: "var(--accent)" }}>{REQUIRED_COLS.join(", ")}</code>
          </p>
        </div>

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
            <div style={{ flex: 1, paddingTop: 20, fontSize: "0.8rem", color: "var(--text-secondary)" }}>
              Each upload week tracks cohort risk progression over the semester.
            </div>
          </div>
          <CSVUploader onFile={handleFile} loading={loading} />
        </div>

        {/* Column guide */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">📋 Expected CSV Format</div>
          </div>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Column</th>
                  <th>Type</th>
                  <th>Required</th>
                  <th>Example</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ["student_code", "string", "✅", "S1042"],
                  ["absences", "integer", "✅", "14"],
                  ["studytime", "integer (1–4)", "✅", "2"],
                  ["failures", "integer", "✅", "1"],
                  ["name", "string", "—", "Arjun Sharma"],
                  ["age", "integer", "—", "18"],
                  ["sex", "M / F", "—", "M"],
                  ["Walc", "integer (1–5)", "—", "3"],
                  ["famsup", "yes / no", "—", "yes"],
                  ["G1, G2, G3", "integer", "—", "12, 10, 8"],
                ].map(([col, type, req, ex]) => (
                  <tr key={col}>
                    <td style={{ fontFamily: "var(--font-mono)", color: "var(--accent)", fontSize: "0.82rem" }}>{col}</td>
                    <td style={{ color: "var(--text-secondary)", fontSize: "0.82rem" }}>{type}</td>
                    <td>{req}</td>
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
            <div className="card-title" style={{ marginBottom: 16 }}>📊 Upload Summary — Week {week}</div>
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
