@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
if errorlevel 1 goto fail
pause
exit /b 0
:fail
echo Installation failed. Close LayoutFixer and try again. Build first using build.bat.
pause
exit /b 1
