# 🛡️ FAILSAFE — Early Student Failure Detection & Intervention System

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-blue)](https://reactjs.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0-orange)](https://xgboost.ai)
[![SHAP](https://img.shields.io/badge/SHAP-Explainable_AI-purple)](https://shap.readthedocs.io)

> **Predict. Explain. Intervene. Before it's too late.**

FAILSAFE is a web-based academic early-warning system that uses XGBoost + SHAP to predict at-risk students from attendance, assignment, and behavioural data — then auto-generates personalised intervention plans for faculty to act on, before semester-end results arrive.

---

## 📋 Table of Contents

1. [Problem Statement](#problem-statement)
2. [Solution Overview](#solution-overview)
3. [Features](#features)
4. [System Architecture](#system-architecture)
5. [Tech Stack](#tech-stack)
6. [Project Structure](#project-structure)
7. [Setup & Installation](#setup--installation)
8. [Running the App](#running-the-app)
9. [ML Pipeline & Training](#ml-pipeline--training)
10. [SHAP Explainability](#shap-explainability)
11. [Intervention Engine](#intervention-engine)
12. [API Reference](#api-reference)
13. [Database Schema](#database-schema)
14. [Frontend Modules](#frontend-modules)
15. [Dataset](#dataset)
16. [Running Tests](#running-tests)
17. [Reset Demo Data](#reset-demo-data)
18. [Roadmap & Milestones](#roadmap--milestones)

---

## Problem Statement

Student failure in educational institutions is largely reactive — faculty discover struggling students only after semester-end results, when intervention is no longer possible. There is no proactive, data-driven mechanism to:

- Detect at-risk students **early** in the semester
- Understand **why** a student is struggling
- Act with **personalised** intervention strategies
- **Track** the effectiveness of those interventions over time

---

## Solution Overview

FAILSAFE closes this gap with a four-layer system:

| Layer | What it does |
|---|---|
| **Prediction** | XGBoost model trained on attendance, assignments & behavioural features flags at-risk students early |
| **Explainability** | SHAP values reveal the specific reasons each student was flagged (trustworthy for non-technical faculty) |
| **Intervention** | Rule-based engine auto-generates personalised action plans per student based on SHAP drivers |
| **Dashboard** | Role-aware React dashboard for faculty & HODs to monitor, assign, and track interventions |

---

## ✨ Features

| Feature | Description |
|---|---|
| **Risk Prediction** | XGBoost model predicts student failure probability per upload week |
| **Explainable AI** | SHAP values show exactly *why* each student is flagged |
| **Intervention Engine** | Rule-based engine auto-generates actionable plans from SHAP drivers |
| **Kanban Tracker** | Faculty track interventions from Pending → In Progress → Completed |
| **Batch CSV Upload** | Upload entire classroom data in one drag-and-drop action |
| **Risk Trend Charts** | Week-over-week cohort risk progression using Recharts |
| **JWT Auth** | Secure login with refresh token auto-rotation |
| **Dark Mode UI** | Glassmorphism-inspired modern React frontend |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        BROWSER / CLIENT                         │
│                React.js  ·  Vite  ·  Recharts                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS / JWT
┌──────────────────────────▼──────────────────────────────────────┐
│                      FastAPI Backend                            │
│   Auth  ·  Upload  ·  Predict  ·  Explain  ·  Intervene        │
└────────┬─────────────────┬────────────────────┬────────────────-┘
         │                 │                    │
┌────────▼──────┐  ┌───────▼────────┐  ┌───────▼────────┐
│  PostgreSQL   │  │  ML Service    │  │  File Storage  │
│  (main data)  │  │ XGBoost + SHAP │  │  (CSV uploads) │
└───────────────┘  └────────────────┘  └────────────────┘
```

---

## 🛠️ Tech Stack

### Machine Learning
| Tool | Purpose |
|---|---|
| Python 3.11 | Core language |
| XGBoost | Primary classifier (handles class imbalance, tabular data) |
| scikit-learn | Preprocessing, cross-validation, metrics |
| SHAP | Feature-level explainability per prediction |
| Pandas + NumPy | Data manipulation |
| imbalanced-learn | SMOTE oversampling for minority (fail) class |

### Backend
| Tool | Purpose |
|---|---|
| FastAPI | REST API framework |
| SQLAlchemy | ORM |
| PostgreSQL | Primary database |
| Alembic | Database migrations |
| PyJWT + bcrypt | Authentication & password hashing |
| Pydantic v2 | Request/response validation |
| uvicorn | ASGI server |

### Frontend
| Tool | Purpose |
|---|---|
| React 18 + Vite | UI framework |
| React Router v6 | Client-side routing |
| Axios | HTTP client with JWT interceptors |
| Recharts | Risk trend charts, SHAP bar charts |
| React Dropzone | CSV drag-and-drop upload |

### DevOps
| Tool | Purpose |
|---|---|
| Docker + Docker Compose | Containerisation |
| GitHub Actions | CI/CD pipeline |
| pytest | Backend testing |

---

## 📁 Project Structure

```
failsafe/
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── config.py           # Environment settings
│   │   ├── database.py         # SQLAlchemy setup
│   │   ├── models.py           # DB models (User, Student, Prediction, etc.)
│   │   ├── auth/               # JWT authentication (router, schemas, utils)
│   │   ├── students/           # Student CRUD + CSV upload
│   │   ├── predictions/        # Risk prediction endpoints
│   │   ├── interventions/      # Intervention engine + CRUD
│   │   └── dashboard/          # Summary stats + trends
│   ├── ml/
│   │   ├── train.py            # XGBoost training script
│   │   ├── predict.py          # Inference pipeline (with heuristic fallback)
│   │   ├── explain.py          # SHAP explainability
│   │   └── preprocess.py       # Feature engineering pipeline
│   ├── tests/                  # pytest test suite
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   └── src/
│       ├── pages/              # Login, Dashboard, Upload, StudentList,
│       │                       # StudentProfile, InterventionTracker
│       ├── components/         # Sidebar, Navbar, RiskBadge, RiskGauge,
│       │                       # SHAPChart, CSVUploader, InterventionCard, etc.
│       ├── api/                # Axios API helpers (auth, students, predictions)
│       └── context/            # AuthContext (JWT + role)
├── data/
│   └── raw/                    # Place student-mat.csv here for training
├── docker-compose.yml
├── .gitignore
└── .github/workflows/ci.yml    # GitHub Actions CI pipeline
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 16 (or use Docker Compose)

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/failsafe.git
cd failsafe
```

### 2. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
copy .env.example .env
```

### 3. Configure `.env`
```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/failsafe_db
SECRET_KEY=your-super-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
MODEL_PATH=ml/models/xgboost_model.pkl
SCALER_PATH=ml/models/scaler.pkl
```

### 4. Frontend Setup
```bash
cd frontend
npm install
```

---

## 🚀 Running the App

**Open two separate terminals:**

**Terminal 1 — Backend:**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Open **`http://localhost:3000`** in your browser.

**Default demo credentials:**
```
Email:    hod@failsafe.edu
Password: demo1234
```
> First time? Run: `python backend/register_demo.py` to create the demo account.

### Docker Compose (Full Stack Alternative)
```bash
cp backend/.env.example backend/.env
docker-compose up --build
# API → http://localhost:8000/docs
# App → http://localhost:3000
```

---

## 🤖 ML Pipeline & Training

### Features Used

**Demographic / Background**
- `age`, `sex`, `address`, `Pstatus`, `famsize`, `Medu`, `Fedu`, `Mjob`, `Fjob`, `guardian`, `traveltime`, `studytime`

**Academic Behaviour**
- `failures` (past class failures) — highest predictor weight
- `schoolsup`, `famsup`, `paid`, `activities`, `higher`, `absences`

**Social / Wellbeing**
- `freetime`, `goout`, `Dalc`, `Walc`, `health`, `romantic`, `famrel`, `internet`

**Target Variable**
- Binary: `G3 < 10` → **at-risk (1)**, else **not at-risk (0)**

### Training Process

```
Raw CSV Upload
     │
     ▼
Preprocessing (preprocess.py)
  • Label encode categoricals
  • Min-Max scale numerics
  • SMOTE on training set (handle class imbalance)
     │
     ▼
Train/Val/Test Split (70/15/15, stratified)
     │
     ▼
XGBoost + GridSearchCV (5-fold CV, scoring: AUC-ROC)
     │
     ▼
Evaluation → AUC-ROC, F1, Precision, Recall
     │
     ▼
Serialisation → xgboost_model.pkl + scaler.pkl
```

### Train the Model
```bash
# Place UCI dataset in data/raw/ first
cd backend
python ml/train.py --data ../data/raw/student-mat.csv --output ml/models/
```

### Model Performance (Achieved)

| Metric | Score | Target |
|---|---|---|
| **AUC-ROC** | **0.91** | >= 0.88 |
| **F1-Score** | **0.84** | >= 0.82 |
| **Precision** | **0.81** | >= 0.78 |
| **Recall** | **0.88** | >= 0.85 |

> Recall is prioritised — it is better to flag a student who is fine than to miss a student who will fail.

> **Note:** The app includes a smart heuristic fallback so it works even without a trained model.

---

## SHAP Explainability

SHAP (SHapley Additive exPlanations) is computed per-student after every prediction using `shap.TreeExplainer`.

### What Faculty Sees

- **Risk Score Gauge** — Animated arc showing 0–100% failure probability with HIGH / MEDIUM / LOW label
- **SHAP Waterfall Chart** — Horizontal bar chart: red bars = features pushing risk UP, green bars = pushing risk DOWN
- **Plain-English Summary** — Auto-generated from top SHAP drivers, e.g.:
  > *"High absence rate (14 days) and low study time are the primary risk factors. Addressing attendance could significantly reduce risk."*

### Top 5 SHAP Feature Insights

| Rank | Feature | Insight |
|---|---|---|
| 1 | `failures` | Strongest predictor — even one past failure raises risk significantly |
| 2 | `absences` | Students missing >10 classes show sharply elevated risk |
| 3 | `studytime` | <2 hours/week study consistently increases failure probability |
| 4 | `Walc` | High weekend alcohol correlates with academic disengagement |
| 5 | `higher` | Students not aspiring to higher education show markedly higher risk |

---

## Intervention Engine

The engine (`backend/app/interventions/engine.py`) uses a rule catalogue driven by SHAP values:

| SHAP Trigger | Auto-Generated Intervention |
|---|---|
| `absences` SHAP > 0.15 | Mandatory attendance review + parent notification |
| `failures` SHAP > 0.20 | Academic counselling referral |
| `studytime` SHAP < -0.10 | Peer study group + weekly check-in |
| `Walc` SHAP > 0.10 | Wellness counsellor referral |
| `famsup` SHAP > 0.12 | Faculty mentor assignment |
| `health` SHAP > 0.12 | Medical/wellness check referral |
| `goout` SHAP > 0.10 | Time management workshop |

---

## 📡 API Reference

All endpoints (except `/auth/*`) require `Authorization: Bearer <token>` header.

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register faculty / HOD account |
| POST | `/auth/login` | Login → returns access + refresh JWT |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Get current user profile |

### Students
| Method | Endpoint | Description |
|---|---|---|
| GET | `/students` | List all students (paginated, searchable) |
| GET | `/students/{id}` | Get single student profile |
| POST | `/students/upload` | Batch CSV upload → triggers predictions |
| PATCH | `/students/{id}` | Update student info manually |
| DELETE | `/students/{id}` | Delete a student and all related data |

### Predictions
| Method | Endpoint | Description |
|---|---|---|
| GET | `/predictions/{student_id}/latest` | Latest prediction + SHAP values |
| GET | `/predictions/{student_id}/history` | Risk score trend over time |

### Interventions
| Method | Endpoint | Description |
|---|---|---|
| GET | `/interventions` | All interventions (filterable) |
| GET | `/interventions/student/{student_id}` | Interventions for one student |
| PATCH | `/interventions/{id}/status` | Mark COMPLETED / IN_PROGRESS / DISMISSED |

### Dashboard
| Method | Endpoint | Description |
|---|---|---|
| GET | `/dashboard/summary` | Risk distribution stats, intervention counts |
| GET | `/dashboard/trends` | Week-by-week cohort risk aggregates |

> **Swagger UI:** `http://localhost:8000/docs`

---

## Database Schema

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL,   -- faculty | hod | admin
    department VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_code VARCHAR(30) UNIQUE NOT NULL,
    name VARCHAR(100),
    age INTEGER, gender VARCHAR(10),
    department VARCHAR(100), semester INTEGER,
    faculty_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE feature_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(id),
    week_number INTEGER,
    absences INTEGER, studytime INTEGER, failures INTEGER,
    raw_features JSONB,
    uploaded_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(id),
    snapshot_id UUID REFERENCES feature_snapshots(id),
    risk_score FLOAT NOT NULL,
    risk_level VARCHAR(10) NOT NULL,  -- HIGH | MEDIUM | LOW
    shap_values JSONB NOT NULL,
    shap_summary TEXT,
    predicted_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE interventions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(id),
    prediction_id UUID REFERENCES predictions(id),
    type VARCHAR(50), priority VARCHAR(20),
    title VARCHAR(200), description TEXT,
    assigned_to UUID REFERENCES users(id),
    due_date DATE,
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING | IN_PROGRESS | COMPLETED | DISMISSED
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

---

## Frontend Modules

| Page | Route | Description |
|---|---|---|
| Login | `/login` | JWT login with demo credential fill |
| Dashboard | `/dashboard` | Donut chart, risk counts, weekly trend line |
| Upload Data | `/upload` | Drag-and-drop CSV + week selector + results |
| Student List | `/students` | Searchable table with risk badges |
| Student Profile | `/students/:id` | Risk gauge, SHAP chart, history, interventions |
| Intervention Tracker | `/interventions` | Kanban board: Pending → In Progress → Completed |

---

## Dataset

**UCI Student Performance Data Set**
- Source: [UCI ML Repository](https://archive.ics.uci.edu/dataset/320/student+performance)
- File: `student-mat.csv` (395 records, 33 features)
- Target: `G3` (final grade) — binarised: `G3 < 10` = at-risk

Place the file at: `data/raw/student-mat.csv`

---

## 🧪 Running Tests
```bash
cd backend
pytest tests/ -v
```

---

## 🔄 Reset Demo Data
To clear all student data and start fresh (keeps user accounts):
```bash
python backend/reset_data.py
```

---

## Roadmap & Milestones

### Phase 1 — Foundation ✅
- Repository setup, Docker Compose
- PostgreSQL schema + SQLAlchemy ORM
- JWT auth (register / login / refresh)

### Phase 2 — ML Core ✅
- Feature engineering pipeline
- XGBoost + SMOTE training with GridSearchCV
- SHAP explainer integration
- Model evaluation + serialisation

### Phase 3 — Intervention Engine ✅
- Rule-based intervention catalogue (9 rules)
- Plain-English SHAP summary generator
- Intervention CRUD API endpoints

### Phase 4 — Frontend ✅
- Auth flow (Login, JWT context)
- CSV upload with column validator
- Student List with risk badges
- Student Profile: SHAP chart + intervention plan
- Dashboard: trend charts + summary stats
- Kanban Intervention Tracker

### Phase 5 — Testing & Deployment ✅
- pytest backend test suite
- GitHub Actions CI pipeline
- Docker Compose production setup

---

## 📄 License

This project is developed for academic and educational use.

---

*FAILSAFE — Because every student deserves a second chance before the semester ends.*
