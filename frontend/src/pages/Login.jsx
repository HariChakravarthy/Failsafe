import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import toast from "react-hot-toast";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState("login"); // login | demo

  const handle = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const user = await login(form.email, form.password);
      toast.success(`Welcome back, ${user.name}!`);
      navigate("/dashboard");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = () => {
    setForm({ email: "hod@failsafe.edu", password: "demo1234" });
    toast("Demo credentials filled — make sure the backend is running!", { icon: "ℹ️" });
  };

  return (
    <div className="login-page">
      <div className="login-card fade-in">
        <div className="login-logo">
          <div style={{ fontSize: "2.5rem", marginBottom: 8 }}>🛡️</div>
          <h1>FAILSAFE</h1>
          <p>Early Student Failure Detection &amp; Intervention</p>
        </div>

        <form onSubmit={submit}>
          <div className="form-group">
            <label className="form-label" htmlFor="email-input">Email</label>
            <input
              id="email-input"
              className="form-input"
              type="email"
              name="email"
              placeholder="faculty@institution.edu"
              value={form.email}
              onChange={handle}
              required
              autoFocus
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="password-input">Password</label>
            <input
              id="password-input"
              className="form-input"
              type="password"
              name="password"
              placeholder="••••••••"
              value={form.password}
              onChange={handle}
              required
            />
          </div>

          <button
            id="login-submit-btn"
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ width: "100%", justifyContent: "center", padding: "12px", marginTop: 8 }}
          >
            {loading ? <span className="spinner" /> : "Sign In →"}
          </button>
        </form>

        <hr className="divider" />

        <button
          id="demo-fill-btn"
          className="btn btn-ghost"
          onClick={fillDemo}
          style={{ width: "100%", justifyContent: "center" }}
        >
          🎭 Use Demo Credentials
        </button>

        <p style={{ textAlign: "center", fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 24 }}>
          FAILSAFE — Predict. Explain. Intervene.
        </p>
      </div>
    </div>
  );
}
