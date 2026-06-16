import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { RefreshCw, Search, UploadCloud } from "lucide-react";
import PageHeader from "../components/common/PageHeader";
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
    <div className="page fade-in">
      <PageHeader
        eyebrow="Student intelligence"
        title="Students"
        description={`${total} students in the current cohort. Search, triage, and open profiles for intervention planning.`}
        actions={(
          <>
            <button className="btn btn-ghost" onClick={load}><RefreshCw size={16} /> Refresh</button>
            <button className="btn btn-primary" onClick={() => navigate("/upload")}><UploadCloud size={16} /> Upload CSV</button>
          </>
        )}
      />

      <div className="filter-toolbar">
        <div className="search-bar">
          <Search size={17} className="search-icon" />
          <input
            id="student-search"
            placeholder="Search by name or student code"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
        </div>
        <div className="segmented-control">
          {RISK_FILTERS.map((f) => (
            <button
              key={f}
              id={`filter-${f.toLowerCase()}`}
              className={riskFilter === f ? "active" : ""}
              onClick={() => setRiskFilter(f)}
            >
              {f === "ALL" ? "All Risk Levels" : <RiskBadge level={f} />}
            </button>
          ))}
        </div>
      </div>

      <div className="card table-card">
        <StudentTable students={filtered} loading={loading} />
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button className="page-btn" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>Prev</button>
          {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => i + 1).map((p) => (
            <button
              key={p}
              className={`page-btn${page === p ? " active" : ""}`}
              onClick={() => setPage(p)}
            >{p}</button>
          ))}
          <button className="page-btn" disabled={page === totalPages} onClick={() => setPage((p) => p + 1)}>Next</button>
        </div>
      )}
    </div>
  );
}
