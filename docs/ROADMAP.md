# AitMate — Product Implementation Roadmap

This document outlines the phased engineering milestones from repository initialization to a production-grade, tested, and packaged Windows desktop assistant.

---

## Phase Matrix & Milestones

| Phase | Title | Core Deliverables | Target Status |
| :--- | :--- | :--- | :--- |
| **Phase 0** | **Repository Assessment** | Toolchain audit, Git baseline, `.gitignore`, `.env.example`, initial commit. | **COMPLETED** |
| **Phase 1** | **Architecture & Plans** | `ARCHITECTURE.md`, `ROADMAP.md`, `SECURITY.md`, `THREAT_MODEL.md`, `DEVELOPMENT.md`. | **IN PROGRESS** |
| **Phase 2** | **Minimal Runnable Foundation** | Python FastAPI backend (`backend/app/main.py`), health checks, typed API models, React + Vite frontend (`src/`), local API client, npm scripts. | Next |
| **Phase 3** | **Task Engine & Permissions** | Task FSM (`queued` -> `completed`), SQLite persistence, Central Permission Engine, Tool Registry, Approval records, pytest test suite. | Planned |
| **Phase 4** | **Conversational Desktop UI** | Real Chat view, Task lifecycle monitor, Approval Center modal, Activity audit feed, Settings page, live backend integration. | Planned |
| **Phase 5** | **AI Provider Integration** | `BaseAIProvider` interface, `MockProvider` (built-in offline demo), `OllamaProvider` (local), cloud adapters, provider health checks. | Planned |
| **Phase 6** | **Initial Real Tools** | Scoped local file reader, text summarizer, draft text generator, strict schema validation, policy compliance tests. | Planned |
| **Phase 7** | **Browser Automation** | Playwright for Python, domain allowlist enforcement, visible browser actions, navigation & extraction, approval gates for mutations. | Planned |
| **Phase 8** | **Drafting & External Integrations** | Communication workflow, message drafting, review screen with exact recipients/body, approval gate before sending, OAuth architecture. | Planned |
| **Phase 9** | **Background Mode & Notifications** | Windows desktop notification service, system tray integration hooks, pause/stop execution controls. | Planned |
| **Phase 10** | **Local Memory & GitLab Integration** | User-controlled transparent memory, GitLab API read-only client (issues/MRs), DevSecOps CI log summarizer. | Planned |
| **Phase 11** | **Quality, Security & Reliability** | Comprehensive pytest suite, prompt-injection penetration tests, approval-bypass tests, secret-redaction tests, ESLint & TypeScript validation. | Planned |
| **Phase 12** | **Packaging & Release** | Tauri 2 desktop shell configuration (`src-tauri/`), Windows build scripts, reproducible installation guide, `.gitlab-ci.yml`. | Planned |
| **Phase 13** | **Final Acceptance & Verification** | End-to-end verification against all 14 master scenarios, `docs/ACCEPTANCE_REPORT.md`. | Planned |

---

## Detailed Acceptance Criteria per Phase

### Phase 2: Minimal Runnable Foundation
- FastAPI backend starts on `127.0.0.1:8000` with `/api/v1/health` returning system status and version.
- Ephemeral session auth token generated and required for non-health endpoints.
- React + TypeScript + Vite frontend builds cleanly with `npm run build` and runs locally with `npm run dev`.
- Frontend successfully queries `/api/v1/health` and displays live backend status.

### Phase 3: Task Engine & Permissions
- Complete task state machine enforced in Python. Invalid transitions raise `InvalidStateTransitionError`.
- Central Permission Engine inspects tool, target, and arguments before any execution.
- Tools requiring approval generate an `ApprovalRequest` and halt execution until approved or rejected.
- Automated tests verify: unapproved sensitive calls are rejected; expired approvals cannot execute; approvals for Target A cannot execute on Target B.

### Phase 4: Conversational Desktop UI
- Chat interface accepts user instructions and initiates real background tasks.
- Task monitor displays real-time progress, plan steps, and execution states.
- Approval Center allows approving or rejecting pending actions with exact diff/content previews.
- Activity feed displays timestamped, redacted audit events loaded from backend SQLite.

### Phase 5: AI Provider Management
- Default offline mode uses `MockProvider` so the application runs without API keys or external services.
- Optional Ollama provider queries local models over HTTP.
- Diagnostics page tests provider connectivity and reports latency/errors honestly.

### Phase 6 & 7: Scoped Tools & Browser Automation
- Local file tool can only read files within user-permitted directories.
- Playwright browser automation is restricted to explicit allowlist domains (e.g., `wikipedia.org`, `github.com`).
- Browser actions display active status to the user and require approval for form submissions.

### Phase 11 & 13: Final Quality & Acceptance
- 100% of security test cases pass (zero unauthorized shell execution, prompt injection cannot grant permissions).
- Production build runs cleanly on Windows.
- `docs/ACCEPTANCE_REPORT.md` details verified features and evidence.
