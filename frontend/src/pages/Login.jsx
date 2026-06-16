import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, GraduationCap, KeyRound, Mail, ShieldCheck, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import toast from "react-hot-toast";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);

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
    toast("Demo credentials filled. Sign in when the backend is running.", { icon: "i" });
  };

  return (
    <div className="login-page">
      <section className="login-shell">
        <div className="login-brand-panel">
          <div className="brand-lockup">
            <div className="brand-mark large"><ShieldCheck size={28} /></div>
            <div>
              <div className="brand-name large">FAILSAFE</div>
              <div className="brand-subtitle">Academic early warning</div>
            </div>
          </div>
          <div className="login-copy">
            <span className="page-eyebrow">Faculty intelligence suite</span>
            <h1>Predict risk early. Explain it clearly. Intervene in time.</h1>
            <p>
              A focused workspace for HODs and faculty to review student risk, upload weekly data, and track interventions.
            </p>
          </div>
          <div className="login-proof-grid">
            <div><GraduationCap size={18} /><span>Student profiles</span></div>
            <div><Sparkles size={18} /><span>Explainable AI</span></div>
            <div><ShieldCheck size={18} /><span>Faculty workflow</span></div>
          </div>
        </div>

        <div className="login-card fade-in">
          <div className="login-card-header">
            <h2>Sign in</h2>
            <p>Use your faculty or HOD account to continue.</p>
          </div>

          <form onSubmit={submit}>
            <div className="form-group">
              <label className="form-label" htmlFor="email-input">Email</label>
              <div className="input-with-icon">
                <Mail size={17} />
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
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="password-input">Password</label>
              <div className="input-with-icon">
                <KeyRound size={17} />
                <input
                  id="password-input"
                  className="form-input"
                  type="password"
                  name="password"
                  placeholder="Enter your password"
                  value={form.password}
                  onChange={handle}
                  required
                />
              </div>
            </div>

            <button id="login-submit-btn" type="submit" className="btn btn-primary btn-wide" disabled={loading}>
              {loading ? <span className="spinner" /> : <>Sign In <ArrowRight size={16} /></>}
            </button>
          </form>

          <div className="login-divider"><span>Demo access</span></div>

          <button id="demo-fill-btn" className="btn btn-ghost btn-wide" onClick={fillDemo}>
            Fill Demo Credentials
          </button>
        </div>
      </section>
    </div>
  );
}
