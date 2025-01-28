@echo off
echo Setting up Python environment...

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    python -m venv venv
    echo Created virtual environment
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements (if any)
pip install -r requirements.txt

echo Environment setup complete!
echo.
echo To activate the environment, run:
echo     venv\Scripts\activate.bat
echo.
echo To run the random number generator:
echo     python random_generator.py 