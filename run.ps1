# ============================================================
# 🦉 Hacker News Report - Script de Inicio (PowerShell)
# Uso: .\run.ps1
# Opciones:
#   .\run.ps1              -> Inicia el servidor web
#   .\run.ps1 fetch        -> Descarga posts y luego inicia el servidor
#   .\run.ps1 fetch-only   -> Solo descarga posts (no inicia servidor)
# ============================================================

param(
    [string]$Action = "serve"
)

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

Write-Host ""
Write-Host "  🦉 Hacker News Report" -ForegroundColor Yellow
Write-Host "  =====================" -ForegroundColor DarkYellow
Write-Host ""

# --- Verificar que el entorno virtual existe ---
$VenvPath = Join-Path $ProjectDir ".venv"
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
$VenvActivate = Join-Path $VenvPath "Scripts\Activate.ps1"

if (-not (Test-Path $VenvPython)) {
    Write-Host "  ❌ No se encontró el entorno virtual (.venv)" -ForegroundColor Red
    Write-Host "  Creando entorno virtual..." -ForegroundColor Cyan
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Error al crear el entorno virtual." -ForegroundColor Red
        exit 1
    }
}

# --- Activar entorno virtual ---
Write-Host "  🔧 Activando entorno virtual..." -ForegroundColor Cyan
& $VenvActivate

# --- Instalar dependencias si faltan ---
$FlaskCheck = & $VenvPython -c "import flask" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  📦 Instalando dependencias..." -ForegroundColor Cyan
    & $VenvPython -m pip install -r requirements.txt --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ❌ Error al instalar dependencias." -ForegroundColor Red
        exit 1
    }
    Write-Host "  ✅ Dependencias instaladas." -ForegroundColor Green
}

# --- Acciones ---
switch ($Action.ToLower()) {
    "fetch" {
        Write-Host "  📡 Descargando posts de Hacker News..." -ForegroundColor Cyan
        & $VenvPython -m src fetch --limit 50
        Write-Host ""
        Write-Host "  🚀 Iniciando servidor web..." -ForegroundColor Green
        Write-Host "  📍 Abre tu navegador en: http://127.0.0.1:5000" -ForegroundColor Yellow
        Write-Host ""
        $env:FLASK_APP = "src.web:create_app"
        $env:FLASK_DEBUG = "1"
        & $VenvPython -m flask run --host=127.0.0.1 --port=5000
    }
    "fetch-only" {
        Write-Host "  📡 Descargando posts de Hacker News..." -ForegroundColor Cyan
        & $VenvPython -m src fetch --limit 50
        Write-Host ""
        Write-Host "  ✅ Posts descargados correctamente." -ForegroundColor Green
    }
    default {
        Write-Host "  🚀 Iniciando servidor web..." -ForegroundColor Green
        Write-Host "  📍 Abre tu navegador en: http://127.0.0.1:5000" -ForegroundColor Yellow
        Write-Host "  ⏹  Presiona Ctrl+C para detener" -ForegroundColor DarkGray
        Write-Host ""
        $env:FLASK_APP = "src.web:create_app"
        $env:FLASK_DEBUG = "1"
        & $VenvPython -m flask run --host=127.0.0.1 --port=5000
    }
}
