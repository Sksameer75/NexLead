NEXLEAD BACKEND PATCH

Extract this archive into C:\CandidateWorkspace\NexLead and allow overwrite of backend\app\crm.py and backend\app\main.py. Back up those two existing files first.

Database safety: startup create_all creates missing tables only; it does not drop or alter existing tables. It adds score_snapshots for immutable score history. No production database has been reset.

Includes: immutable score snapshots and history endpoint; historical rescoring uses a prior snapshot and never overwrites the live score; active scoring weight validation; purpose-specific marketing consent enforcement; no territory fallback; routing preview/validated assignment; future and post-conversion activities excluded from score updates; task consent and representative territory checks; deterministic IDs for newly created leads/tasks/opportunities; Lost reason requirement; separate lead conversion and opportunity win rates.

Smoke tests passed on a temporary SQLite database: dashboard, rep/lead/task creation, marketing consent block, activity scoring, score history, historical score without changing the live score, and invalid assignment rejection. Production MySQL has not yet been smoke-tested.
