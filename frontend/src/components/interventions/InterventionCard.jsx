import React, { useState } from "react";
import { interventionsApi } from "../../api/interventionsApi";
import toast from "react-hot-toast";
import { fmtDate } from "../../utils/formatters";
import OutcomeModal from "./OutcomeModal";

const PRIORITY_COLOR = {
  URGENT: "var(--risk-high)",
  HIGH: "var(--risk-medium)",
  MEDIUM: "var(--accent)",
  LOW: "var(--text-secondary)",
};

const OUTCOME_LABELS = {
  IMPROVED: "Improved ✅",
  NO_CHANGE: "No Change ➖",
  DECLINED: "Declined ⬇️",
};

export default function InterventionCard({ intervention, onUpdate }) {
  const [loading, setLoading] = useState(false);
  const [notes, setNotes] = useState(intervention.notes || "");
  const [showNotes, setShowNotes] = useState(false);
  const [showOutcomeModal, setShowOutcomeModal] = useState(false);

  const updateStatus = async (status, outcome = undefined, outcomeNotes = undefined) => {
    setLoading(true);
    try {
      await interventionsApi.updateStatus(
        intervention.id,
        status,
        notes || undefined,
        outcome,
        outcomeNotes
      );
      toast.success(`Marked as ${status.replace("_", " ")}`);
      onUpdate?.();
    } catch {
      toast.error("Failed to update status");
    } finally {
      setLoading(false);
    }
  };

  const handleOutcomeSubmit = async ({ outcome, outcomeNotes }) => {
    setShowOutcomeModal(false);
    await updateStatus("COMPLETED", outcome, outcomeNotes);
  };

  const prioColor = PRIORITY_COLOR[intervention.priority] || "var(--text-secondary)";

  return (
    <div className="card" style={{ marginBottom: 16, borderLeft: `3px solid ${prioColor}` }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4, flexWrap: "wrap" }}>
            <span style={{ fontSize: "0.72rem", fontWeight: 700, color: prioColor, textTransform: "uppercase", letterSpacing: "0.05em" }}>
              {intervention.priority}
            </span>
            <span className={`status-badge ${intervention.status}`}>{intervention.status.replace("_", " ")}</span>
            {intervention.status === "COMPLETED" && intervention.outcome && (
              <span className={`outcome-badge ${intervention.outcome}`}>
                {OUTCOME_LABELS[intervention.outcome] || intervention.outcome}
              </span>
            )}
          </div>
          <div style={{ fontWeight: 700, fontSize: "0.95rem" }}>{intervention.title}</div>
        </div>
        <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", whiteSpace: "nowrap", marginLeft: 12 }}>
          Due: {fmtDate(intervention.due_date)}
        </div>
      </div>

      <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", lineHeight: 1.6, marginBottom: 14 }}>
        {intervention.description}
      </p>

      {intervention.status === "COMPLETED" && intervention.outcome_notes && (
        <div style={{ marginTop: 8, padding: "8px 12px", background: "var(--bg-secondary)", borderRadius: "var(--radius-sm)", borderLeft: "2px solid var(--border-accent)" }}>
          <div style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", marginBottom: 2 }}>Outcome Notes</div>
          <p style={{ fontSize: "0.78rem", color: "var(--text-primary)", fontStyle: "italic", margin: 0 }}>
            "{intervention.outcome_notes}"
          </p>
        </div>
      )}

      {intervention.status !== "COMPLETED" && intervention.status !== "DISMISSED" && (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 14 }}>
          {intervention.status === "PENDING" && (
            <button className="btn btn-ghost btn-sm" disabled={loading} onClick={() => updateStatus("IN_PROGRESS")}>
              ▶ Start
            </button>
          )}
          <button className="btn btn-primary btn-sm" disabled={loading} onClick={() => setShowOutcomeModal(true)}>
            ✓ Complete
          </button>
          <button className="btn btn-ghost btn-sm" disabled={loading} onClick={() => setShowNotes(!showNotes)}>
            📝 Note
          </button>
          <button className="btn btn-danger btn-sm" disabled={loading} onClick={() => updateStatus("DISMISSED")}>
            Dismiss
          </button>
        </div>
      )}

      {showNotes && (
        <div style={{ marginTop: 12 }}>
          <textarea
            className="form-input"
            placeholder="Add a note…"
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            style={{ resize: "vertical", fontFamily: "var(--font)" }}
          />
        </div>
      )}

      <OutcomeModal
        isOpen={showOutcomeModal}
        onClose={() => setShowOutcomeModal(false)}
        onSubmit={handleOutcomeSubmit}
        title={intervention.title}
      />
    </div>
  );
}
