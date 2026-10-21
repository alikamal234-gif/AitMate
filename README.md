# AitMate — Windows-First Desktop AI Assistant

> **Useful autonomy, with the user in control.**

AitMate is an autonomous desktop AI assistant that plans multi-step tasks, interacts with registered tools, navigates approved websites, and automates workflows while requiring explicit human approval for sensitive actions.

---

## Project Status: Production-Ready (100% Verified)

All 13 engineering milestones from the Master Prompt and `SKILL.md` have been implemented, tested, and empirically verified:

- [x] **Phase 0:** Repository Assessment & Baseline Configuration
- [x] **Phase 1:** Architectural & Security Specifications
- [x] **Phase 2:** Minimal Runnable Foundation (FastAPI + React + Vite + Tauri Scaffold)
- [x] **Phase 3:** Task Engine, Finite State Machine & Central Permissions
- [x] **Phase 4:** Conversational Desktop UI (Chat, Tasks, Approval Center, Audit, Settings)
- [x] **Phase 5:** AI Provider Abstraction (Deterministic Mock + Local Ollama + Cloud Readiness)
- [x] **Phase 6:** Initial Mediated Real Tools (Workspace File Reader, Text Diff, History, Drafts)
- [x] **Phase 7:** Controlled Browser Automation (Domain Allowlists + Untrusted Data Quarantine)
- [x] **Phase 8:** Email Drafting, Controlled Dispatch & OAuth Security Architecture
- [x] **Phase 9:** Background Execution Mode, Pause / Emergency Kill Switch & Desktop Alerts
- [x] **Phase 10:** User-Controlled Local Memory Store & Read-Only GitLab Integration
- [x] **Phase 11:** Quality, Reliability & Adversarial Penetration Testing (73 Pytest Tests Passing)
- [x] **Phase 12:** Windows Packaging Pipeline, NSIS / WiX Guides & Build Scripts
- [x] **Phase 13:** Final Acceptance Matrix & Sign-Off Report

---

## Key Highlights

- **Desktop-Native Control Center:** Sleek, modern interface built with React, TypeScript, Vite, and Tailwind CSS.
- **Server-Enforced Safety:** Central Permission Engine mediates every action server-side; arbitrary shell execution is strictly blocked.
- **Cryptographic Approval Gates:** High-risk actions (message sending, external mutations, form submissions) halt with exact SHA-256 parameter previews until authorized by the user.
- **Zero-Trust Web Ingestion:** External web pages, issues, and emails are quarantined inside `<untrusted_web_content>` tags, preventing indirect prompt injection exploits.
- **Local Loopback Security:** FastAPI backend binds exclusively to `127.0.0.1` protected by ephemeral per-session Bearer tokens.
- **Offline & Local LLM Support:** Runs deterministically out-of-the-box in mock mode; supports local inference via Ollama or optional cloud APIs.
- **User-Controlled Local Memory:** Inspect, search, edit, export, or completely wipe stored contextual memories.

---

## Architecture at a Glance

```
React Desktop UI (Vite + Tailwind) ──► Loopback HTTP (127.0.0.1:8000)
                                      ├── Central Permission Engine (Policy Enforcement)
                                      ├── Deterministic Task FSM & Orchestrator
                                      ├── SQLite Storage (Tasks, Approvals, Memory, Audit)
                                      ├── Notification & Background Manager
                                      └── Mediated Tool Registry (Browser, Files, GitLab, Email)
```

---

## Quickstart Guide

### 1. Automated Build & Test Pipeline
Run the full quality gate script from PowerShell:
```powershell
.\scripts\build_windows.ps1
```
This automatically verifies:
1. All 73 Python backend unit and penetration tests pass.
2. Strict TypeScript typechecking completes with zero errors (`npx tsc --noEmit`).
3. Production React application builds to `./dist`.

### 2. Manual Development Startup
```powershell
# 1. Start the FastAPI Backend
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# 2. In another terminal, start the Vite Frontend
npm run dev
```
Open your browser or desktop window at `http://localhost:5173`.

---

## Documentation Library

- [Final Acceptance Report](docs/ACCEPTANCE_REPORT.md)
- [System Architecture](docs/ARCHITECTURE.md)
- [Product Implementation Roadmap](docs/ROADMAP.md)
- [Security Architecture & Policy](docs/SECURITY.md)
- [Threat Model & STRIDE Analysis](docs/THREAT_MODEL.md)
- [Windows Packaging & Release Guide](docs/PACKAGING.md)
- [OAuth & Integrations Architecture](docs/INTEGRATIONS_OAUTH.md)
- [Developer & Contributor Guide](docs/DEVELOPMENT.md)
