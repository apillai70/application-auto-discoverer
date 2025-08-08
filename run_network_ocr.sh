#!/bin/bash
# Network OCR Processor - Shell Script Runner
# Save as: C:/Users/AjayPillai/application_auto_discoverer/run_network_ocr.sh
# Usage: bash run_network_ocr.sh (from Git Bash)

echo "======================================================="
echo "  Application Auto Discoverer - Network OCR Processor"
echo "======================================================="
echo

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "utils/network_ocr_processor.py" ]; then
    echo -e "${RED}ERROR: Script not found!${NC}"
    echo "Make sure you're running this from the project root directory."
    echo "Expected: C:/Users/AjayPillai/application_auto_discoverer/"
    echo
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if download folder exists
if [ ! -d "download" ]; then
    echo -e "${YELLOW}Creating download folder...${NC}"
    mkdir -p download
fi

# Check if images exist in download folder
image_count=$(find download -maxdepth 1 -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.tiff" -o -iname "*.bmp" \) | wc -l)

if [ "$image_count" -eq 0 ]; then
    echo
    echo -e "${YELLOW}WARNING: No images found in download/ folder!${NC}"
    echo "Please add your network monitoring screenshots to:"
    echo "$(pwd)/download/"
    echo
    echo "Supported formats: PNG, JPG, JPEG, TIFF, BMP"
    echo
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
else
    echo -e "${GREEN}Found $image_count image(s) in download folder${NC}"
fi

echo
echo "Choose an option:"
echo "1. Process all images in download folder"
echo "2. Process single image"
echo "3. Watch folder for new images"
echo "4. Show current data summary"
echo "5. Open output folder"
echo "6. View logs"
echo "7. Exit"
echo

while true; do
    read -p "Enter your choice (1-7): " choice
    case $choice in
        1)
            echo
            echo -e "${BLUE}Processing all images in download folder...${NC}"
            echo "=============================================="
            python utils/network_ocr_processor.py
            break
            ;;
        2)
            echo
            # List available images
            echo -e "${BLUE}Available images in download folder:${NC}"
            find download -maxdepth 1 -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.tiff" -o -iname "*.bmp" \) -printf "%f\n" | head -10
            echo
            read -p "Enter image filename: " imagename
            if [ -f "download/$imagename" ]; then
                echo
                echo -e "${BLUE}Processing single image: $imagename${NC}"
                echo "========================================"
                python utils/network_ocr_processor.py --single "$imagename"
            else
                echo -e "${RED}Error: Image not found in download folder${NC}"
            fi
            break
            ;;
        3)
            echo
            echo -e "${BLUE}Starting watch mode...${NC}"
            echo "This will monitor the download folder for new images."
            echo "Press Ctrl+C to stop."
            echo "========================================"
            python utils/network_ocr_processor.py --watch
            break
            ;;
        4)
            echo
            echo -e "${BLUE}Showing current data summary...${NC}"
            echo "================================="
            python utils/network_ocr_processor.py --summary
            break
            ;;
        5)
            echo
            echo -e "${BLUE}Opening output folder...${NC}"
            if [ -d "data_staging" ]; then
                # Try to open folder in Windows Explorer (works in Git Bash)
                explorer.exe "$(cygpath -w "$(pwd)/data_staging")" 2>/dev/null || \
                start "$(pwd)/data_staging" 2>/dev/null || \
                echo "Output folder: $(pwd)/data_staging"
                if [ -f "data_staging/network_connections_consolidated.xlsx" ]; then
                    echo -e "${GREEN}✓ Output file exists: network_connections_consolidated.xlsx${NC}"
                else
                    echo -e "${YELLOW}⚠ No output file found yet${NC}"
                fi
            else
                echo -e "${YELLOW}Output folder doesn't exist yet. Run processing first.${NC}"
            fi
            ;;
        6)
            echo
            echo -e "${BLUE}Recent log entries:${NC}"
            echo "==================="
            if [ -f "logs/network_ocr_processor.log" ]; then
                tail -20 "logs/network_ocr_processor.log"
            else
                echo -e "${YELLOW}No log file found yet.${NC}"
            fi
            echo
            read -p "Press Enter to continue..."
            continue
            ;;
        7)
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Please enter 1-7.${NC}"
            ;;
    esac
done

echo
echo "======================================================="
echo -e "${GREEN}Processing complete!${NC}"
echo
echo -e "${BLUE}📊 Output file:${NC} data_staging/network_connections_consolidated.xlsx"
echo -e "${BLUE}📋 Log file:${NC} logs/network_ocr_processor.log"
echo -e "${BLUE}📁 Processed images:${NC} download/processed/"
echo

# Show quick stats if output file exists
if [ -f "data_staging/network_connections_consolidated.xlsx" ]; then
    echo -e "${GREEN}✓ Output file successfully created${NC}"
    
    # Try to show file size
    if command -v stat >/dev/null 2>&1; then
        filesize=$(stat -c%s "data_staging/network_connections_consolidated.xlsx" 2>/dev/null || stat -f%z "data_staging/network_connections_consolidated.xlsx" 2>/dev/null)
        if [ ! -z "$filesize" ]; then
            echo -e "${BLUE}📈 File size:${NC} $(($filesize / 1024)) KB"
        fi
    fi
fi

echo
read -p "Press Enter to exit..."