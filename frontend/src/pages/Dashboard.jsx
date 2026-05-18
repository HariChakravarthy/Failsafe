import React, { useEffect, useState } from "react";
import Navbar from "../components/common/Navbar";
import SummaryStats from "../components/dashboard/SummaryStats";
import RiskTrendChart from "../components/dashboard/RiskTrendChart";
import LoadingSpinner from "../components/common/LoadingSpinner";
import { dashboardApi } from "../api/interventionsApi";
import toast from "react-hot-toast";

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [s, t] = await Promise.all([dashboardApi.summary(), dashboardApi.trends()]);
      setSummary(s);
      setTrends(t);
    } catch (err) {
      toast.error("Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <>
      <Navbar title="Dashboard" />
      <div className="page fade-in">
        {loading ? (
          <LoadingSpinner center size="lg" />
        ) : (
          <>
            <div className="section-header" style={{ marginBottom: 24 }}>
              <div>
                <h1 style={{ fontSize: "1.6rem", fontWeight: 800, marginBottom: 4 }}>
                  Overview
                </h1>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
                  Real-time cohort risk snapshot and intervention tracking
                </p>
              </div>
              <button className="btn btn-ghost btn-sm" onClick={load}>↻ Refresh</button>
            </div>

            <SummaryStats summary={summary} />

            <div className="card" style={{ marginTop: 20 }}>
              <div className="card-header">
                <div>
                  <div className="card-title">Weekly Risk Trend</div>
                  <div className="card-subtitle">Cohort average failure probability per upload week</div>
                </div>
              </div>
              <RiskTrendChart weeks={trends?.weeks || []} />
            </div>
          </>
        )}
      </div>
    </>
  );
}
