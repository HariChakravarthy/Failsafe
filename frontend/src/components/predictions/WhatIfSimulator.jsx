import React, { useState, useEffect } from "react";
import { RotateCcw } from "lucide-react";
import { predictionsApi } from "../../api/predictionsApi";
import RiskGauge from "./RiskGauge";

export default function WhatIfSimulator({ studentId, originalPrediction }) {
  const raw = originalPrediction?.raw_features || {};

  const [absences, setAbsences] = useState(raw.absences !== undefined ? Number(raw.absences) : 0);
  const [studytime, setStudytime] = useState(raw.studytime !== undefined ? Number(raw.studytime) : 2);
  const [failures, setFailures] = useState(raw.failures !== undefined ? Number(raw.failures) : 0);
  const [Walc, setWalc] = useState(raw.Walc !== undefined ? Number(raw.Walc) : 1);
  const [goout, setGoout] = useState(raw.goout !== undefined ? Number(raw.goout) : 2);
  const [health, setHealth] = useState(raw.health !== undefined ? Number(raw.health) : 3);

  const [simScore, setSimScore] = useState(originalPrediction?.risk_score || 0);
  const [simLevel, setSimLevel] = useState(originalPrediction?.risk_level || "LOW");
  const [loading, setLoading] = useState(false);

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

  const studytimeLabels = ["< 2 hrs", "2 - 5 hrs", "5 - 10 hrs", "> 10 hrs"];
  const alcoholLabels = ["Very Low", "Low", "Moderate", "High", "Very High"];
  const gooutLabels = ["Very Low", "Low", "Moderate", "High", "Very High"];
  const healthLabels = ["Very Bad", "Bad", "Fair", "Good", "Very Good"];

  const controls = [
    { label: "Weekly Absences", value: absences, display: `${absences} days`, min: 0, max: 93, onChange: setAbsences },
    { label: "Study Time", value: studytime, display: studytimeLabels[studytime - 1] || `${studytime} / 4`, min: 1, max: 4, onChange: setStudytime },
    { label: "History of Failures", value: failures, display: `${failures} classes`, min: 0, max: 3, onChange: setFailures },
    { label: "Weekend Alcohol Use", value: Walc, display: alcoholLabels[Walc - 1] || `${Walc} / 5`, min: 1, max: 5, onChange: setWalc },
    { label: "Going Out with Friends", value: goout, display: gooutLabels[goout - 1] || `${goout} / 5`, min: 1, max: 5, onChange: setGoout },
    { label: "Current Health Status", value: health, display: healthLabels[health - 1] || `${health} / 5`, min: 1, max: 5, onChange: setHealth },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">What-If Risk Simulator</div>
          <div className="card-subtitle">Adjust key academic and lifestyle factors to preview simulated risk changes.</div>
        </div>
        {hasChanges && (
          <button className="btn btn-ghost btn-sm" onClick={handleReset}>
            <RotateCcw size={14} /> Reset Values
          </button>
        )}
      </div>

      <div className="simulator-grid">
        <div className="slider-stack">
          {controls.map((control) => (
            <div className="form-group" key={control.label}>
              <div className="slider-row">
                <span className="form-label">{control.label}</span>
                <span className="slider-value">{control.display}</span>
              </div>
              <input
                type="range"
                min={control.min}
                max={control.max}
                value={control.value}
                onChange={(e) => control.onChange(Number(e.target.value))}
                style={{ width: "100%", accentColor: "var(--accent)" }}
              />
            </div>
          ))}
        </div>

        <div>
          <div className="comparison-panel">
            {loading && <div className="loading-overlay"><span className="spinner" /></div>}
            <div className="comparison-cell">
              <div className="comparison-label">Original Risk</div>
              <div className="comparison-score">{Math.round((originalPrediction?.risk_score || 0) * 100)}%</div>
              <span className={`risk-badge ${originalPrediction?.risk_level || "LOW"}`}>
                {originalPrediction?.risk_level || "LOW"}
              </span>
            </div>
            <div className="comparison-cell">
              <div className="comparison-label">Simulated Risk</div>
              <div
                className="comparison-score"
                style={{ color: simLevel === "HIGH" ? "var(--risk-high)" : simLevel === "MEDIUM" ? "var(--risk-medium)" : "var(--risk-low)" }}
              >
                {Math.round(simScore * 100)}%
              </div>
              <span className={`risk-badge ${simLevel}`}>{simLevel}</span>
            </div>
          </div>

          <div style={{ display: "flex", justifyContent: "center", paddingTop: 18 }}>
            <RiskGauge score={simScore} level={simLevel} />
          </div>
        </div>
      </div>
    </div>
  );
}
