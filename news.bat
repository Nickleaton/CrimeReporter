@echo off
REM Get the directory of this batch file (assumes it is in project root)
SET SCRIPT_DIR=%~dp0

REM Ensure project root is in PYTHONPATH
SET PYTHONPATH=%SCRIPT_DIR%

REM Run the Python script with all arguments (%*)
python "%SCRIPT_DIR%scripts\news.py" %*