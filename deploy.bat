@echo off
title Security Champion Dashboard — IBM Cloud Deploy
color 1F
cls

echo.
echo ============================================================
echo   Security Champion Dashboard — IBM Cloud Auto Deploy
echo   Using: IBM Code Engine (Dallas / us-south)
echo ============================================================
echo.

:: ── STEP 1: Ask for API Key ──────────────────────────────────
set /p APIKEY="Paste your IBM Cloud API Key and press Enter: "
echo.

if "%APIKEY%"=="" (
    echo ERROR: No API key entered. Please run this script again.
--    echo.
    pause
    exit /b 1
)

:: ── STEP 2: Login ────────────────────────────────────────────
echo [1/6] Logging into IBM Cloud (Dallas / us-south)...
echo.
ibmcloud login --apikey %APIKEY% -r us-south
echo.
echo Login step done. Press any key to continue...
pause
echo.

:: ── STEP 3: Target Default resource group ────────────────────
echo [2/6] Targeting Default resource group...
echo.
ibmcloud target -g Default
echo.
echo Resource group step done. Press any key to continue...
pause
echo.

:: ── STEP 4: Install Code Engine plugin ───────────────────────
echo [3/6] Installing IBM Code Engine plugin...
echo.
ibmcloud plugin install code-engine -f
echo.
echo Plugin install step done. Press any key to continue...
pause
echo.

:: ── STEP 5: Create Code Engine project ───────────────────────
echo [4/6] Setting up Code Engine project...
echo.
ibmcloud ce project create --name security-champion
if %ERRORLEVEL% NEQ 0 (
    echo Project may already exist - selecting it instead...
    ibmcloud ce project select --name security-champion
)
echo.
echo Project step done. Press any key to continue...
pause
echo.

:: ── STEP 6: Deploy from source ───────────────────────────────
echo [5/6] Deploying dashboard...
echo       This will take 3-5 minutes. Please wait...
echo.
cd /d "%~dp0"

ibmcloud ce application create --name security-champion-dashboard --build-source . --build-dockerfile Dockerfile --port 3000 --min-scale 1 --max-scale 3
if %ERRORLEVEL% NEQ 0 (
    echo App may already exist - updating it instead...
    ibmcloud ce application update --name security-champion-dashboard --build-source . --build-dockerfile Dockerfile --port 3000
)
echo.
echo Deploy step done. Press any key to continue...
pause
echo.

:: ── STEP 7: Get public URL ────────────────────────────────────
echo [6/6] Getting your public URL...
echo.
ibmcloud ce application get --name security-champion-dashboard --output url
echo.

echo ============================================================
echo   YOUR DASHBOARD IS NOW PUBLIC!
echo   Copy the URL shown above and share it with your team.
echo   Anyone can open it - no login required.
echo ============================================================
echo.
pause
