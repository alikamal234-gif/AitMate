# AitMate Windows Packaging, Distribution & Release Guide

This document defines the packaging pipeline, installer generation, sidecar binary orchestration, code signing, and auto-update architecture for AitMate on Windows.

---

## 1. Distribution Architecture

AitMate uses a **hybrid desktop architecture**:
1. **Frontend Host:** Tauri 2 native desktop window utilizing the Windows WebView2 runtime (pre-installed on Windows 10/11).
2. **Backend Engine:** Python FastAPI service executing on `127.0.0.1:8000` with ephemeral session tokens and SQLModel/SQLite.
3. **Packaging Strategy:**
   - **Development Mode:** Vite dev server on `127.0.0.1:5173` proxying to FastAPI backend on `127.0.0.1:8000`.
   - **Production Distribution:** Tauri bundles the optimized React assets (`dist/`) directly into the executable and orchestrates the backend as an embedded sidecar or system service.

```
+---------------------------------------------------------+
|                  AitMate.exe (Tauri 2)                  |
|  +---------------------------------------------------+  |
|  |           WebView2 Window (React 18 UI)           |  |
|  +---------------------------------------------------+  |
|                          | Loopback HTTP (Bearer Auth)   |
|                          v                              |
|  +---------------------------------------------------+  |
|  |        aitmate-backend.exe (FastAPI Sidecar)      |  |
|  |        - Policy Engine & Permission Gate          |  |
|  |        - SQLite Database (aitmate.db)             |  |
|  |        - Mediated Tool Registry                   |  |
|  +---------------------------------------------------+  |
+---------------------------------------------------------+
```

---

## 2. Windows Installer Formats

Tauri 2 generates two standard Windows installer formats:
1. **NSIS Installer (`.exe`):**
   - Streamlined, customizable setup wizard.
   - Recommended for individual desktop users.
   - Supports per-user installation (`%LOCALAPPDATA%`) without requiring administrator elevation.
2. **WiX Toolset Installer (`.msi`):**
   - Enterprise-standard Windows Installer package.
   - Recommended for enterprise deployment via Microsoft Intune, Group Policy (GPO), or SCCM.
   - Supports silent installation (`msiexec /i AitMate.msi /quiet /qn`).

---

## 3. Step-by-Step Packaging Pipeline

### Prerequisites
- Windows 10/11 (x64)
- Python 3.10+ with backend dependencies (`pip install -e .`)
- Node.js 18+ and npm
- Rust toolchain (`rustup target add x86_64-pc-windows-msvc`)
- Visual Studio C++ Build Tools

### Step 1: Run the Automated Quality & Build Gate
Execute the build script from PowerShell:
```powershell
.\scripts\build_windows.ps1
```
This runs:
- 73+ Python automated tests (policy, tools, security pen tests, FSM).
- TypeScript strict compiler check (`npx tsc --noEmit`).
- Production Vite bundler (`npm run build`).

### Step 2: Build the Python Sidecar Binary
Package the backend using PyInstaller:
```powershell
pyinstaller --name aitmate-backend-x86_64-pc-windows-msvc `
            --onefile `
            --clean `
            --distpath src-tauri/binaries `
            backend/app/main.py
```

### Step 3: Compile the Tauri Desktop Installer
```powershell
npm run tauri build
```
Output artifacts will be generated in `src-tauri/target/release/bundle/`:
- `nsis/AitMate_0.1.0_x64-setup.exe`
- `msi/AitMate_0.1.0_x64.msi`

---

## 4. Code Signing (Windows Authenticode)

To prevent Windows Defender SmartScreen warnings on clean installs, sign both the executable and the installer with an Authenticode certificate:

```powershell
# Using an EV Code Signing Certificate or Azure Trusted Signing
signtool sign /tr http://timestamp.digicert.com `
              /td sha256 `
              /fd sha256 `
              /a "src-tauri\target\release\bundle\nsis\AitMate_0.1.0_x64-setup.exe"
```

---

## 5. Auto-Update Mechanism

AitMate uses Tauri's cryptographic auto-updater:
1. **Public Key Verification:** The application binary embeds an Ed25519 public key.
2. **Release Manifest:** Updates check a secure HTTPS release endpoint (`https://releases.aitmate.com/updates/latest.json`).
3. **Signature Check:** Tauri verifies the digital signature of the downloaded payload before applying the update in the background.
4. **User Choice:** Updates can prompt the user or apply upon next restart.
