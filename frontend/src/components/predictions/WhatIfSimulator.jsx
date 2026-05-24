import React, { useState, useEffect } from "react";
import { predictionsApi } from "../../api/predictionsApi";
import RiskGauge from "./RiskGauge";

export default function WhatIfSimulator({ studentId, originalPrediction }) {
  const raw = originalPrediction?.raw_features || {};

  // Sliders state
  const [absences, setAbsences] = useState(raw.absences !== undefined ? Number(raw.absences) : 0);
  const [studytime, setStudytime] = useState(raw.studytime !== undefined ? Number(raw.studytime) : 2);
  const [failures, setFailures] = useState(raw.failures !== undefined ? Number(raw.failures) : 0);
  const [Walc, setWalc] = useState(raw.Walc !== undefined ? Number(raw.Walc) : 1);
  const [goout, setGoout] = useState(raw.goout !== undefined ? Number(raw.goout) : 2);
  const [health, setHealth] = useState(raw.health !== undefined ? Number(raw.health) : 3);

  // Simulation result
  const [simScore, setSimScore] = useState(originalPrediction?.risk_score || 0);
  const [simLevel, setSimLevel] = useState(originalPrediction?.risk_level || "LOW");
  const [loading, setLoading] = useState(false);

  // Sync state if original prediction changes
  useEffect(() => {
    if (originalPrediction) {
      const freshRaw = originalPrediction.raw_features || {};
      setAbsences(freshRaw.absences !== undefined ? Number(freshRaw.absences) : 0);
      setStudytime(freshRaw.studytime !== undefined ? Number(freshRaw.studytime) : 2);
      setFailures(freshRaw.failures !== undefined ? Number(freshRaw.failures) : 0);
      setWalc(freshRaw.Walc !== undefined ? Number(freshRaw.Walc) : 1);
      setGoout(freshRaw.goout !== undefined ? Number(freshRaw.goout) : 2);
      setHealth(freshRaw.health !== undefined ? Number(freshRaw.health) : 3);
      setSimScore(originalPrediction.risk_score);
      setSimLevel(originalPrediction.risk_level);
    }
  }, [originalPrediction]);

  // Debounced simulation effect
  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    const timer = setTimeout(async () => {
      try {
        const result = await predictionsApi.simulate(studentId, {
          absences,
          studytime,
          failures,
          Walc,
          goout,
          health,
        });
        if (isMounted) {
          setSimScore(result.risk_score);
          setSimLevel(result.risk_level);
        }
      } catch (err) {
        console.error("Simulation failed:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }, 300);

    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [studentId, absences, studytime, failures, Walc, goout, health]);

  const handleReset = () => {
    const origRaw = originalPrediction?.raw_features || {};
    setAbsences(origRaw.absences !== undefined ? Number(origRaw.absences) : 0);
    setStudytime(origRaw.studytime !== undefined ? Number(origRaw.studytime) : 2);
    setFailures(origRaw.failures !== undefined ? Number(origRaw.failures) : 0);
    setWalc(origRaw.Walc !== undefined ? Number(origRaw.Walc) : 1);
    setGoout(origRaw.goout !== undefined ? Number(origRaw.goout) : 2);
    setHealth(origRaw.health !== undefined ? Number(origRaw.health) : 3);
  };

  const hasChanges =
    absences !== (raw.absences !== undefined ? Number(raw.absences) : 0) ||
    studytime !== (raw.studytime !== undefined ? Number(raw.studytime) : 2) ||
    failures !== (raw.failures !== undefined ? Number(raw.failures) : 0) ||
    Walc !== (raw.Walc !== undefined ? Number(raw.Walc) : 1) ||
    goout !== (raw.goout !== undefined ? Number(raw.goout) : 2) ||
    health !== (raw.health !== undefined ? Number(raw.health) : 3);

  // Formatting helper labels
  const studytimeLabels = ["< 2 hrs", "2 - 5 hrs", "5 - 10 hrs", "> 10 hrs"];
  const alcoholLabels = ["Very Low", "Low", "Moderate", "High", "Very High"];
  const gooutLabels = ["Very Low", "Low", "Moderate", "High", "Very High"];
  const healthLabels = ["Very Bad", "Bad", "Fair", "Good", "Very Good"];

  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h2 className="card-title">What-If Risk Simulator</h2>
          <p className="card-subtitle">Tweak key academic & lifestyle factors to see the simulated risk change live</p>
        </div>
        {hasChanges && (
          <button className="btn btn-ghost btn-sm" onClick={handleReset}>
            Reset Values
          </button>
        )}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 32, alignItems: "start" }}>
        {/* Sliders Form */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Absences */}
          <div className="form-group" style={{ margin: 0 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <span className="form-label" style={{ margin: 0 }}>Weekly Absences</span>
              <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--accent)" }}>{absences} days</span>
            </div>
            <input
              type="range"
              min="0"
              max="93"
              value={absences}
              onChange={(e) => setAbsences(Number(e.target.value))}
              style={{ width: "100%", height: 6, cursor: "pointer", accentColor: "var(--accent)" }}
            />
          </div>

          {/* Study Time */}
          <div className="form-group" style={{ margin: 0 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <span className="form-label" style={{ margin: 0 }}>Study Time (Weekly)</span>
              <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--accent)" }}>
                {studytimeLabels[studytime - 1] || `${studytime} / 4`}
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="4"
              value={studytime}
              onChange={(e) => setStudytime(Number(e.target.value))}
              style={{ width: "100%", height: 6, cursor: "pointer", accentColor: "var(--accent)" }}
            />
          </div>

          {/* Failures */}
          <div className="form-group" style={{ margin: 0 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <span className="form-label" style={{ margin: 0 }}>History of Failures</span>
              <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--accent)" }}>{failures} classes</span>
            </div>
            <input
              type="range"
              min="0"
              max="3"
              value={failures}
              onChange={(e) => setFailures(Number(e.target.value))}
              style={{ width: "100%", height: 6, cursor: "pointer", accentColor: "var(--accent)" }}
            />
          </div>

          {/* Weekend Alcohol */}
          <div className="form-group" style={{ margin: 0 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <span className="form-label" style={{ margin: 0 }}>Weekend Alcohol Use</span>
              <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--accent)" }}>
                {alcoholLabels[Walc - 1] || `${Walc} / 5`}
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="5"
              value={Walc}
              onChange={(e) => setWalc(Number(e.target.value))}
              style={{ width: "100%", height: 6, cursor: "pointer", accentColor: "var(--accent)" }}
            />
          </div>

          {/* Going Out */}
          <div className="form-group" style={{ margin: 0 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <span className="form-label" style={{ margin: 0 }}>Going Out with Friends</span>
              <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--accent)" }}>
                {gooutLabels[goout - 1] || `${goout} / 5`}
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="5"
              value={goout}
              onChange={(e) => setGoout(Number(e.target.value))}
              style={{ width: "100%", height: 6, cursor: "pointer", accentColor: "var(--accent)" }}
            />
          </div>

          {/* Health Status */}
          <div className="form-group" style={{ margin: 0 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <span className="form-label" style={{ margin: 0 }}>Current Health Status</span>
              <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--accent)" }}>
                {healthLabels[health - 1] || `${health} / 5`}
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="5"
              value={health}
              onChange={(e) => setHealth(Number(e.target.value))}
              style={{ width: "100%", height: 6, cursor: "pointer", accentColor: "var(--accent)" }}
            />
          </div>
        </div>

        {/* Side-by-Side Comparison */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16, height: "100%" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, background: "var(--bg-secondary)", borderRadius: "var(--radius-lg)", padding: 16, border: "1px solid var(--border)", position: "relative" }}>
            {loading && (
              <div style={{ position: "absolute", inset: 0, background: "rgba(10, 14, 26, 0.6)", backdropFilter: "blur(2px)", borderRadius: "var(--radius-lg)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 10 }}>
                <span className="spinner"></span>
              </div>
            )}
            
            {/* Original column */}
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
              <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Original Risk</div>
              <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "var(--text-primary)" }}>
                {Math.round((originalPrediction?.risk_score || 0) * 100)}%
              </div>
              <span className={`risk-badge ${originalPrediction?.risk_level || "LOW"}`}>
                {originalPrediction?.risk_level || "LOW"}
              </span>
            </div>

            {/* Separator line */}
            <div style={{ borderLeft: "1px solid var(--border)" }} />

            {/* Simulated column */}
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
              <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "var(--accent)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Simulated Risk</div>
              <div style={{ fontSize: "1.75rem", fontWeight: 800, color: simLevel === "HIGH" ? "var(--risk-high)" : simLevel === "MEDIUM" ? "var(--risk-medium)" : "var(--risk-low)" }}>
                {Math.round(simScore * 100)}%
              </div>
              <span className={`risk-badge ${simLevel}`}>
                {simLevel}
              </span>
            </div>
          </div>
          
          <div style={{ display: "flex", justifyContent: "center", padding: "10px 0" }}>
            <RiskGauge score={simScore} level={simLevel} />
          </div>
        </div>
      </div>
    </div>
  );
}
