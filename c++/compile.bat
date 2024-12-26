@echo off

:: Set paths
set SOURCE_FILE=main.cpp 
set OUTPUT_FILE=challenge_system.exe

:: Check if g++ is available
where g++ >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo "g++ not found! Please ensure MinGW or GCC is installed and added to the PATH."
    pause
    exit /b 1
)

:: Compile the program
g++ %SOURCE_FILE% -o %OUTPUT_FILE%

:: Check if compilation was successful
if %ERRORLEVEL% neq 0 (
    echo "Compilation failed! Check your source code and paths."
    pause
    exit /b 1
)

echo "Compilation successful! Executable created: %OUTPUT_FILE%"
pause