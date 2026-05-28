# Local preview harness for the Comprenda Streamlit app.
#
# Renders the app in a browser with fixture data - NO Snowflake connection,
# NO trial credits, and it sidesteps the Norton TLS issue entirely (nothing
# ever talks to snowflakecomputing.com).
#
# Usage (from anywhere):
#     powershell -ExecutionPolicy Bypass -File streamlit\_harness\run.ps1
# or just type in the Claude Code prompt:
#     ! streamlit\_harness\run.ps1
#
# First run creates a venv under _harness\.venv and installs streamlit + altair
# (snowpark + pandas come from the system Python via --system-site-packages).

$ErrorActionPreference = "Stop"

$HarnessDir = $PSScriptRoot
$AppDir     = Split-Path $HarnessDir -Parent        # ...\streamlit
$VenvDir    = Join-Path $HarnessDir ".venv"
$VenvPy     = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $VenvPy)) {
    Write-Host "[harness] creating venv (first run)..." -ForegroundColor Cyan
    python -m venv --system-site-packages $VenvDir
    & $VenvPy -m pip install --upgrade pip
    & $VenvPy -m pip install streamlit altair
}

# Put the harness dir on PYTHONPATH so sitecustomize.py auto-loads and patches
# the session + query module before any app code runs.
$env:PYTHONPATH = $HarnessDir

Write-Host "[harness] launching Comprenda in MOCK MODE - http://localhost:8501" -ForegroundColor Green
Set-Location $AppDir
& $VenvPy -m streamlit run comprenda_app.py
