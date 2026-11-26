# Role-Based Learning Management System (LMS)

A role-based Learning Management System for a training institute supporting **Admin**, **Instructor**, and **Student** roles.

## Tech Stack

- **Frontend:** React.js (Vite), Tailwind CSS, Recharts, Axios, React Router DOM
- **Backend:** Python FastAPI, SQLAlchemy ORM, Alembic, PyMySQL, JWT Auth, SlowAPI, ReportLab, Pytest
- **Database:** MySQL 8.x (SQLite in-memory for automated Pytest suite)
- **Cloud Storage:** Local disk (`dev`) / Cloudinary authenticated private storage (`prod`)

## Folder Overview

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app, CORS, health check, router registration
│   │   ├── config.py           # Pydantic settings & production env configuration
│   │   ├── database.py         # SQLAlchemy engine & session factory
│   │   ├── models/             # ORM models (users, courses, assessments, tracking, finance)
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── routers/            # API endpoints per module
│   │   ├── services/           # Business logic & storage abstraction
│   │   ├── middleware/         # Global exception & error handlers
│   │   ├── dependencies/       # JWT auth & RBAC dependencies
│   │   └── utils/              # Security, rate limiter, PDF generator, seed script
│   ├── migrations/             # Alembic database migrations
│   ├── tests/                  # Pytest integration & security suites
│   ├── Procfile                # Render start command
│   ├── requirements.txt        # Pinned Python dependencies
│   └── .env.example            # Backend environment template
├── frontend/
│   ├── src/                    # React pages, layouts, components, services, context
│   ├── vercel.json             # Vercel SPA rewrite rules
│   ├── .env.example            # Frontend environment template
│   └── package.json
└── docs/
    ├── 03-business-rules/      # Attendance & course completion policies
    ├── 04-architecture/        # Security architecture & audit checklist
    ├── 05-api/                 # API endpoints reference & Postman collection
    ├── 08-testing/             # Test plan, test report, known issues
    └── 09-deployment/          # Env guide, deployment guide, backup & restore
```

## Prerequisites

- Python 3.11+
- Node.js 18+ & npm
- MySQL 8.x (for local/production runtime; not required to run Pytest)

## Local Setup & Run

### 1. Backend

1. Activate the virtual environment:
   ```powershell
   .\backend\venv\Scripts\Activate.ps1
   ```
2. Install pinned dependencies:
   ```powershell
   pip install -r backend\requirements.txt
   ```
3. Copy `backend/.env.example` to `backend/.env` and configure `DATABASE_URL`, `JWT_SECRET_KEY`, and `FRONTEND_ORIGIN`.
4. Run database migrations and seed initial data:
   ```powershell
   cd backend
   alembic upgrade head
   python -m app.utils.seed
   ```
5. Start the API server:
   ```powershell
   uvicorn app.main:app --reload --app-dir backend
   ```
6. Verify health: `GET http://localhost:8000/api/health`

### 2. Frontend

1. Copy `frontend/.env.example` to `frontend/.env`.
2. Install dependencies and start the dev server:
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

## Running Tests

Run the full backend Pytest suite (30 tests covering auth, RBAC, IDOR, CRUD, assignments, quizzes, attendance, payments, certificates, and security):

```powershell
backend\venv\Scripts\pytest.exe backend\tests -v
```

## Deployment & Documentation

- [Deployment Guide (Vercel + Render + Managed MySQL)](docs/09-deployment/deployment-guide.md)
- [Environment Variables Guide](docs/09-deployment/env-guide.md)
- [Backup & Restore Policy](docs/09-deployment/backup-restore.md)
- [Security Architecture & Checklist](docs/04-architecture/security.md)
- [API Reference](docs/05-api/api-endpoints.md) & [Postman Collection](docs/05-api/postman_collection.json)
- [Test Plan](docs/08-testing/test-plan.md) & [Test Report](docs/08-testing/test-report.md)
