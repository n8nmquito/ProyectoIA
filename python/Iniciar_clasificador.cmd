@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    set "TICKET_PYTHON=%~dp0.venv\Scripts\python.exe"
) else (
    set "TICKET_PYTHON=python"
)
"%TICKET_PYTHON%" -m streamlit run app/app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
if errorlevel 1 (
    echo.
    echo No se pudo iniciar. Instala las dependencias con:
    echo python -m pip install -r requirements.txt
    pause
)
endlocal
