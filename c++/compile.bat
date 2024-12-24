@echo off

:: Set paths
set SOURCE_FILE=cha.cpp
set OUTPUT_FILE=challenge_system.exe
set INCLUDE_PATH=nlohmann

:: Check if g++ is available
where g++ >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo "g++ not found! Please ensure MinGW or GCC is installed and added to the PATH."
    pause
    exit /b 1
)

:: Compile the program
g++ %SOURCE_FILE% -o %OUTPUT_FILE% -I%INCLUDE_PATH%

:: Check if compilation was successful
if %ERRORLEVEL% neq 0 (
    echo "Compilation failed! Check your source code and paths."
    pause
    exit /b 1
)

echo "Compilation successful! Executable created: %OUTPUT_FILE%"
pause