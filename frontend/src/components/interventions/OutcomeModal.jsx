import React, { useState } from "react";

export default function OutcomeModal({ isOpen, onClose, onSubmit, title }) {
  const [outcome, setOutcome] = useState("IMPROVED"); // IMPROVED | NO_CHANGE | DECLINED
  const [notes, setNotes] = useState("");

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ outcome, outcomeNotes: notes });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <h3 style={{ fontSize: "1.15rem", fontWeight: 700 }}>Record Intervention Outcome</h3>
          <button className="btn btn-ghost btn-icon btn-sm" onClick={onClose} style={{ border: "none", fontSize: "1.2rem" }}>
            &times;
          </button>
        </div>

        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: 16 }}>
          You are marking <strong>{title}</strong> as completed. Please record the student's response to this intervention.
        </p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Student Outcome</label>
            <div className="outcome-options">
              <button
                type="button"
                className={`outcome-btn IMPROVED ${outcome === "IMPROVED" ? "active" : ""}`}
                onClick={() => setOutcome("IMPROVED")}
              >
                <span style={{ fontSize: "1.2rem" }}>✅</span>
                <span>Improved</span>
              </button>
              <button
                type="button"
                className={`outcome-btn NO_CHANGE ${outcome === "NO_CHANGE" ? "active" : ""}`}
                onClick={() => setOutcome("NO_CHANGE")}
              >
                <span style={{ fontSize: "1.2rem" }}>➖</span>
                <span>No Change</span>
              </button>
              <button
                type="button"
                className={`outcome-btn DECLINED ${outcome === "DECLINED" ? "active" : ""}`}
                onClick={() => setOutcome("DECLINED")}
              >
                <span style={{ fontSize: "1.2rem" }}>⬇️</span>
                <span>Declined</span>
              </button>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Outcome Notes / Observations</label>
            <textarea
              className="form-input"
              rows={3}
              placeholder="Provide detail on student progress, attendance changes, or feedback..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              style={{ resize: "vertical", fontFamily: "var(--font)", fontSize: "0.85rem" }}
              required
            />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: 12, marginTop: 24 }}>
            <button type="button" className="btn btn-ghost" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              ✓ Confirm Complete
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
