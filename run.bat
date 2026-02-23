@echo off
REM ============================================================
REM  Hacker News Report - Script de Inicio (CMD)
REM  Uso: run.bat
REM  Opciones:
REM    run.bat              -> Inicia el servidor web
REM    run.bat fetch        -> Descarga posts y luego inicia el servidor
REM    run.bat fetch-only   -> Solo descarga posts (no inicia servidor)
REM ============================================================

cd /d "%~dp0"

echo.
echo   === Hacker News Report ===
echo.

REM --- Verificar entorno virtual ---
set VENV_PYTHON=%~dp0.venv\Scripts\python.exe
set VENV_PIP=%~dp0.venv\Scripts\pip.exe

if not exist "%VENV_PYTHON%" (
    echo   [!] No se encontro el entorno virtual (.venv)
    echo   Creando entorno virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo   [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
)

REM --- Activar entorno virtual ---
echo   [OK] Activando entorno virtual...
call "%~dp0.venv\Scripts\activate.bat"

REM --- Verificar dependencias ---
"%VENV_PYTHON%" -c "import flask" 2>nul
if errorlevel 1 (
    echo   [..] Instalando dependencias...
    "%VENV_PIP%" install -r requirements.txt --quiet
    if errorlevel 1 (
        echo   [ERROR] Error al instalar dependencias.
        pause
        exit /b 1
    )
    echo   [OK] Dependencias instaladas.
)

REM --- Ejecutar accion ---
if /i "%1"=="fetch" goto :fetch
if /i "%1"=="fetch-only" goto :fetchonly
goto :serve

:fetch
echo   [..] Descargando posts de Hacker News...
"%VENV_PYTHON%" -m src fetch --limit 50
echo.
echo   [OK] Iniciando servidor web...
echo   URL: http://127.0.0.1:5000
echo.
set FLASK_APP=src.web:create_app
set FLASK_DEBUG=1
"%VENV_PYTHON%" -m flask run --host=127.0.0.1 --port=5000
goto :end

:fetchonly
echo   [..] Descargando posts de Hacker News...
"%VENV_PYTHON%" -m src fetch --limit 50
echo.
echo   [OK] Posts descargados correctamente.
goto :end

:serve
echo   [OK] Iniciando servidor web...
echo   URL: http://127.0.0.1:5000
echo   Presiona Ctrl+C para detener
echo.
set FLASK_APP=src.web:create_app
set FLASK_DEBUG=1
"%VENV_PYTHON%" -m flask run --host=127.0.0.1 --port=5000
goto :end

:end
pause
