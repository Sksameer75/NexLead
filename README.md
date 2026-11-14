# NexLead — Lead Intelligence & Sales Operations Platform

NexLead is a web-based Lead Intelligence and Sales Operations Platform designed to help sales teams manage leads, evaluate lead quality, prioritize prospects, coordinate sales activities, and track opportunities through the sales pipeline.

It combines lead scoring, sales workflow management, territory-based assignment, duplicate detection, campaign operations, and performance insights in one application.

The project is built using React, TypeScript, Python, FastAPI, SQLAlchemy, and MySQL.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation and Setup](#installation-and-setup)
- [Running the Application](#running-the-application)
- [Demo Data](#demo-data)
- [API Documentation](#api-documentation)
- [Important API Endpoints](#important-api-endpoints)
- [Testing and Verification](#testing-and-verification)
- [Data and Documentation](#data-and-documentation)

---

## Project Overview

Sales teams frequently deal with large numbers of leads, inconsistent lead quality, delayed follow-ups, duplicate records, and difficulty identifying which prospects deserve immediate attention.

NexLead addresses these operational challenges through a centralized application that provides:

- Centralized lead management.
- Multi-dimensional lead scoring.
- Lead prioritization and score history.
- Territory-based lead routing.
- Sales activity and task management.
- Opportunity and pipeline tracking.
- Lead consent management.
- Duplicate lead detection.
- Campaign-related operations.
- Historical performance and operational insights.

The application is designed around a practical sales workflow:

**Capture → Evaluate → Prioritize → Assign → Engage → Convert**

---

## Key Features

### 1. Lead Management

- View and manage lead records from a centralized interface.
- Access individual lead information.
- Track lead ownership and territory.
- Manage lead-related activities.
- Maintain lead consent information.

### 2. Intelligent Lead Scoring

NexLead evaluates leads using multiple scoring dimensions:

- **Fit Score:** Measures how well a lead matches the target customer profile.
- **Intent Score:** Represents the lead's buying intent.
- **Engagement Score:** Measures engagement with sales activities.
- **Total Score:** Provides an overall lead prioritization score.

The platform also supports historical score snapshots, allowing changes in lead quality to be examined over time.

### 3. Territory-Based Lead Routing

- Preview lead assignment decisions.
- Evaluate territory-based routing.
- Identify the appropriate sales representative.
- Support structured lead distribution.

### 4. Duplicate Detection

Duplicate detection functionality helps identify potentially repeated lead records and improve lead data quality.

### 5. Sales Task Management

- View assigned sales tasks.
- Track pending and completed tasks.
- Update task completion status.
- Coordinate follow-up activities.

### 6. Opportunity Management

- Associate opportunities with leads.
- Track sales opportunities.
- Manage opportunity pipeline stages.
- Monitor sales progress.

### 7. Campaign Operations

The backend includes dedicated campaign-related functionality to support campaign operations and lead engagement workflows.

### 8. Operational Insights

The application provides dashboard-level visibility into lead and sales operations, helping users understand lead distribution, scoring, task progress, and opportunity activity.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React 18, TypeScript, Vite |
| Backend | Python, FastAPI |
| Data Validation | Pydantic |
| ORM / Database Access | SQLAlchemy |
| Database | MySQL |
| Database Driver | PyMySQL |
| API Communication | REST API, HTTP, JSON |
| Testing | Pytest |
| Version Control | Git, GitHub |

---

## System Architecture

NexLead follows a three-tier application architecture.

```text
+--------------------------------------+
|          PRESENTATION TIER           |
|                                      |
|       React + TypeScript + Vite      |
|                                      |
|              Port 5173               |
+------------------+-------------------+
                   |
                   | HTTP / JSON
                   | REST API
                   v
+--------------------------------------+
|          APPLICATION TIER            |
|                                      |
|              FastAPI                 |
|                                      |
|    Lead Management and CRM Logic     |
|    Scoring and Routing               |
|    Tasks and Opportunities           |
|    Campaign and Deduplication Logic  |
|                                      |
|              Port 8000               |
+------------------+-------------------+
                   |
                   | SQLAlchemy
                   | PyMySQL
                   v
+--------------------------------------+
|              DATA TIER               |
|                                      |
|                MySQL                 |
|                                      |
|       Persistent Application Data   |
+--------------------------------------+
```

### Presentation Tier

The React frontend provides the user interface and communicates with the backend through REST API endpoints.

### Application Tier

FastAPI handles API requests, validation, database interactions, and CRM business operations.

The backend functionality is organized across application modules, including:

- `crm.py`
- `crm_campaigns.py`
- `crm_dedupe.py`
- `crm_extensions.py`

### Data Tier

MySQL provides persistent relational data storage. SQLAlchemy is used for database interaction, with PyMySQL as the database driver.

The application also includes dedicated health-check functionality for application and database diagnostics.

---

## Project Structure

```text
NexLead/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   └── health.py
│   │   │       └── router.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   │
│   │   ├── models/
│   │   │   └── base.py
│   │   │
│   │   ├── repositories/
│   │   │   └── health_repository.py
│   │   │
│   │   ├── schemas/
│   │   │   └── health.py
│   │   │
│   │   ├── services/
│   │   │   └── health_service.py
│   │   │
│   │   ├── crm.py
│   │   ├── crm_campaigns.py
│   │   ├── crm_dedupe.py
│   │   └── crm_extensions.py
│   │
│   │   └── main.py
│   │
│   ├── tests/
│   │   └── test_health.py
│   │
│   ├── .env.example
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts
│   │   │   └── healthApi.ts
│   │   │
│   │   ├── components/
│   │   │   └── HealthStatus.tsx
│   │   │
│   │   ├── types/
│   │   │   └── health.ts
│   │   │
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.tsx
│   │
│   ├── .env.example
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.ts
│
├── data/
│   ├── generated/
│   ├── ground_truth/
│   ├── exports/
│   └── nexlead_export.csv
│
├── docs/
│   ├── architecture.md
│   └── requirements-traceability.md
│
├── .env.example
├── .gitignore
└── README.md
```

---

## Prerequisites

Install the following software before running the application:

| Software | Recommended Version |
|---|---|
| Windows | Windows 10 / 11 |
| Python | 3.11 or newer |
| Node.js | 18 or newer |
| npm | Compatible with installed Node.js |
| MySQL | MySQL 8.0 or newer |
| Git | Latest stable version |

The project was developed and tested in a Windows environment using Python 3.13 and Node.js 24.

---

## Installation and Setup

### 1. Clone the Repository

```powershell
git clone https://github.com/Sksameer75/NexLead.git
cd NexLead
```

### 2. Database Setup

Make sure your MySQL service is running.

Create the application database:

```sql
CREATE DATABASE IF NOT EXISTS lead_intelligence
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

You can execute this through MySQL Workbench or the MySQL command-line client.

### 3. Backend Setup

Open PowerShell from the project root:

```powershell
cd backend
```

Create a Python virtual environment:

```powershell
python -m venv .venv
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
python -m pip install -r requirements.txt
```

Create the backend environment file:

```powershell
Copy-Item .env.example .env
```

Open `backend/.env` and configure the database connection.

Example:

```env
DATABASE_URL=mysql+pymysql://YOUR_USER:YOUR_PASSWORD@127.0.0.1:3306/lead_intelligence
```

Replace the example credentials with your actual MySQL credentials.

Do not commit your actual `.env` file or database passwords.

### 4. Start the Backend

From the `backend` directory, with the virtual environment activated:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend address:

```text
http://127.0.0.1:8000
```

### 5. Frontend Setup

Open a second PowerShell terminal.

Navigate to the frontend directory:

```powershell
cd NexLead/frontend
```

Create the frontend environment file:

```powershell
Copy-Item .env.example .env
```

Install frontend dependencies:

```powershell
npm.cmd install
```

Start the development server:

```powershell
npm.cmd run dev
```

Frontend address:

```text
http://127.0.0.1:5173
```

---

## Running the Application

Once both servers are running:

| Component | URL |
|---|---|
| NexLead Frontend | http://127.0.0.1:5173 |
| FastAPI Backend | http://127.0.0.1:8000 |
| Swagger API Documentation | http://127.0.0.1:8000/api/v1/docs |
| OpenAPI Specification | http://127.0.0.1:8000/api/v1/openapi.json |

The frontend communicates with the backend through the configured API client.

---

## Demo Data

NexLead includes a demonstration data workflow.

After configuring the backend and database and starting the application, the demo-seeding endpoint can be used to populate demonstration records.

```powershell
Invoke-RestMethod `
  -Method POST `
  -Uri "http://127.0.0.1:8000/api/v1/demo/seed"
```

The repository also contains a synthetic lead dataset:

```text
data/nexlead_export.csv
```

This dataset contains demonstration lead records and scoring information.

Use synthetic data for demonstrations and testing. Do not use real customer information in public repositories.

---

## API Documentation

NexLead exposes REST API functionality under:

```text
/api/v1
```

The API supports operations related to lead management, scoring, routing, tasks, opportunities, and other CRM workflows.

Interactive API documentation is available through FastAPI Swagger UI:

```text
http://127.0.0.1:8000/api/v1/docs
```

The Swagger interface can be used to inspect available operations, provide request parameters, submit API requests, and examine JSON responses.

---

## Important API Endpoints

The following are key application endpoints.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/dashboard` | Retrieve dashboard information |
| GET | `/api/v1/leads` | Retrieve leads |
| GET | `/api/v1/leads/{lead_id}` | Retrieve an individual lead |
| GET | `/api/v1/leads/{lead_id}/score` | Retrieve lead scoring information |
| GET | `/api/v1/leads/{lead_id}/activities` | Retrieve lead activities |
| POST | `/api/v1/leads/{lead_id}/consent` | Manage lead consent |
| GET | `/api/v1/tasks` | Retrieve sales tasks |
| POST | `/api/v1/tasks/{task_id}/complete` | Complete a task |
| GET | `/api/v1/opportunities` | Retrieve opportunities |
| GET | `/api/v1/leads/{lead_id}/opportunities` | Retrieve opportunities associated with a lead |
| POST | `/api/v1/opportunities/{opportunity_id}/stage` | Update an opportunity stage |
| POST | `/api/v1/demo/seed` | Seed demonstration data |

For request parameters, supported HTTP methods, and complete response schemas, refer to the live Swagger documentation.

---

## Testing and Verification

### 1. Application Health Check

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/health" |
  ConvertTo-Json -Depth 5
```

### 2. Database Connectivity Check

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/health/db" |
  ConvertTo-Json -Depth 5
```

### 3. Detailed Health Check

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/health/detailed" |
  ConvertTo-Json -Depth 5
```

### 4. Backend Tests

From the backend directory:

```powershell
python -m pytest tests -v
```

### 5. Frontend Production Build

From the frontend directory:

```powershell
npm.cmd run build
```

A successful build verifies that the frontend can be compiled for production.

---

## Data and Documentation

Additional project resources are available in the repository.

| Resource | Description |
|---|---|
| `data/nexlead_export.csv` | Synthetic lead demonstration dataset |
| `docs/architecture.md` | Architecture documentation |
| `docs/requirements-traceability.md` | Requirements traceability information |
| `backend/tests/` | Backend automated tests |

---

## Repository

**GitHub:** https://github.com/Sksameer75/NexLead

---

## Project Goal

NexLead aims to make sales operations more structured, measurable, and efficient by combining lead intelligence with practical CRM workflows.

It provides a centralized foundation for evaluating prospects, organizing sales activities, managing opportunities, and supporting data-driven sales decisions.

**NexLead — Turn Lead Data Into Sales Intelligence.**
