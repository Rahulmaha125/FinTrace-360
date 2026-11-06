@echo off
title FinTrace 360 - PostgreSQL Automated Setup
echo =================================================================
echo        FinTrace 360: PostgreSQL Warehouse Automated Setup
echo =================================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_postgres.ps1"
echo.
pause
