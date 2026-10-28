@echo off
cd /d "%~dp0"
py -3 -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements-build.txt
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name LayoutFixer app.py
if errorlevel 1 goto fail
echo Built: dist\LayoutFixer.exe
pause
exit /b 0
:fail
echo Build failed. Check Python installation and internet connection.
pause
exit /b 1
