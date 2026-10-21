# AitMate — Developer & Contributor Guide

Welcome to the AitMate developer guide. This document provides step-by-step instructions for configuring, developing, testing, and running AitMate locally on Windows.

---

## 1. System Requirements

- **Operating System:** Windows 10 / 11 (64-bit)
- **Node.js:** v18.0.0+ (Tested with v24.x)
- **npm:** v10.0.0+ (Tested with v11.x)
- **Python:** v3.12+ (Tested with Python 3.14.0)
- **Rust & Cargo:** (Optional for native desktop shell build; install via [rustup.rs](https://rustup.rs))

---

## 2. Initial Setup

### 2.1 Clone and Environment Setup
```powershell
# Clone the repository
git clone https://github.com/alikamal234-gif/AitMate.git
cd AitMate

# Create local environment file from template
Copy-Item .env.example .env
```

### 2.2 Python Backend Setup
```powershell
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r backend/requirements.txt
```

### 2.3 Frontend Setup
```powershell
# Install frontend dependencies using npm
npm install
```

---

## 3. Running AitMate Locally

AitMate operates via a local 2-tier process architecture during development:

### 3.1 Step 1: Start the Python Backend
In your first terminal (with `.venv` active):
```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
The API documentation will be available at: `http://127.0.0.1:8000/docs`
Health check endpoint: `http://127.0.0.1:8000/api/v1/health`

### 3.2 Step 2: Start the Frontend UI
In a second terminal:
```powershell
npm run dev
```
Open `http://localhost:5173` in your browser to interact with the AitMate Command Center.

### 3.3 Optional: Launch Tauri Native Desktop Shell
When Rust/Cargo is installed on your Windows machine:
```powershell
npm run tauri dev
```

---

## 4. Verification & Testing

Always verify your changes before committing:

### 4.1 Backend Tests & Quality Checks
```powershell
# Run backend test suite
pytest backend/tests/ -v

# Run linting and style checks
ruff check backend/
```

### 4.2 Frontend Quality Checks
```powershell
# Run TypeScript type check
npm run typecheck

# Verify frontend production build
npm run build
```

---

## 5. Security Checklist for Contributors

Before submitting any code changes, verify that:
1. No hardcoded API keys, passwords, or test tokens exist in any file.
2. Every new agent action is registered as a typed tool in `backend/app/tools/registry.py`.
3. High-risk operations (mutations, network transmission, file deletion) have `requires_approval=True`.
4. All database queries use parameterized SQL or SQLModel ORM models.
5. All external web/email content is wrapped as untrusted data before reaching model prompts.
