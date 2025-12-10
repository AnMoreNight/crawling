@echo off
REM ============================================
REM  Quick Test Run (10 URLs + Auto-Export)
REM  Perfect for first-time users
REM ============================================

cd /d %~dp0

echo.
echo ====================================
echo  Quick Test Run
echo ====================================
echo.
echo This will:
echo  1. Crawl 10 test URLs
echo  2. Automatically export to Google Sheets
echo  3. Show you the results
echo.
echo Press any key to start...
pause > nul

echo.
echo Starting crawl (may take 2-3 minutes)...
echo.

python batch_crawler.py "test data.xlsx" --limit 10 --timeout 15 --robots-policy ignore

if %ERRORLEVEL% neq 0 (
    echo.
    echo Error during crawl. Please check the output above.
    pause
    exit /b 1
)

echo.
echo ====================================
echo Now exporting to Google Sheets...
echo ====================================
echo.

python export_to_sheets.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo Export script not found or failed.
    echo You can still export manually:
    echo   - Run RUN_CRAWLER.bat
    echo   - Choose option 1
    pause
    exit /b 1
)

echo.
echo ====================================
echo SUCCESS!
echo ====================================
echo.
echo Your crawl results have been exported to Google Sheets.
echo.
echo Next time, just run RUN_CRAWLER.bat for the full menu.
echo.
pause
