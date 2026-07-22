@echo off
echo.
echo ======================================
echo  Pushing dashboard to GitHub Pages...
echo ======================================
echo.

cd /d "%~dp0"

"C:\Program Files\Git\cmd\git.exe" add public/index.html public/xlsx.full.min.js

"C:\Program Files\Git\cmd\git.exe" commit -m "Update dashboard %date% %time%"

"C:\Program Files\Git\cmd\git.exe" push origin HEAD

echo.
if %errorlevel%==0 (
  echo ======================================
  echo  SUCCESS! Wait 60 seconds then open:
  echo  https://sowndharya123-dev.github.io/watsonsec/
  echo ======================================
) else (
  echo ======================================
  echo  PUSH FAILED - see error above
  echo ======================================
)
echo.
pause
