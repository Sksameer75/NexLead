# NexLead — Requirements Traceability Matrix (RTM)

This document tracks all functional, non-functional, and architectural requirements for NexLead from initial architecture foundation through future phases, establishing exact implementation mappings and verification methods.

---

## 1. Architectural & Foundational Requirements (Phase 1)

| Requirement ID | Requirement Description | Architectural Layer | Planned Implementation Module | Verification Method | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-ARC-01** | Genuine Three-Tier Architecture | Presentation, Application, Data | `frontend/` (React), `backend/` (FastAPI), MySQL 8.4 (`lead_intelligence`) | Independent startup of tiers, decoupled REST API communication, automated health tests | **Verified** |
| **REQ-ARC-02** | Presentation Tier Foundation | Presentation | React 18, Vite, TypeScript, `frontend/src/` | `npm run build` TypeScript check, HTTP 200 on port 5173 | **Verified** |
| **REQ-ARC-03** | Application Tier Foundation | Application | FastAPI, Pydantic v2, SQLAlchemy 2.0, `backend/app/` | `pytest backend/tests`, HTTP 200 on port 8000 | **Verified** |
| **REQ-ARC-04** | Data Tier Connectivity | Data | MySQL 8.4 database `lead_intelligence`, PyMySQL driver | Health check query (`SELECT 1, VERSION(), DATABASE()`) returning status `connected` | **Verified** |
| **REQ-ARC-05** | Modular Monolith (No Microservices) | Architecture | Single backend repository divided into `api/`, `services/`, `repositories/`, `models/`, `core/` | Code structure inspection, no RPC/distributed microservices | **Verified** |
| **REQ-ARC-06** | Separation of Concerns (No SQL in Routes) | Application | Route handlers call Service layer; Service layer calls Repository layer; Repositories execute queries | Static code analysis, code review of `backend/app/api/` | **Verified** |
| **REQ-ARC-07** | Pure Presentation Components | Presentation | React components contain no domain scoring, business rules, or direct database access | Frontend source review (`frontend/src/`) | **Verified** |
| **REQ-ARC-08** | Environment Configuration | Cross-Cutting | Pydantic `BaseSettings` (`backend/app/core/config.py`), `.env.example`, `.env` | Env resolution test from root and backend, zero hardcoded secrets | **Verified** |
| **REQ-ARC-09** | Application Health Endpoint | Application | `GET /api/v1/health` and `GET /health` | Automated pytest `test_root_health`, `test_api_v1_health` | **Verified** |
| **REQ-ARC-10** | Database Connectivity Health Check | Application / Data | `GET /api/v1/health/db` and `GET /api/v1/health/detailed` | Automated pytest `test_database_health`, live curl/REST query | **Verified** |
| **REQ-ARC-11** | Zero Extraneous Infrastructure | Infrastructure | No Redis, Kafka, Kubernetes, Celery, or external caching introduced | Dependency audits in `requirements.txt` and `package.json` | **Verified** |
| **REQ-ARC-12** | Standardized Data Directories | Infrastructure | `data/generated/`, `data/ground_truth/`, `data/exports/` | Directory existence check with `.gitkeep` placeholders | **Verified** |

---

## 2. Planned Implementation Roadmap (Future Phases)

| Phase / Module | Feature Description | Planned Module Path | Planned Verification Method |
| :--- | :--- | :--- | :--- |
| **Phase 2: Data Modeling** | Relational schema design for Leads, Accounts, Contacts, Interactions, Scores | `backend/app/models/`, `backend/app/schemas/` | Alembic migrations, foreign key integrity tests, table creation scripts |
| **Phase 3: Data Ingestion** | Synthetic data generation & ingestion pipelines for leads | `backend/app/services/ingestion/`, `data/generated/` | Validation against `data/ground_truth/`, schema conformance tests |
| **Phase 4: Lead Scoring Engine** | Deterministic business scoring algorithms & prioritization logic | `backend/app/services/scoring/` | Unit tests with test fixtures verifying scoring edge cases |
| **Phase 5: Sales Ops Dashboard** | Real-time lead review, filterable pipeline tables, triage UI | `frontend/src/components/`, `frontend/src/views/` | Cypress/Playwright E2E tests, REST integration tests |
| **Phase 6: Reporting & Export** | Structured analytics exports (CSV, JSON) for sales management | `backend/app/api/v1/endpoints/exports.py`, `data/exports/` | Export data integrity validation against database records |

