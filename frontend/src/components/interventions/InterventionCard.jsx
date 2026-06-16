import React, { useState } from "react";
import { Check, MessageSquareText, Play, X } from "lucide-react";
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
  IMPROVED: "Improved",
  NO_CHANGE: "No Change",
  DECLINED: "Declined",
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
    <div className="intervention-card" style={{ borderLeftColor: prioColor }}>
      <div className="intervention-card-header">
        <div>
          <div className="intervention-meta">
            <span style={{ color: prioColor }}>{intervention.priority}</span>
            <span className={`status-badge ${intervention.status}`}>{intervention.status.replace("_", " ")}</span>
            {intervention.status === "COMPLETED" && intervention.outcome && (
              <span className={`outcome-badge ${intervention.outcome}`}>
                {OUTCOME_LABELS[intervention.outcome] || intervention.outcome}
              </span>
            )}
          </div>
          <div className="intervention-title">{intervention.title}</div>
        </div>
        <div className="intervention-due">Due {fmtDate(intervention.due_date)}</div>
      </div>

      <p>{intervention.description}</p>

      {intervention.status === "COMPLETED" && intervention.outcome_notes && (
        <div className="outcome-note">
          <strong>Outcome notes</strong>
          <span>{intervention.outcome_notes}</span>
        </div>
      )}

      {intervention.status !== "COMPLETED" && intervention.status !== "DISMISSED" && (
        <div className="inline-actions wrap">
          {intervention.status === "PENDING" && (
            <button className="btn btn-ghost btn-sm" disabled={loading} onClick={() => updateStatus("IN_PROGRESS")}>
              <Play size={14} /> Start
            </button>
          )}
          <button className="btn btn-primary btn-sm" disabled={loading} onClick={() => setShowOutcomeModal(true)}>
            <Check size={14} /> Complete
          </button>
          <button className="btn btn-ghost btn-sm" disabled={loading} onClick={() => setShowNotes(!showNotes)}>
            <MessageSquareText size={14} /> Note
          </button>
          <button className="btn btn-danger btn-sm" disabled={loading} onClick={() => updateStatus("DISMISSED")}>
            <X size={14} /> Dismiss
          </button>
        </div>
      )}

      {showNotes && (
        <div className="note-editor">
          <textarea
            className="form-input"
            placeholder="Add a note..."
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
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
