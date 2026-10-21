# AitMate — Windows-First Desktop AI Assistant

> **Useful autonomy, with the user in control.**

AitMate is an autonomous desktop AI assistant that plans multi-step tasks, interacts with registered tools, navigates approved websites, and automates workflows while requiring explicit human approval for sensitive actions.

---

## Key Highlights

- **Desktop-Native Control Center:** Sleek, modern interface built with React, TypeScript, Vite, and Tailwind CSS.
- **Server-Enforced Safety:** Central Permission Engine mediates every action server-side; untrusted shell execution is strictly disabled.
- **Human Approval Gates:** High-risk actions (message sending, external mutations, file modifications) are paused with exact parameter previews until approved.
- **Zero-Trust Web Ingestion:** External web pages and emails are treated as data, preventing indirect prompt-injection exploits.
- **Local Loopback Security:** FastAPI backend binds exclusively to `127.0.0.1` protected by ephemeral per-session Bearer tokens.
- **Offline & Local LLM Support:** Runs deterministically out-of-the-box in mock mode; supports local inference via Ollama or optional cloud APIs.

---

## Architecture at a Glance

```
React Desktop UI (Vite + Tailwind) ──► Loopback HTTP/WebSocket (127.0.0.1)
                                      ├── FastAPI Agent Backend
                                      ├── Central Permission Engine
                                      ├── SQLite Task & Audit Store
                                      └── Playwright Browser Automation
```

---

## Quickstart Guide

### 1. Backend Setup
```powershell
# Create & activate Python virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies & run backend
pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Setup
```powershell
# Install npm dependencies
npm install

# Start Vite development server
npm run dev
```

### 3. Verify Health & Tests
```powershell
# Run backend test suite
pytest backend/tests/ -v

# Run frontend typecheck & production build
npm run typecheck
npm run build
```

---

## Documentation

- [System Architecture](file:///docs/ARCHITECTURE.md)
- [Product Implementation Roadmap](file:///docs/ROADMAP.md)
- [Security Architecture & Policy](file:///docs/SECURITY.md)
- [Threat Model & STRIDE Analysis](file:///docs/THREAT_MODEL.md)
- [Developer & Contributor Guide](file:///docs/DEVELOPMENT.md)
