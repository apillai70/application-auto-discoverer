#!/bin/bash
# Network OCR Processor Setup Script
# Save as: C:/Users/AjayPillai/application_auto_discoverer/setup_ocr.sh
# Usage: bash setup_ocr.sh (from Git Bash)

echo "======================================================="
echo "  Network OCR Processor - Setup Script"
echo "======================================================="
echo

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if we're in the right directory
if [[ ! "$(pwd)" =~ application_auto_discoverer$ ]]; then
    echo -e "${YELLOW}WARNING: You may not be in the correct directory${NC}"
    echo "Expected to be in: application_auto_discoverer"
    echo "Current directory: $(pwd)"
    echo
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

echo -e "${BLUE}Creating directory structure...${NC}"

# Create necessary directories
directories=("utils" "download" "download/processed" "data_staging" "logs")

for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo -e "${GREEN}✓ Created: $dir/${NC}"
    else
        echo -e "${YELLOW}✓ Exists: $dir/${NC}"
    fi
done

echo
echo -e "${BLUE}Checking Python installation...${NC}"

# Check Python
if command -v python >/dev/null 2>&1; then
    python_version=$(python --version 2>&1)
    echo -e "${GREEN}✓ Python found: $python_version${NC}"
elif command -v python3 >/dev/null 2>&1; then
    python_version=$(python3 --version 2>&1)
    echo -e "${GREEN}✓ Python3 found: $python_version${NC}"
    echo -e "${YELLOW}Note: You may need to use 'python3' instead of 'python'${NC}"
else
    echo -e "${RED}✗ Python not found${NC}"
    echo "Please install Python from https://python.org"
    exit 1
fi

echo
echo -e "${BLUE}Checking pip installation...${NC}"

# Check pip
if command -v pip >/dev/null 2>&1; then
    echo -e "${GREEN}✓ pip found${NC}"
    pip_cmd="pip"
elif command -v pip3 >/dev/null 2>&1; then
    echo -e "${GREEN}✓ pip3 found${NC}"
    pip_cmd="pip3"
else
    echo -e "${RED}✗ pip not found${NC}"
    echo "Please install pip"
    exit 1
fi

echo
echo -e "${BLUE}Checking required Python packages...${NC}"

# Required packages
packages=("pandas" "openpyxl" "pillow" "opencv-python" "pytesseract")
missing_packages=()

for package in "${packages[@]}"; do
    if python -c "import ${package//-/_}" 2>/dev/null; then
        echo -e "${GREEN}✓ $package${NC}"
    else
        echo -e "${RED}✗ $package (missing)${NC}"
        missing_packages+=("$package")
    fi
done

# Install missing packages
if [ ${#missing_packages[@]} -gt 0 ]; then
    echo
    echo -e "${YELLOW}Installing missing packages...${NC}"
    
    for package in "${missing_packages[@]}"; do
        echo -e "${BLUE}Installing $package...${NC}"
        $pip_cmd install "$package"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Successfully installed $package${NC}"
        else
            echo -e "${RED}✗ Failed to install $package${NC}"
        fi
    done
fi

echo
echo -e "${BLUE}Checking Tesseract OCR...${NC}"

# Check Tesseract
tesseract_paths=(
    "/c/Program Files/Tesseract-OCR/tesseract.exe"
    "/usr/bin/tesseract"
    "/usr/local/bin/tesseract"
    "/opt/homebrew/bin/tesseract"
)

tesseract_found=false
for path in "${tesseract_paths[@]}"; do
    if [ -f "$path" ]; then
        echo -e "${GREEN}✓ Tesseract found at: $path${NC}"
        tesseract_found=true
        break
    fi
done

if [ "$tesseract_found" = false ]; then
    # Try tesseract in PATH
    if command -v tesseract >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Tesseract found in PATH${NC}"
        tesseract_found=true
    fi
fi

if [ "$tesseract_found" = false ]; then
    echo -e "${RED}✗ Tesseract OCR not found${NC}"
    echo "Please install Tesseract OCR:"
    echo "Windows: https://github.com/UB-Mannheim/tesseract/wiki"
    echo "Linux: sudo apt-get install tesseract-ocr"
    echo "Mac: brew install tesseract"
else
    # Test tesseract
    if python -c "import pytesseract; print('Tesseract version:', pytesseract.get_tesseract_version())" 2>/dev/null; then
        echo -e "${GREEN}✓ Tesseract integration working${NC}"
    else
        echo -e "${YELLOW}⚠ Tesseract found but integration may need configuration${NC}"
    fi
fi

echo
echo -e "${BLUE}Checking required files...${NC}"

# Check if main script exists
if [ -f "utils/network_ocr_processor.py" ]; then
    echo -e "${GREEN}✓ Main script: utils/network_ocr_processor.py${NC}"
else
    echo -e "${RED}✗ Main script missing: utils/network_ocr_processor.py${NC}"
    echo "Please save the network_ocr_processor.py script to the utils/ folder"
fi

# Check if shell runner exists
if [ -f "run_network_ocr.sh" ]; then
    echo -e "${GREEN}✓ Shell runner: run_network_ocr.sh${NC}"
    # Make executable
    chmod +x run_network_ocr.sh
else
    echo -e "${YELLOW}⚠ Shell runner missing: run_network_ocr.sh${NC}"
    echo "Save the run_network_ocr.sh script to the project root"
fi

echo
echo "======================================================="
echo -e "${GREEN}Setup Summary:${NC}"
echo "======================================================="

# Create a simple test
echo -e "${BLUE}Testing setup...${NC}"

test_passed=true

# Test Python imports
if python -c "
import pandas as pd
import pytesseract
from PIL import Image
import cv2
import numpy as np
print('✓ All Python packages imported successfully')
" 2>/dev/null; then
    echo -e "${GREEN}✓ Python environment ready${NC}"
else
    echo -e "${RED}✗ Python environment has issues${NC}"
    test_passed=false
fi

echo
if [ "$test_passed" = true ]; then
    echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
    echo
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Add your network monitoring screenshots to: download/"
    echo "2. Run: bash run_network_ocr.sh"
    echo "3. Check results in: data_staging/network_connections_consolidated.xlsx"
    echo
    echo -e "${BLUE}Quick test:${NC}"
    echo "bash run_network_ocr.sh"
else
    echo -e "${RED}⚠ Setup completed with warnings${NC}"
    echo "Please resolve the issues above before running the OCR processor"
fi

echo
read -p "Press Enter to exit..."