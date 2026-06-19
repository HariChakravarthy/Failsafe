import React from "react";
import { GraduationCap, UserRound } from "lucide-react";
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
        <div className="empty-icon"><GraduationCap size={42} /></div>
        <div className="empty-title">No students found</div>
        <div className="empty-sub">Upload a CSV or adjust the current filters.</div>
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
              <td className="mono-cell">{s.student_code}</td>
              <td>
                <div className="student-name-cell">
                  <span className="student-mini-avatar"><UserRound size={15} /></span>
                  <strong>{s.name || "Unnamed student"}</strong>
                </div>
              </td>
              <td>{s.department || "Not assigned"}</td>
              <td>{s.semester ? `Semester ${s.semester}` : "Not set"}</td>
              <td>
                {s.latest_risk ? <RiskBadge level={s.latest_risk} /> : <span className="muted-text">Pending</span>}
              </td>
              <td>{fmtDate(s.created_at)}</td>
              <td className="table-action-cell">
                <button
                  className="btn btn-ghost btn-sm"
                  id={`view-student-${s.id}`}
                  onClick={() => navigate(`/students/${s.id}`)}
                >
                  View Profile
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
