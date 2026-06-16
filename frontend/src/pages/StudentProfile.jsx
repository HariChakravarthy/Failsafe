import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Download, RefreshCw, UserRound } from "lucide-react";
import PageHeader from "../components/common/PageHeader";
import RiskGauge from "../components/predictions/RiskGauge";
import SHAPChart from "../components/predictions/SHAPChart";
import StatusTracker from "../components/interventions/StatusTracker";
import InterventionCard from "../components/interventions/InterventionCard";
import LoadingSpinner from "../components/common/LoadingSpinner";
import WhatIfSimulator from "../components/predictions/WhatIfSimulator";
import { studentsApi } from "../api/studentsApi";
import { predictionsApi } from "../api/predictionsApi";
import { interventionsApi } from "../api/interventionsApi";
import { fmtDate } from "../utils/formatters";
import toast from "react-hot-toast";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";

const TABS = ["Overview", "Explanation", "Simulator", "Interventions"];

export default function StudentProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [student, setStudent] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [history, setHistory] = useState([]);
  const [interventions, setInterventions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [activeTab, setActiveTab] = useState("Overview");

  const handleDownloadReport = async () => {
    setDownloading(true);
    const toastId = toast.loading("Generating PDF report...");
    try {
      const data = await studentsApi.downloadReport(student.id);
      const url = window.URL.createObjectURL(new Blob([data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${student.student_code}_report.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success("Report downloaded successfully", { id: toastId });
    } catch {
      toast.error("Failed to generate PDF report", { id: toastId });
    } finally {
      setDownloading(false);
    }
  };

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

  if (loading) return <div className="page"><LoadingSpinner center size="lg" /></div>;
  if (!student) return <div className="page"><p>Student not found.</p></div>;

  const trendData = history.map((h) => ({
    week: `W${h.week_number}`,
    "Risk %": Math.round(h.risk_score * 100),
  }));

  return (
    <div className="page fade-in">
      <PageHeader
        eyebrow="Student profile"
        title={student.name || student.student_code}
        description="Review risk level, explanation drivers, simulation options, and intervention progress."
        meta={(
          <>
            <span>{student.student_code}</span>
            {student.department && <span>{student.department}</span>}
            {student.semester && <span>Semester {student.semester}</span>}
            {student.age && <span>Age {student.age}</span>}
            <span>Added {fmtDate(student.created_at)}</span>
          </>
        )}
        actions={(
          <>
            <button className="btn btn-ghost" onClick={() => navigate("/students")}><ArrowLeft size={16} /> Back</button>
            <button className="btn btn-ghost" onClick={load}><RefreshCw size={16} /> Refresh</button>
            {prediction && (
              <button className="btn btn-primary" onClick={handleDownloadReport} disabled={downloading}>
                <Download size={16} /> Download Report
              </button>
            )}
          </>
        )}
      />

      <div className="student-profile-hero">
        <div className="student-identity-card">
          <div className="profile-avatar"><UserRound size={28} /></div>
          <div>
            <h2>{student.name || "Unnamed student"}</h2>
            <p>{student.student_code}</p>
          </div>
        </div>
        {prediction ? (
          <div className="profile-risk-strip">
            <span className={`risk-badge ${prediction.risk_level}`}>{prediction.risk_level} Risk</span>
            <strong>{Math.round(prediction.risk_score * 100)}%</strong>
            <small>Last predicted {fmtDate(prediction.predicted_at)}</small>
          </div>
        ) : (
          <div className="profile-risk-strip muted">No prediction yet</div>
        )}
      </div>

      <div className="profile-tabs">
        {TABS.map((tab) => (
          <button key={tab} className={activeTab === tab ? "active" : ""} onClick={() => setActiveTab(tab)}>
            {tab}
          </button>
        ))}
      </div>

      {activeTab === "Overview" && (
        <div className="profile-grid">
          <div className="profile-left">
            <div className="card centered-card">
              <div className="card-title">Current Risk Score</div>
              {prediction ? (
                <>
                  <RiskGauge score={prediction.risk_score} level={prediction.risk_level} />
                  <p className="summary-text">{prediction.shap_summary}</p>
                </>
              ) : (
                <div className="empty-state compact">
                  <div className="empty-title">No prediction yet</div>
                  <div className="empty-sub">Upload data to generate a risk score.</div>
                </div>
              )}
            </div>

            <div className="card">
              <div className="card-header">
                <div className="card-title">Intervention Progress</div>
                <span className="muted-text">{interventions.length} total</span>
              </div>
              <StatusTracker interventions={interventions} />
            </div>
          </div>

          <div className="profile-right">
            {trendData.length > 1 && (
              <div className="card">
                <div className="card-header">
                  <div>
                    <div className="card-title">Risk Score History</div>
                    <div className="card-subtitle">Week-over-week trend</div>
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={trendData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e8edf3" />
                    <XAxis dataKey="week" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis domain={[0, 100]} tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ background: "#fff", border: "1px solid #d9e2ec", borderRadius: 8 }} />
                    <Line type="monotone" dataKey="Risk %" stroke="#2563eb" strokeWidth={2} dot={{ fill: "#2563eb", r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
            {prediction && (
              <div className="card">
                <div className="card-header">
                  <div>
                    <div className="card-title">Explanation Preview</div>
                    <div className="card-subtitle">Top SHAP feature contributions</div>
                  </div>
                </div>
                <SHAPChart shapValues={prediction.shap_values} />
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "Explanation" && prediction && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">SHAP Feature Contributions</div>
              <div className="card-subtitle">Positive values increase predicted risk; negative values reduce it.</div>
            </div>
          </div>
          <SHAPChart shapValues={prediction.shap_values} />
        </div>
      )}

      {activeTab === "Explanation" && !prediction && (
        <div className="card">
          <div className="empty-state compact">
            <div className="empty-title">No explanation available</div>
            <div className="empty-sub">Upload current data to generate model explanations for this student.</div>
          </div>
        </div>
      )}

      {activeTab === "Simulator" && prediction && (
        <WhatIfSimulator studentId={student.id} originalPrediction={prediction} />
      )}

      {activeTab === "Simulator" && !prediction && (
        <div className="card">
          <div className="empty-state compact">
            <div className="empty-title">Simulator unavailable</div>
            <div className="empty-sub">A current prediction is required before risk scenarios can be simulated.</div>
          </div>
        </div>
      )}

      {activeTab === "Interventions" && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Intervention Plans</div>
              <div className="card-subtitle">Auto-generated from SHAP drivers</div>
            </div>
          </div>
          {interventions.length === 0 ? (
            <div className="empty-state compact">
              <div className="empty-title">No interventions yet</div>
              <div className="empty-sub">Upload student data to auto-generate plans.</div>
            </div>
          ) : (
            interventions.map((iv) => (
              <InterventionCard key={iv.id} intervention={iv} onUpdate={load} />
            ))
          )}
        </div>
      )}
    </div>
  );
}
