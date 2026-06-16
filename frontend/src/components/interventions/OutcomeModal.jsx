import React, { useState } from "react";
import { CheckCircle2, MinusCircle, TrendingDown, X } from "lucide-react";

const OPTIONS = [
  { value: "IMPROVED", label: "Improved", icon: CheckCircle2 },
  { value: "NO_CHANGE", label: "No Change", icon: MinusCircle },
  { value: "DECLINED", label: "Declined", icon: TrendingDown },
];

export default function OutcomeModal({ isOpen, onClose, onSubmit, title }) {
  const [outcome, setOutcome] = useState("IMPROVED");
  const [notes, setNotes] = useState("");

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ outcome, outcomeNotes: notes });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3>Record Intervention Outcome</h3>
            <p>You are marking <strong>{title}</strong> as completed.</p>
          </div>
          <button className="btn btn-ghost btn-icon btn-sm" onClick={onClose} aria-label="Close">
            <X size={17} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Student Outcome</label>
            <div className="outcome-options">
              {OPTIONS.map((option) => {
                const Icon = option.icon;
                return (
                  <button
                    key={option.value}
                    type="button"
                    className={`outcome-btn ${option.value} ${outcome === option.value ? "active" : ""}`}
                    onClick={() => setOutcome(option.value)}
                  >
                    <Icon size={20} />
                    <span>{option.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Outcome Notes / Observations</label>
            <textarea
              className="form-input"
              rows={3}
              placeholder="Describe student progress, attendance changes, or feedback..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              required
            />
          </div>

          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Confirm Complete
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
