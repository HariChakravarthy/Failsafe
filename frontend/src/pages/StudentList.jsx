import React, { useEffect, useState, useCallback, useRef } from "react";
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
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("ALL");
  const navigate = useNavigate();
  const SIZE = 20;
  const debounceTimer = useRef(null);

  // Debounce search input (300ms)
  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearch(val);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      setDebouncedSearch(val);
      setPage(1);
    }, 300);
  };

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
    };
  }, []);

  const load = async () => {
    setLoading(true);
    try {
      const params = { page, size: SIZE };
      if (debouncedSearch) params.search = debouncedSearch;
      if (riskFilter !== "ALL") params.risk_level = riskFilter;
      const data = await studentsApi.list(params);
      setStudents(data.items);
      setTotal(data.total);
    } catch {
      toast.error("Failed to load students");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [page, debouncedSearch, riskFilter]);

  const totalPages = Math.ceil(total / SIZE);

  // Build pagination buttons with ellipsis for large page counts
  const getPaginationButtons = () => {
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }
    const pages = [];
    pages.push(1);
    if (page > 3) pages.push("...");
    for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) {
      pages.push(i);
    }
    if (page < totalPages - 2) pages.push("...");
    pages.push(totalPages);
    return pages;
  };

  return (
    <>
      <Navbar title="Students" />
      <div className="page fade-in">
        <div className="section-header">
          <div>
            <h1 style={{ fontSize: "1.6rem", fontWeight: 800, marginBottom: 4 }}>All Students</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>{total} students{riskFilter !== "ALL" ? ` (${riskFilter} risk)` : " in cohort"}</p>
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
              onChange={handleSearchChange}
            />
          </div>
          {RISK_FILTERS.map((f) => (
            <button
              key={f}
              id={`filter-${f.toLowerCase()}`}
              className={`btn btn-sm ${riskFilter === f ? "btn-primary" : "btn-ghost"}`}
              onClick={() => { setRiskFilter(f); setPage(1); }}
            >
              {f === "ALL" ? "All" : <RiskBadge level={f} />}
            </button>
          ))}
        </div>

        <div className="card">
          <StudentTable students={students} loading={loading} />
        </div>

        {totalPages > 1 && (
          <div className="pagination">
            <button className="page-btn" disabled={page === 1} onClick={() => setPage(p => p - 1)}>←</button>
            {getPaginationButtons().map((p, idx) =>
              p === "..." ? (
                <span key={`ellipsis-${idx}`} className="page-btn" style={{ cursor: "default", opacity: 0.5 }}>…</span>
              ) : (
                <button
                  key={p}
                  className={`page-btn${page === p ? " active" : ""}`}
                  onClick={() => setPage(p)}
                >{p}</button>
              )
            )}
            <button className="page-btn" disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>→</button>
          </div>
        )}
      </div>
    </>
  );
}
