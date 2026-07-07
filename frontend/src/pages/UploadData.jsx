import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { BarChart3, CheckCircle2, Clock3, FileSpreadsheet, ListChecks, UploadCloud } from "lucide-react";
import PageHeader from "../components/common/PageHeader";
import CSVUploader from "../components/upload/CSVUploader";
import { studentsApi } from "../api/studentsApi";
import toast from "react-hot-toast";

const PHASES = [
  {
    value: 0,
    label: "Before Term 1",
    description: "Earliest warning using attendance, study habits, family background, and lifestyle signals.",
    requiredGrades: [],
    color: "low",
  },
  {
    value: 1,
    label: "Between Term 1 & Term 2",
    description: "Use after Term 1 results are available. Include G1 for stronger prediction quality.",
    requiredGrades: ["G1"],
    color: "medium",
  },
  {
    value: 2,
    label: "After Term 2",
    description: "Use after Term 2 results are available. Include G1 and G2 for the final pre-exam window.",
    requiredGrades: ["G1", "G2"],
    color: "high",
  },
];

const REQUIRED_ROWS = [
  ["student_code", "Student identifier", "S1042"],
  ["absences", "Integer", "14"],
  ["studytime", "1 to 4", "2"],
  ["failures", "Integer", "1"],
  ["G1", "Phase 1 and 2", "12"],
  ["G2", "Phase 2 only", "10"],
];

export default function UploadData() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [week, setWeek] = useState(1);
  const [phase, setPhase] = useState(0);
  const navigate = useNavigate();

  const selectedPhase = PHASES.find((p) => p.value === phase);

  const handleFile = async (file) => {
    setLoading(true);
    setResult(null);
    try {
      const summary = await studentsApi.upload(file, week, phase);
      setResult(summary);
      if (summary.errors?.length) {
        toast(`Upload complete with ${summary.errors.length} row errors`, { icon: "!" });
      } else {
        toast.success(`${summary.total_uploaded} students processed`);
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page fade-in">
      <PageHeader
        eyebrow="Data intake"
        title="Upload Student Data"
        description="Process a classroom CSV, stamp it by week, and generate current risk predictions."
      />

      <div className="upload-layout">
        <div className="upload-main">
          <div className="card upload-card">
            <div className="card-header">
              <div>
                <div className="card-title">CSV Upload</div>
                <div className="card-subtitle">Drop a CSV file to process students for Week {week}</div>
              </div>
              <span className={`phase-pill ${selectedPhase.color}`}>{selectedPhase.label}</span>
            </div>
            <CSVUploader onFile={handleFile} loading={loading} />
          </div>

          {result && (
            <div className="card upload-result-card">
              <div className="card-header">
                <div>
                  <div className="card-title">Upload Summary</div>
                  <div className="card-subtitle">Week {week} / {selectedPhase.label}</div>
                </div>
                <CheckCircle2 size={24} className="success-icon" />
              </div>
              <div className="stats-grid compact">
                <div className="stat-card navy"><div className="stat-value">{result.total_uploaded}</div><div className="stat-label">Processed</div></div>
                <div className="stat-card high"><div className="stat-value">{result.high_risk}</div><div className="stat-label">High Risk</div></div>
                <div className="stat-card medium"><div className="stat-value">{result.medium_risk}</div><div className="stat-label">Medium Risk</div></div>
                <div className="stat-card low"><div className="stat-value">{result.low_risk}</div><div className="stat-label">Low Risk</div></div>
              </div>
              {result.errors?.length > 0 && (
                <div className="error-list">
                  <strong>{result.errors.length} row errors</strong>
                  {result.errors.map((e, i) => <span key={i}>{e}</span>)}
                </div>
              )}
              <div className="result-actions">
                <button className="btn btn-primary" onClick={() => navigate("/students")}>View Students</button>
                <button className="btn btn-ghost" onClick={() => navigate("/dashboard")}>Go to Dashboard</button>
              </div>
            </div>
          )}
        </div>

        <aside className="setup-panel">
          <div className="panel-section">
            <div className="panel-heading"><Clock3 size={17} /> Upload Week</div>
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

          <div className="panel-section">
            <div className="panel-heading"><BarChart3 size={17} /> Prediction Phase</div>
            <div className="phase-stack">
              {PHASES.map((p) => (
                <button
                  key={p.value}
                  className={`phase-card ${phase === p.value ? "active" : ""}`}
                  onClick={() => setPhase(p.value)}
                >
                  <span className={`phase-dot ${p.color}`} />
                  <span>
                    <strong>{p.label}</strong>
                    <small>{p.description}</small>
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="panel-section">
            <div className="panel-heading"><ListChecks size={17} /> CSV Checklist</div>
            <div className="checklist">
              {REQUIRED_ROWS.map(([col, type, ex]) => (
                <div key={col} className="checklist-row">
                  <FileSpreadsheet size={15} />
                  <span><strong>{col}</strong><small>{type} / e.g. {ex}</small></span>
                </div>
              ))}
            </div>
          </div>

          <div className="note-panel">
            <UploadCloud size={18} />
            <p>
              The upload uses the existing backend endpoint and stores predictions immediately after processing.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
