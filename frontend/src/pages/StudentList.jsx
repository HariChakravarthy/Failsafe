import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/common/Navbar";
import StudentTable from "../components/students/StudentTable";
import RiskBadge from "../components/common/RiskBadge";
import { studentsApi } from "../api/studentsApi";
import toast from "react-hot-toast";

const RISK_FILTERS = ["ALL", "HIGH", "MEDIUM", "LOW"];

export default function StudentList() {
  const [students, setStudents] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("ALL");
  const navigate = useNavigate();
  const SIZE = 20;

  const load = async () => {
    setLoading(true);
    try {
      const params = { page, size: SIZE };
      if (search) params.search = search;
      const data = await studentsApi.list(params);
      setStudents(data.items);
      setTotal(data.total);
    } catch {
      toast.error("Failed to load students");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [page, search]);

  const filtered = riskFilter === "ALL"
    ? students
    : students.filter((s) => s.latest_risk === riskFilter);

  const totalPages = Math.ceil(total / SIZE);

  return (
    <>
      <Navbar title="Students" />
      <div className="page fade-in">
        <div className="section-header">
          <div>
            <h1 style={{ fontSize: "1.6rem", fontWeight: 800, marginBottom: 4 }}>All Students</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>{total} students in cohort</p>
          </div>
          <button className="btn btn-primary" onClick={() => navigate("/upload")}>
            📤 Upload CSV
          </button>
        </div>

        <div className="filter-row">
          <div className="search-bar" style={{ flex: 1, maxWidth: 340 }}>
            <span className="search-icon">🔍</span>
            <input
              id="student-search"
              placeholder="Search by name or code…"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            />
          </div>
          {RISK_FILTERS.map((f) => (
            <button
              key={f}
              id={`filter-${f.toLowerCase()}`}
              className={`btn btn-sm ${riskFilter === f ? "btn-primary" : "btn-ghost"}`}
              onClick={() => setRiskFilter(f)}
            >
              {f === "ALL" ? "All" : <RiskBadge level={f} />}
            </button>
          ))}
        </div>

        <div className="card">
          <StudentTable students={filtered} loading={loading} />
        </div>

        {totalPages > 1 && (
          <div className="pagination">
            <button className="page-btn" disabled={page === 1} onClick={() => setPage(p => p - 1)}>←</button>
            {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => i + 1).map((p) => (
              <button
                key={p}
                className={`page-btn${page === p ? " active" : ""}`}
                onClick={() => setPage(p)}
              >{p}</button>
            ))}
            <button className="page-btn" disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>→</button>
          </div>
        )}
      </div>
    </>
  );
}
