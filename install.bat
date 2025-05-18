@echo off
REM install.bat: Sets up virtual environment and installs dependencies

REM Create virtual environment
py -m venv .venv

REM Activate environment
call .\.venv\Scripts\activate.bat

REM Upgrade pip and install
pip install --upgrade pip
pip install -r requirements.txt

echo Setup complete. Use '.\.venv\Scripts\activate.bat' and 'start.bat' to launch.