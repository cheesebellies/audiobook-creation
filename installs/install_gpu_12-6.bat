@echo off
setlocal

cd /d "%~dp0"
cd ..


winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements
set "PYTHON_BASE=%LOCALAPPDATA%\Programs\Python"
for /d %%i in ("%PYTHON_BASE%\*") do (
    set "PYTHON_DIR=%%i"
    goto :found_python_dir
)
:found_python_dir

set "PATH=%PYTHON_DIR%;%PYTHON_DIR%\Scripts;%PATH%"
start /wait winget install --id=ChrisBagwell.SoX  -e --accept-package-agreements --accept-source-agreements
set "SOX_DIR=%ProgramFiles(x86)%\sox-14-4-2"
set "PATH=%SOX_DIR%;%PATH%"

start /wait winget install -e --id Gyan.FFmpeg --accept-package-agreements --accept-source-agreements

for /d %%A in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\*") do (
    echo %%A | findstr /i "Gyan.FFmpeg_" >nul
    if not errorlevel 1 (
        for /d %%B in ("%%A\*") do (
            set "FFMPEG_DIR=%%B"
            REM Break both loops by forcing an exit here
            goto :loops_done
        )
    )
)

:loops_done
set "PATH=%FFMPEG_DIR%\bin;%PATH%"

python -m venv .venv
call .venv\Scripts\activate.bat

mkdir books 2>nul
mkdir voices 2>nul

python -m pip install --upgrade pip -q --disable-pip-version-check
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu126
pip install --no-input -r requirements.txt
python -m spacy download en_core_web_sm
pause
