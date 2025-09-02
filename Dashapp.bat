@echo off
ECHO Starting Streamlit App...

REM Set the path to your Python executable
set "PYTHON_PATH=E:\Code\BPL_Dashboard\architecture_based\venv\Scripts\python.exe"


REM Set the path to your Streamlit app
set "APP_PATH=E:\Code\BPL_Dashboard\architecture_based\app.py"

REM Run the Streamlit app
"%PYTHON_PATH%" -m streamlit run "%APP_PATH%"

pause
