# AitMate — System Architecture Specification

## 1. System Overview

**AitMate** is a Windows-first desktop AI assistant engineered around the core principle:
> **Useful autonomy, with the user in control.**

Unlike unrestricted autonomous agents or simple chatbots, AitMate executes multi-step computer tasks via mediated, typed tool calls governed by a centralized, server-side permission engine and explicit human-in-the-loop approval gates.

```
┌─────────────────────────────────────────────────────────────────┐
│                     AitMate Desktop UI                          │
│        React + TypeScript + Vite + Tailwind CSS + Lucide        │
│       [Chat]   [Tasks]   [Approvals]   [Activity]   [Settings]  │
└────────────────────────────────┬────────────────────────────────┘
                                 │ HTTP / WebSocket (127.0.0.1)
                                 │ Bearer Token Auth + Strict CORS
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Local Backend                        │
│       - Auth & Session Guard      - OpenAPI Typed Contracts    │
│       - Task Lifecycle Manager    - SQLite Database (SQLModel)  │
└────────────────────────────────┬────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Agent Orchestrator                          │
│                                                                 │
│   1. Parse Request ──► 2. Bounded Plan ──► 3. Policy Check     │
│                                                   │             │
│                                            Needs Approval?      │
│                                            ├── Yes ──► UI Gate │
│                                            └── No  ──► Execute │
│                                                   │             │
│   6. Output Summary ◄── 5. Audit Log  ◄── 4. Tool Registry     │
└────────────┬───────────────────┬───────────────────┬────────────┘
             ▼                   ▼                   ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │  AI Providers   │ │ Central Policy  │ │ Registered Tools│
    │  - Mock (Demo)  │ │ - Risk Evaluator│ │ - Files (Scoped)│
    │  - Ollama Local │ │ - Approval State│ │ - Browser (Play)│
    │  - Cloud APIs   │ │ - Rate Limits   │ │ - OS / Notif    │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## 2. Core Architectural Layers

### 2.1 Desktop Presentation Layer
- **Tech Stack:** React, TypeScript (strict mode), Vite, Tailwind CSS, Lucide icons.
- **Role:** Interactive command center for natural-language instructions, plan preview, real-time task progress, approval decision center, activity audits, and diagnostic settings.
- **Design Philosophy:** Clean, desktop-native productivity experience. Clear distinction between AI proposals, pending human approvals, active execution, and verified outcomes.

### 2.2 Desktop Shell (Tauri 2)
- **Role:** Native Windows wrapper providing system tray integration, native OS notifications, controlled window lifecycle, and offline packaging.
- **Architecture Strategy:** The web application communicates over standard loopback HTTP/WebSocket with the local Python agent backend. This enables full web development and testing via `npm run dev` while allowing Tauri to package the application into a native `.exe` whenever the Rust toolchain is compiled.

### 2.3 Local API & Security Boundary (FastAPI)
- **Binding:** Strictly bound to loopback `127.0.0.1` (never `0.0.0.0`).
- **Authentication:** Ephemeral per-session bearer tokens generated upon startup and shared securely with the desktop UI.
- **CORS:** Restricted to `http://localhost:*` and `tauri://localhost`.
- **Validation:** 100% of request and response payloads validated via typed Pydantic models.

### 2.4 Agent Orchestrator & Task Lifecycle
Tasks are managed by a deterministic finite state machine (FSM).

```
[queued] ──► [planning] ──► [awaiting_approval] ──► [running] ──► [completed]
    │             │                  │                 │
    ▼             ▼                  ▼                 ▼
[cancelled]   [failed]           [rejected]        [failed]
```

#### Valid Task States:
1. `queued`: Task accepted and waiting for worker allocation.
2. `planning`: Model generating bounded step-by-step execution plan.
3. `awaiting_approval`: Sensitive tool call paused pending explicit user decision.
4. `running`: Tool actively executing within scoped bounds.
5. `completed`: All plan steps completed and results verified.
6. `failed`: Execution failed (error captured and reported; non-idempotent actions not retried).
7. `cancelled`: User initiated immediate task termination.

---

## 3. Central Permission Engine & Tool Registry

### 3.1 Policy Enforcement
All tool execution is Mediated Server-Side:
- The UI is never trusted to enforce security policies.
- Every tool declares:
  - `name`: Unique identifier.
  - `description`: Plain-language explanation for user review.
  - `parameters_schema`: Pydantic JSON schema.
  - `risk_level`: `LOW` (read-only), `MEDIUM` (controlled file creation/reading), `HIGH` (external messaging, network mutation, deletion).
  - `requires_approval`: Boolean flag determining whether the human gate is triggered.
  - `allowed_targets`: Explicit domain or directory allowlist.

### 3.2 Approval Gate Mechanics
When a tool call has `requires_approval=True`:
1. The orchestrator transitions the task to `awaiting_approval`.
2. An `ApprovalRequest` record is created with:
   - `task_id`, `tool_name`, `target` (exact URL, recipient, file path).
   - `exact_parameters` (diff or message body).
   - `reason` and `risk_level`.
   - `expires_at` timestamp.
3. The UI presents the approval modal.
4. If approved: Tool executes with the exact parameters approved. If parameters change, approval is invalidated.
5. If rejected: Task halts safely; no retries bypass the rejection.

---

## 4. AI Provider Abstraction

The agent backend defines a provider interface `BaseAIProvider`:
- **`MockProvider`**: Deterministic mock provider for tests and standalone operation when no external AI is configured.
- **`OllamaProvider`**: Direct local inference via `http://127.0.0.1:11434` for offline privacy without GPU requirements.
- **`CloudProvider` (OpenAI / Anthropic)**: Optional cloud provider adapters authenticated strictly via environment variables or OS secrets.

**Fail-Safe Rule:** AitMate remains fully usable for browsing history, managing settings, and viewing logs even when no AI provider is active.

---

## 5. Storage & Audit Logging

- **Database:** SQLite (`aitmate.db`) using parameterized SQL / SQLModel.
- **Tables:**
  - `tasks`: Task definitions, status, plans, summaries.
  - `approvals`: Approval requests, statuses (`pending`, `approved`, `rejected`, `expired`), timestamps.
  - `audit_events`: Chronological append-only security and operational audit trail.
  - `settings`: Local user preferences and domain allowlists.
- **Audit Log File:** Append-only JSON-Lines (`aitmate_audit.log`) with automatic secret redaction (API keys, session cookies, and sensitive passwords are never written to disk).
