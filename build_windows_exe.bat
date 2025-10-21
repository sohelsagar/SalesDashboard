@echo off
REM Sales Dashboard - Windows EXE Build Script
REM This script builds a standalone Windows executable using Docker and PyInstaller

setlocal enabledelayedexpansion

echo.
echo ====================================================
echo Sales Dashboard - Windows EXE Builder
echo ====================================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed or not in PATH
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo Docker found: 
docker --version
echo.

REM Check if shapefiles folder exists
if not exist "shapefiles" (
    echo ERROR: shapefiles folder not found in current directory
    echo Please create a 'shapefiles' folder and add your .shp, .shx, .dbf, .prj files
    pause
    exit /b 1
)

echo Checking shapefile contents...
if not exist "shapefiles\adm01.shp" (
    echo WARNING: adm01.shp not found in shapefiles folder
)
if not exist "shapefiles\adm01.shx" (
    echo WARNING: adm01.shx not found in shapefiles folder
)
if not exist "shapefiles\adm01.dbf" (
    echo WARNING: adm01.dbf not found in shapefiles folder
)
echo.

REM Check if app.py exists
if not exist "app.py" (
    echo ERROR: app.py not found in current directory
    pause
    exit /b 1
)

echo app.py found
echo.

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found in current directory
    pause
    exit /b 1
)

echo requirements.txt found
echo.

REM Create dist folder
if not exist "dist" (
    echo Creating dist folder...
    mkdir dist
    echo dist folder created
)
echo.

echo ====================================================
echo Building Docker image...
echo ====================================================
echo This may take 5-10 minutes on first run
echo.

docker build -t sales-dashboard-builder .

if %errorlevel% neq 0 (
    echo ERROR: Docker build failed
    pause
    exit /b 1
)

echo.
echo ====================================================
echo Running PyInstaller to create Windows EXE...
echo ====================================================
echo This may take another 10-20 minutes
echo.

docker run --rm -v "%cd%\dist:/app/dist" sales-dashboard-builder

if %errorlevel% neq 0 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)

echo.
echo ====================================================
echo Build Complete!
echo ====================================================
echo.

REM Check if EXE was created
if exist "dist\SalesDashboard.exe" (
    echo SUCCESS: SalesDashboard.exe created successfully!
    echo.
    echo Location: %cd%\dist\SalesDashboard.exe
    echo Size: 
    for %%A in (dist\SalesDashboard.exe) do echo %%~zA bytes
    echo.
    echo Next steps:
    echo 1. Test the EXE on this machine by double-clicking it
    echo 2. Copy the EXE to other computers to distribute
    echo 3. No additional installation required on target machines
    echo.
) else (
    echo ERROR: SalesDashboard.exe was not created
    echo Please check the build output above for errors
)

echo.
pause