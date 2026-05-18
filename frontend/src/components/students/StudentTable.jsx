import React from "react";
import { useNavigate } from "react-router-dom";
import RiskBadge from "../common/RiskBadge";
import { fmtDate } from "../../utils/formatters";

export default function StudentTable({ students, loading }) {
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className="loading-center">
        <span className="spinner spinner-lg" />
      </div>
    );
  }

  if (!students?.length) {
    return (
      <div className="empty-state">
        <div className="empty-icon">🎓</div>
        <div className="empty-title">No students found</div>
        <div className="empty-sub">Upload a CSV to get started</div>
      </div>
    );
  }

  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Student Code</th>
            <th>Name</th>
            <th>Department</th>
            <th>Semester</th>
            <th>Risk</th>
            <th>Added</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {students.map((s) => (
            <tr key={s.id}>
              <td style={{ fontFamily: "var(--font-mono)", color: "var(--accent)", fontSize: "0.82rem" }}>
                {s.student_code}
              </td>
              <td style={{ fontWeight: 600 }}>{s.name || "—"}</td>
              <td style={{ color: "var(--text-secondary)" }}>{s.department || "—"}</td>
              <td style={{ color: "var(--text-secondary)" }}>
                {s.semester ? `Sem ${s.semester}` : "—"}
              </td>
              <td>
                {s.latest_risk ? <RiskBadge level={s.latest_risk} /> : <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>Pending</span>}
              </td>
              <td style={{ color: "var(--text-secondary)", fontSize: "0.8rem" }}>{fmtDate(s.created_at)}</td>
              <td>
                <button
                  className="btn btn-ghost btn-sm"
                  id={`view-student-${s.id}`}
                  onClick={() => navigate(`/students/${s.id}`)}
                >
                  View →
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
