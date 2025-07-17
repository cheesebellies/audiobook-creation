@echo off
setlocal

winget install -e --id Python.Python.3.11
winget install --id=ChrisBagwell.SoX  -e

python -m venv .venv
call .venv\Scripts\activate.bat

python -m pip install --upgrade pip

mkdir books 2>nul
mkdir voices 2>nul

pip install -r requirements.txt

