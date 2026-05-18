import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Navbar from "../components/common/Navbar";
import RiskGauge from "../components/predictions/RiskGauge";
import SHAPChart from "../components/predictions/SHAPChart";
import StatusTracker from "../components/interventions/StatusTracker";
import InterventionCard from "../components/interventions/InterventionCard";
import LoadingSpinner from "../components/common/LoadingSpinner";
import { studentsApi } from "../api/studentsApi";
import { predictionsApi } from "../api/predictionsApi";
import { interventionsApi } from "../api/interventionsApi";
import { fmtDate } from "../utils/formatters";
import toast from "react-hot-toast";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";

export default function StudentProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [student, setStudent] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [history, setHistory] = useState([]);
  const [interventions, setInterventions] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [s, iv] = await Promise.all([
        studentsApi.get(id),
        interventionsApi.getByStudent(id).catch(() => ({ items: [] })),
      ]);
      setStudent(s);
      setInterventions(iv.items || []);

      const [pred, hist] = await Promise.all([
        predictionsApi.getLatest(id).catch(() => null),
        predictionsApi.getHistory(id).catch(() => ({ history: [] })),
      ]);
      setPrediction(pred);
      setHistory(hist.history || []);
    } catch {
      toast.error("Failed to load student profile");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [id]);

  if (loading) return <><Navbar title="Student Profile" /><LoadingSpinner center size="lg" /></>;
  if (!student) return <><Navbar title="Not Found" /><div className="page"><p>Student not found.</p></div></>;

  const trendData = history.map((h) => ({
    week: `W${h.week_number}`,
    "Risk %": Math.round(h.risk_score * 100),
  }));

  return (
    <>
      <Navbar title="Student Profile" />
      <div className="page fade-in">
        {/* Header */}
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 24 }}>
          <div>
            <button className="btn btn-ghost btn-sm" style={{ marginBottom: 10 }} onClick={() => navigate("/students")}>
              ← Back
            </button>
            <h1 style={{ fontSize: "1.8rem", fontWeight: 800 }}>{student.name || student.student_code}</h1>
            <div style={{ display: "flex", gap: 16, marginTop: 6, flexWrap: "wrap" }}>
              <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                🆔 <code style={{ fontFamily: "var(--font-mono)", color: "var(--accent)" }}>{student.student_code}</code>
              </span>
              {student.department && <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>🏛️ {student.department}</span>}
              {student.semester && <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>📚 Semester {student.semester}</span>}
              {student.age && <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>🎂 Age {student.age}</span>}
              <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>📅 Added {fmtDate(student.created_at)}</span>
            </div>
          </div>
        </div>

        <div className="profile-grid">
          {/* Left column */}
          <div className="profile-left">
            {/* Risk gauge */}
            <div className="card" style={{ textAlign: "center" }}>
              <div className="card-title" style={{ marginBottom: 20 }}>Current Risk Score</div>
              {prediction ? (
                <>
                  <RiskGauge score={prediction.risk_score} level={prediction.risk_level} />
                  <hr className="divider" />
                  <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", lineHeight: 1.7, textAlign: "left" }}>
                    {prediction.shap_summary}
                  </p>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 8, textAlign: "left" }}>
                    Last predicted: {fmtDate(prediction.predicted_at)}
                  </div>
                </>
              ) : (
                <div className="empty-state" style={{ padding: "20px" }}>
                  <div className="empty-icon">🔮</div>
                  <div className="empty-title">No prediction yet</div>
                  <div className="empty-sub">Upload data to generate a risk score</div>
                </div>
              )}
            </div>

            {/* Intervention tracker */}
            <div className="card">
              <div className="card-header">
                <div className="card-title">Intervention Progress</div>
                <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                  {interventions.length} total
                </span>
              </div>
              <StatusTracker interventions={interventions} />
            </div>
          </div>

          {/* Right column */}
          <div className="profile-right">
            {/* SHAP chart */}
            {prediction && (
              <div className="card">
                <div className="card-header">
                  <div>
                    <div className="card-title">SHAP Feature Contributions</div>
                    <div className="card-subtitle">Why this student was flagged</div>
                  </div>
                </div>
                <SHAPChart shapValues={prediction.shap_values} />
              </div>
            )}

            {/* Risk history */}
            {trendData.length > 1 && (
              <div className="card">
                <div className="card-header">
                  <div className="card-title">Risk Score History</div>
                  <div className="card-subtitle">Week-over-week trend</div>
                </div>
                <ResponsiveContainer width="100%" height={180}>
                  <LineChart data={trendData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="week" tick={{ fill: "var(--text-secondary)", fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis domain={[0, 100]} tick={{ fill: "var(--text-secondary)", fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8 }} />
                    <Line type="monotone" dataKey="Risk %" stroke="#4f8ef7" strokeWidth={2} dot={{ fill: "#4f8ef7", r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Interventions */}
            <div className="card">
              <div className="card-header">
                <div className="card-title">Intervention Plans</div>
                <div className="card-subtitle">Auto-generated from SHAP drivers</div>
              </div>
              {interventions.length === 0 ? (
                <div className="empty-state" style={{ padding: "30px" }}>
                  <div className="empty-icon">🎯</div>
                  <div className="empty-title">No interventions yet</div>
                  <div className="empty-sub">Upload student data to auto-generate plans</div>
                </div>
              ) : (
                interventions.map((iv) => (
                  <InterventionCard key={iv.id} intervention={iv} onUpdate={load} />
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
