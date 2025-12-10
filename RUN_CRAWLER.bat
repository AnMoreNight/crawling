@echo off
REM ============================================
REM  Phase 1 Crawler - Simple Runner
REM  Just double-click this file!
REM ============================================

cd /d %~dp0

echo.
echo ====================================
echo  Phase 1 Web Crawler
echo ====================================
echo.

REM Ask user for input
echo What do you want to do?
echo.
echo 1. Crawl test data (small test - 10 URLs)
echo 2. Crawl with limit (50 URLs)
echo 3. Crawl all URLs
echo.

set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" (
    set "CMD=python batch_crawler.py "test data.xlsx" --limit 10 --timeout 15 --robots-policy ignore"
    call :run_and_export "%CMD%"
    goto end
)

if "%choice%"=="2" (
    set "CMD=python batch_crawler.py "test data.xlsx" --limit 50"
    call :run_and_export "%CMD%"
    goto end
)

if "%choice%"=="3" (
    set "CMD=python batch_crawler.py "test data.xlsx""
    call :run_and_export "%CMD%"
    goto end
)

echo Invalid choice. Please try again.
pause
goto start

:end
echo.
echo ====================================
echo Done!
echo ====================================
pause
exit /b

:run_and_export
REM %1 contains the command to run (quoted)
setlocal enabledelayedexpansion
set "CMD_IN=%~1"
echo.
echo Running: !CMD_IN!
echo.
call %CMD_IN%
set "CRAWL_EXIT=%ERRORLEVEL%"

if %CRAWL_EXIT% neq 0 (
    echo.
    echo Crawl failed with exit code %CRAWL_EXIT%
    endlocal & goto :eof
)

REM After crawl completes, check for results file and export
set "RESULT_FILE=crawl_results.jsonl"
if exist "%RESULT_FILE%" (
    echo.
    echo ✓ Crawl results saved to %RESULT_FILE%
    echo.
    set /p autoexport="Export results to Google Sheets now? (Y/n): "
    
    if /i "%autoexport%"=="n" (
        echo Skipping export.
        endlocal & goto :eof
    )
    
    REM Check for service account credentials
    if exist "credentials.json" (
        set /p use_creds="Service account credentials (credentials.json) found. Use it? (Y/n): "
        if /i "%use_creds%"=="n" (
            goto :use_apps_script
            else (
            echo.
            echo Exporting via service account...
            REM Use google_sheets_export to send the JSONL results via service account
            python google_sheets_export.py "%RESULT_FILE%"
            echo.
            echo ✓ Export complete. Check your Google Sheet!
            endlocal & goto :eof
        )
    )
    
    :use_apps_script
    echo.
    echo Using Google Apps Script deployment URL
    set /p apps_url="Enter URL (leave empty for embedded default): "
    
    if "%apps_url%"=="" (
        set "apps_url=https://script.google.com/macros/s/AKfycbz39IOKmJgBdt4ZL2wW2eljPtdxeSrd52q0DJrXfgGnlaLQb5izqupTqSRwx1XvgqdM/exec"
    )
    
    echo.
    echo Exporting to Google Sheets via Apps Script...
    python export_to_sheets.py
    echo.
    echo ✓ Export complete. Check your Google Sheet!
    endlocal & goto :eof
) else (
    echo.
    echo No results file found. Export skipped.
    endlocal & goto :eof
)

