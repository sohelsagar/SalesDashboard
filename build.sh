#!/bin/bash

# Build script for SalesDashboard Windows executable using Wine
# Run this from your Ubuntu machine

set -e  # Exit on error

echo "======================================"
echo "Building SalesDashboard Windows EXE"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/engine/install/ubuntu/"
    exit 1
fi

# Check if required files exist
if [ ! -f "app.py" ]; then
    echo -e "${RED}Error: app.py not found${NC}"
    exit 1
fi

if [ ! -d "shapefiles" ]; then
    echo -e "${RED}Error: shapefiles directory not found${NC}"
    exit 1
fi

# Check for app_icon.ico
if [ ! -f "app_icon.ico" ]; then
    echo -e "${YELLOW}Warning: app_icon.ico not found. Building without custom icon.${NC}"
else
    echo -e "${GREEN}Found app_icon.ico, will use custom icon.${NC}"
fi

# Clean previous builds
echo -e "${GREEN}Cleaning previous builds...${NC}"
rm -rf dist/ build/ *.spec

# Build Docker image (this will take 15-30 minutes on first run)
echo -e "${GREEN}Building Docker image with Wine...${NC}"
echo -e "${YELLOW}This will take 15-30 minutes on first build (downloading Wine + Python for Windows)${NC}"
docker build -t salesdashboard-builder .

if [ $? -ne 0 ]; then
    echo -e "${RED}Docker build failed!${NC}"
    exit 1
fi

# Run Docker container and build the executable
echo -e "${GREEN}Building Windows executable with PyInstaller...${NC}"
echo -e "${YELLOW}This may take 10-20 minutes...${NC}"

if [ -f "app_icon.ico" ]; then
    # Run with icon file mounted
    docker run --rm \
        -v "$(pwd)/dist:/app/dist" \
        -v "$(pwd)/app_icon.ico:/app/app_icon.ico:ro" \
        salesdashboard-builder
else
    # Run without icon
    docker run --rm \
        -v "$(pwd)/dist:/app/dist" \
        salesdashboard-builder
fi

# Check if the executable was created
if [ -f "dist/SalesDashboard.exe" ]; then
    echo -e "${GREEN}======================================"
    echo "Build successful!"
    echo "======================================"
    echo "Executable location: $(pwd)/dist/SalesDashboard.exe"
    echo "Size: $(du -h dist/SalesDashboard.exe | cut -f1)"
    echo ""
    echo "File type check:"
    file dist/SalesDashboard.exe
    echo ""
    echo "To deploy on Windows:"
    echo "1. Copy dist/SalesDashboard.exe to your Windows machine"
    echo "2. Double-click to run"
    echo "3. Your browser will open with the dashboard"
    echo ""
    echo "Note: First run may trigger Windows Defender. Add an exception if needed."
    echo -e "${NC}"
else
    echo -e "${RED}======================================"
    echo "Build failed!"
    echo "Executable not found in dist/ folder"
    echo "Check the output above for errors"
    echo "=====================================${NC}"
    exit 1
fi