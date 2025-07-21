@echo off
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting SSH Connection Tester...
python ssh_connection_tester.py
pause
