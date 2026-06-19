import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Check, Play, RefreshCw, UserRound } from "lucide-react";
import PageHeader from "../components/common/PageHeader";
import LoadingSpinner from "../components/common/LoadingSpinner";
import { interventionsApi } from "../api/interventionsApi";
import { fmtDate } from "../utils/formatters";
import toast from "react-hot-toast";
import OutcomeModal from "../components/interventions/OutcomeModal";

const COLUMNS = [
  { key: "PENDING", label: "Pending", color: "var(--text-secondary)" },
  { key: "IN_PROGRESS", label: "In Progress", color: "var(--accent)" },
  { key: "COMPLETED", label: "Completed", color: "var(--success)" },
];

const PRIORITY_DOT = { URGENT: "var(--risk-high)", HIGH: "var(--risk-medium)", MEDIUM: "var(--accent)", LOW: "var(--text-muted)" };

const OUTCOME_LABELS = {
  IMPROVED: "Improved",
  NO_CHANGE: "No Change",
  DECLINED: "Declined",
};

export default function InterventionTracker() {
  const [allItems, setAllItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [priorityFilter, setPriorityFilter] = useState("ALL");
  const [completingItem, setCompletingItem] = useState(null);
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    try {
      const data = await interventionsApi.list({ size: 500 });
      setAllItems(data.items || []);
    } catch {
      toast.error("Failed to load interventions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const filtered = priorityFilter === "ALL"
    ? allItems
    : allItems.filter((iv) => iv.priority === priorityFilter);

  const getCol = (status) => filtered.filter((iv) => iv.status === status);

  const updateStatus = async (id, status) => {
    try {
      await interventionsApi.updateStatus(id, status);
      toast.success(`Moved to ${status.replace("_", " ")}`);
      load();
    } catch {
      toast.error("Update failed");
    }
  };

  return (
    <div className="page fade-in">
      <PageHeader
        eyebrow="Action management"
        title="Intervention Tracker"
        description="Prioritize student support and move interventions from pending to completed."
        actions={<button className="btn btn-ghost" onClick={load}><RefreshCw size={16} /> Refresh</button>}
      />

      <div className="filter-toolbar">
        <div className="segmented-control">
          {["ALL", "URGENT", "HIGH", "MEDIUM", "LOW"].map((p) => (
            <button
              key={p}
              id={`priority-filter-${p.toLowerCase()}`}
              className={priorityFilter === p ? "active" : ""}
              onClick={() => setPriorityFilter(p)}
            >
              {p !== "ALL" && <span className="priority-dot" style={{ background: PRIORITY_DOT[p] }} />} {p === "ALL" ? "All Priorities" : p}
            </button>
          ))}
        </div>
        <span className="toolbar-count">{filtered.length} interventions</span>
      </div>

      {loading ? (
        <LoadingSpinner center size="lg" />
      ) : (
        <div className="kanban-board">
          {COLUMNS.map((col) => {
            const items = getCol(col.key);
            return (
              <div key={col.key} className="kanban-col">
                <div className="kanban-col-header" style={{ color: col.color }}>
                  {col.label}
                  <span className="kanban-count">{items.length}</span>
                </div>
                {items.length === 0 && (
                  <div className="empty-state compact">
                    <div className="empty-sub">No items here.</div>
                  </div>
                )}
                {items.map((iv) => (
                  <div
                    key={iv.id}
                    className="kanban-card"
                    id={`kanban-card-${iv.id}`}
                    style={{ borderLeft: `3px solid ${PRIORITY_DOT[iv.priority] || "var(--border)"}` }}
                  >
                    <div className="kanban-card-title">{iv.title}</div>
                    {iv.status === "COMPLETED" && iv.outcome && (
                      <div style={{ marginBottom: 8 }}>
                        <span className={`outcome-badge ${iv.outcome}`}>
                          {OUTCOME_LABELS[iv.outcome] || iv.outcome}
                        </span>
                      </div>
                    )}
                    <button className="kanban-card-student" onClick={() => navigate(`/students/${iv.student_id}`)}>
                      <UserRound size={14} /> View student
                    </button>
                    <div className="kanban-due">Due {fmtDate(iv.due_date)}</div>
                    <div className="kanban-card-footer">
                      <span className="priority-label" style={{ color: PRIORITY_DOT[iv.priority] }}>
                        {iv.priority}
                      </span>
                      <div className="inline-actions">
                        {col.key !== "IN_PROGRESS" && col.key !== "COMPLETED" && (
                          <button className="btn btn-ghost btn-icon btn-sm" title="Start" onClick={() => updateStatus(iv.id, "IN_PROGRESS")}>
                            <Play size={14} />
                          </button>
                        )}
                        {col.key !== "COMPLETED" && (
                          <button className="btn btn-primary btn-icon btn-sm" title="Complete" onClick={() => setCompletingItem(iv)}>
                            <Check size={14} />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      )}

      <OutcomeModal
        isOpen={!!completingItem}
        onClose={() => setCompletingItem(null)}
        onSubmit={async ({ outcome, outcomeNotes }) => {
          const item = completingItem;
          setCompletingItem(null);
          try {
            await interventionsApi.updateStatus(item.id, "COMPLETED", undefined, outcome, outcomeNotes);
            toast.success("Marked as completed");
            load();
          } catch {
            toast.error("Failed to complete intervention");
          }
        }}
        title={completingItem?.title || ""}
      />
    </div>
  );
}
