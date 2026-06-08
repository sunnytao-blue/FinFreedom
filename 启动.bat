@echo off
cd /d "%~dp0"

echo ================================
echo FinFreedom - Dev Mode
echo ================================
echo.
echo Port: 3568
echo.

start http://localhost:3568

streamlit run app.py --server.port 3568

pause