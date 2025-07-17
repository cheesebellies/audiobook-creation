@echo off
setlocal

winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements
set "PYTHON_DIR=%LOCALAPPDATA%\Programs\Python\Python311"
set "PATH=%PYTHON_DIR%;%PYTHON_DIR%\Scripts;%PATH%"
start /wait winget install --id=ChrisBagwell.SoX  -e --accept-package-agreements --accept-source-agreements
set "SOX_DIR=%ProgramFiles(x86)%\sox-14-4-2"
set "PATH=%SOX_DIR%;%PATH%"

python -m venv .venv
call .venv\Scripts\activate.bat

python -m pip install --upgrade pip -q --disable-pip-version-check

mkdir books 2>nul
mkdir voices 2>nul

pip install --no-input -r requirements.txt
pause
