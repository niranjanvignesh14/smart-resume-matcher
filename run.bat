@echo off
where py >nul 2>nul
if %errorlevel%==0 (
    set PYCMD=py
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set PYCMD=python
    ) else (
        echo Python was not found on this computer.
        echo Install it from https://www.python.org/downloads/ and make sure
        echo to check "Add python.exe to PATH" during setup, then try again.
        pause
        exit /b 1
    )
)

if "%GEMINI_API_KEY%"=="" (
    set /p GEMINI_API_KEY="Paste your Gemini API key: "
)

echo Installing dependencies (first run only, may take a minute)...
%PYCMD% -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo INSTALL FAILED - see the error above.
    pause
    exit /b 1
)

echo Starting the app...
%PYCMD% -m streamlit run app.py
if errorlevel 1 (
    echo.
    echo APP FAILED TO START - see the error above.
    pause
    exit /b 1
)

pause
