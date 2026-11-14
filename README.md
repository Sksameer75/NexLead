# NexLead — Lead Intelligence & Sales Operations Platform

NexLead is a professional Lead Intelligence and Sales Operations Platform built with a genuine three-tier architecture:

1. **Presentation Tier**: React 18 + Vite + TypeScript
2. **Application Tier**: Python 3.13 + FastAPI + Pydantic v2 + SQLAlchemy 2.0
3. **Data Tier**: MySQL 8.4 (`lead_intelligence`)

---

## Architecture Overview

```
                      +-----------------------------+
                      |      Presentation Tier      |
                      |   React + Vite + TypeScript  |
                      |         (Port 5173)         |
                      +--------------+--------------+
                                     |
                                     | REST / JSON
                                     v
                      +-----------------------------+
                      |      Application Tier       |
                      |      FastAPI + SQLAlchemy   |
                      |         (Port 8000)         |
                      +--------------+--------------+
                                     |
                                     | TCP (Port 3306)
                                     v
                      +-----------------------------+
                      |          Data Tier          |
                      |      MySQL 8.4 Database     |
                      |     (lead_intelligence)     |
                      +-----------------------------+
```

- **Frontend $\leftrightarrow$ Backend**: All communication is strictly over HTTP/JSON via REST API endpoints mounted under `/api/v1`.
- **Backend $\leftrightarrow$ Database**: The backend owns all business logic and connects to MySQL 8.4 through a dedicated SQLAlchemy repository layer with connection pooling.
- **Modular Monolith**: Clean separation between API transport, business services, repositories, and data models. No microservices or extraneous distributed systems.

---

## Project Structure

```
NexLead/
├── data/
│   ├── generated/              # Generated synthetic data
│   ├── ground_truth/           # Ground truth validation datasets
│   └── exports/                # Exported reports and analytics
├── docs/
│   ├── architecture.md         # Three-tier system architecture specification
│   └── requirements-traceability.md # Requirements traceability matrix
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   └── health.py    # Health & DB diagnostic route handlers
│   │   │       └── router.py        # Master v1 API router
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic BaseSettings environment config
│   │   │   └── database.py          # SQLAlchemy engine, session pool, get_db
│   │   ├── models/
│   │   │   └── base.py              # SQLAlchemy Declarative Base
│   │   ├── repositories/
│   │   │   └── health_repository.py # Data access layer for DB diagnostics
│   │   ├── schemas/
│   │   │   └── health.py            # Pydantic validation schemas
│   │   ├── services/
│   │   │   └── health_service.py    # Business logic layer
│   │   └── main.py                  # FastAPI application entry point
│   ├── tests/
│   │   └── test_health.py           # Automated health & DB endpoint tests
│   ├── .env.example                 # Backend environment variable template
│   ├── .env                         # Local dev environment (gitignored)
│   └── requirements.txt             # Minimal Python dependencies
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts            # Fetch-based REST client
│   │   │   └── healthApi.ts         # Health API callers
│   │   ├── components/
│   │   │   └── HealthStatus.tsx     # Tier status display component
│   │   ├── types/
│   │   │   └── health.ts            # TypeScript interfaces
│   │   ├── App.tsx                  # Root layout & lifecycle
│   │   ├── App.css                  # UI styling
│   │   ├── index.css                # Base styling
│   │   ├── main.tsx                 # React entry point
│   │   └── vite-env.d.ts            # Vite client type definitions
│   ├── .env.example                 # Frontend environment template
│   ├── .env                         # Frontend local dev configuration
│   ├── package.json                 # Minimal npm dependencies
│   ├── tsconfig.json                # TypeScript compiler config
│   └── vite.config.ts               # Vite configuration (port 5173)
├── .env.example                     # Root environment template
├── .gitignore                       # Git exclusion rules
└── README.md                        # Setup and startup guide
```

---

## Prerequisites

- **Operating System**: Windows 10/11
- **PowerShell**: Windows PowerShell 5.1+ or PowerShell 7+
- **Python**: 3.11+ (tested on Python 3.13)
- **Node.js**: v18+ (tested on Node v24.21.0, npm 11.19.0)
- **MySQL**: MySQL 8.4 (or MySQL 8.0 Community Server running on port 3306)

---

## Setup & Startup Instructions (Windows PowerShell)

Open Windows PowerShell.

### 1. Database Setup

Ensure the MySQL service is running and create the `lead_intelligence` database if it does not already exist:

```powershell
# Using MySQL Command Line Client (replace with your credentials)
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS lead_intelligence CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

---

### 2. Backend Setup (Application Tier)

Navigate to the `backend` directory, create a virtual environment, and install dependencies:

```powershell
cd c:\Users\Sameer\Desktop\NexLead\backend

# 1. Create Python virtual environment
python -m venv .venv

# 2. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Install strictly required dependencies
pip install -r requirements.txt

# 4. Configure environment variables
# Copy .env.example to .env and adjust credentials if needed
Copy-Item .env.example .env
```

Ensure `backend/.env` contains your correct database credentials:
```ini
DATABASE_URL="mysql+pymysql://<user>:<password>@127.0.0.1:3306/lead_intelligence"
```

#### Start Backend Server:

```powershell
# From the backend directory with virtual environment activated:
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend will be accessible at:
- **API Root**: `http://127.0.0.1:8000`
- **Swagger Documentation**: `http://127.0.0.1:8000/api/v1/docs`
- **Interactive OpenAPI Specification**: `http://127.0.0.1:8000/api/v1/openapi.json`

---

### 3. Frontend Setup (Presentation Tier)

Open a **new** PowerShell terminal for the frontend:

```powershell
cd c:\Users\Sameer\Desktop\NexLead\frontend

# 1. Configure environment variables
Copy-Item .env.example .env

# 2. Install dependencies (using npm.cmd on Windows)
cmd /c npm install

# 3. Start Vite development server
cmd /c npm run dev
```

Frontend will be accessible at:
- **Application URL**: `http://127.0.0.1:5173`

---

## Verification & Health Check Endpoints

Both tiers can be verified independently via PowerShell or curl:

### Application Health Check:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" | ConvertTo-Json
```
**Sample Response:**
```json
{
  "status": "healthy",
  "app": "NexLead API",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2026-11-14T09:42:11.410437Z"
}
```

### Database Connectivity Health Check:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health/db" | ConvertTo-Json
```
**Sample Response:**
```json
{
  "status": "connected",
  "database": "mysql",
  "version": "8.0.46",
  "latency_ms": 1.24,
  "database_name": "lead_intelligence",
  "message": "Database connection established successfully"
}
```

### Full System Health Check:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health/detailed" | ConvertTo-Json
```

### Run Automated Backend Test Suite:
```powershell
cd c:\Users\Sameer\Desktop\NexLead
.\backend\.venv\Scripts\pytest.exe backend\tests -v
```

### Verify Frontend TypeScript Build:
```powershell
cd c:\Users\Sameer\Desktop\NexLead\frontend
cmd /c npm run build
```

