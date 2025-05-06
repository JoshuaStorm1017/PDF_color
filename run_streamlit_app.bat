@echo off
echo Starting PDF Color Page Analyzer...

:: Change to the directory where this batch file is located
cd /d "%~dp0"

:: Run the Streamlit app
streamlit run app.py

echo Application closed. Press any key to exit...
pause
