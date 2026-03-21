@echo off
REM Quick fix script for Hospital Management System
REM Installs all dependencies in one command

echo.
echo ======================================
echo Hospital Management System - Quick Fix
echo ======================================
echo.

REM Check if virtual environment exists
if not exist "pp" (
    echo Creating virtual environment...
    python -m venv pp
    echo Virtual environment created.
)

REM Activate virtual environment
echo Activating virtual environment...
call pp\Scripts\activate.bat

REM Install dependencies
echo.
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt -q

echo.
echo ✓ Dependencies installed successfully!
echo.
echo Next steps:
echo 1. Run Django check: python manage.py check
echo 2. Run migrations: python manage.py migrate
echo 3. Create superuser: python manage.py createsuperuser
echo 4. Start server: python manage.py runserver
echo.
echo Visit: http://localhost:8000/admin/
echo.
pause
