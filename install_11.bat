@echo off
setlocal

winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements
start /wait winget install --id=ChrisBagwell.SoX  -e --accept-package-agreements --accept-source-agreements

python -m venv .venv
call .venv\Scripts\activate.bat

python -m pip install --upgrade pip -q --disable-pip-version-check

mkdir books 2>nul
mkdir voices 2>nul

pip install --no-input -r requirements.txt
pause
