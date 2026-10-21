# AitMate Windows Production Build & Packaging Script
# Requires: Python 3.10+, Node 18+, npm 9+
# Optional for installer packaging: Rust/Cargo, Tauri CLI, PyInstaller

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   AitMate Desktop AI Assistant — Windows Build Pipeline" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Step 1: Python Tests & Quality Gate
Write-Host "`n[1/4] Running Python automated test suite..." -ForegroundColor Yellow
python -m pytest backend/tests/ -v
if ($LASTEXITCODE -ne 0) {
    Write-Error "Backend test suite failed. Build aborted."
    exit 1
}
Write-Host "[✓] All backend tests passed." -ForegroundColor Green

# Step 2: Frontend TypeScript Validation
Write-Host "`n[2/4] Verifying Frontend TypeScript typing..." -ForegroundColor Yellow
npx tsc --noEmit
if ($LASTEXITCODE -ne 0) {
    Write-Error "TypeScript compilation check failed. Build aborted."
    exit 1
}
Write-Host "[✓] TypeScript verification passed with zero errors." -ForegroundColor Green

# Step 3: Production Frontend Build
Write-Host "`n[3/4] Building production React web bundle..." -ForegroundColor Yellow
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Error "Vite production build failed. Build aborted."
    exit 1
}
Write-Host "[✓] Production bundle generated in ./dist." -ForegroundColor Green

# Step 4: Verification
Write-Host "`n[4/4] Verifying build output integrity..." -ForegroundColor Yellow
if (-not (Test-Path "dist/index.html")) {
    Write-Error "dist/index.html not found after build!"
    exit 1
}
$distSize = (Get-ChildItem -Recurse dist | Measure-Object -Property Length -Sum).Sum / 1KB
Write-Host ("[✓] Build output verified: {0:N1} KB in dist directory." -f $distSize) -ForegroundColor Green

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "   Build completed successfully! Ready for packaging." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "To package as a standalone Windows installer (.msi / .exe):"
Write-Host "  1. (Optional) Compile Python sidecar: pyinstaller --onefile backend/app/main.py"
Write-Host "  2. Run Tauri build: npm run tauri build"
