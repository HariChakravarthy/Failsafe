import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { RefreshCw, UploadCloud, Users } from "lucide-react";
import PageHeader from "../components/common/PageHeader";
import SummaryStats from "../components/dashboard/SummaryStats";
import RiskTrendChart from "../components/dashboard/RiskTrendChart";
import LoadingSpinner from "../components/common/LoadingSpinner";
import { dashboardApi, interventionsApi } from "../api/interventionsApi";
import { fmtDate } from "../utils/formatters";
import toast from "react-hot-toast";

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [trends, setTrends] = useState(null);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    try {
      const [s, t, iv] = await Promise.all([
        dashboardApi.summary(),
        dashboardApi.trends(),
        interventionsApi.list({ size: 5 }).catch(() => ({ items: [] })),
      ]);
      setSummary(s);
      setTrends(t);
      setRecent(iv.items || []);
    } catch {
      toast.error("Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="page fade-in">
      <PageHeader
        eyebrow="Command center"
        title="Academic Risk Dashboard"
        description="Monitor cohort risk, spot emerging patterns, and move quickly from insight to intervention."
        actions={(
          <>
            <button className="btn btn-ghost" onClick={load}><RefreshCw size={16} /> Refresh</button>
            <button className="btn btn-ghost" onClick={() => navigate("/students")}><Users size={16} /> View Students</button>
            <button className="btn btn-primary" onClick={() => navigate("/upload")}><UploadCloud size={16} /> Upload CSV</button>
          </>
        )}
      />

      {loading ? (
        <LoadingSpinner center size="lg" />
      ) : (
        <>
          <div className="dashboard-hero">
            <div>
              <span className="hero-kicker">Live cohort snapshot</span>
              <h2>{summary?.high_risk_percentage || 0}% high-risk concentration</h2>
              <p>
                Use the weekly trend and intervention queue to decide where faculty attention should go next.
              </p>
            </div>
            <div className="hero-actions">
              <button className="btn btn-light" onClick={() => navigate("/upload")}><UploadCloud size={16} /> Add new data</button>
              <button className="btn btn-navy" onClick={() => navigate("/interventions")}>Review actions</button>
            </div>
          </div>

          <SummaryStats summary={summary} />

          <div className="dashboard-grid">
            <div className="card chart-card">
              <div className="card-header">
                <div>
                  <div className="card-title">Weekly Risk Trend</div>
                  <div className="card-subtitle">Cohort average failure probability per upload week</div>
                </div>
              </div>
              <RiskTrendChart weeks={trends?.weeks || []} />
            </div>

            <div className="card recent-card">
              <div className="card-header">
                <div>
                  <div className="card-title">Recent Interventions</div>
                  <div className="card-subtitle">Latest faculty action items</div>
                </div>
              </div>
              {recent.length === 0 ? (
                <div className="empty-state compact">
                  <div className="empty-title">No interventions yet</div>
                  <div className="empty-sub">Upload student data to generate plans.</div>
                </div>
              ) : (
                <div className="recent-list">
                  {recent.map((item) => (
                    <button key={item.id} className="recent-item" onClick={() => navigate(`/students/${item.student_id}`)}>
                      <span>
                        <strong>{item.title}</strong>
                        <small>{item.priority || "LOW"} priority / Due {fmtDate(item.due_date)}</small>
                      </span>
                      <span className={`status-badge ${item.status}`}>{item.status.replace("_", " ")}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
