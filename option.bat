@echo off
title ASTA Institutional Options Flow
echo ========================================================
echo  INITIALIZING: Institutional Options Flow Engine
echo ========================================================
echo.

REM Get today's date safely in MM-DD-YYYY format using PowerShell
for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "Get-Date -Format 'MM-dd-yyyy'"`) do set TARGET_DATE=%%i

echo [*] Looking for Barchart CSV files for: %TARGET_DATE%

set ACTIVE=data\most-active-stock-options-%TARGET_DATE%.csv
set DECOI=data\stocks-decrease-change-in-open-interest-%TARGET_DATE%.csv
set INCOI=data\stocks-increase-change-in-open-interest-%TARGET_DATE%.csv
set UNUSUAL=data\unusual-stock-options-activity-%TARGET_DATE%.csv
set OUT=output\flagged_options_%TARGET_DATE%.txt

set MISSING=
if not exist "%ACTIVE%" (
    echo [!] MISSING: %ACTIVE%
    set MISSING=1
)
if not exist "%DECOI%" (
    echo [!] MISSING: %DECOI%
    set MISSING=1
)
if not exist "%INCOI%" (
    echo [!] MISSING: %INCOI%
    set MISSING=1
)
if not exist "%UNUSUAL%" (
    echo [!] MISSING: %UNUSUAL%
    set MISSING=1
)

if defined MISSING (
    echo.
    echo [ERROR] The 4 required Barchart files were not found in the 'data\' folder!
    echo Please make sure you downloaded them and moved them to C:\screener\data\
    echo.
    pause
    exit /b 1
)

echo [*] All 4 files found! Beginning quantitative analysis...
echo.

python analyze_flow.py --active "%ACTIVE%" --decoi "%DECOI%" --incoi "%INCOI%" --unusual "%UNUSUAL%" --out "%OUT%"

echo.
echo [*] PROCESS COMPLETE. Report saved to: %OUT%
pause
