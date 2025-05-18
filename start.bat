@echo off
REM start.bat: Activates environment and runs the app

REM Activate virtual environment
call .\.venv\Scripts\activate.bat

REM Run application
python app.py