@echo off
REM Network OCR Processor - Easy Runner
REM Save as: C:\Users\AjayPillai\application_auto_discoverer\run_network_ocr.bat

echo =======================================================
echo  Application Auto Discoverer - Network OCR Processor
echo =======================================================
echo.

REM Check if we're in the right directory
if not exist "utils\network_ocr_processor.py" (
    echo ERROR: Script not found!
    echo Make sure you're running this from the project root directory.
    echo Expected: C:\Users\AjayPillai\application_auto_discoverer\
    pause
    exit /b 1
)

REM Check if download folder exists
if not exist "download" (
    echo Creating download folder...
    mkdir download
)

REM Check if images exist in download folder
dir /b download\*.png download\*.jpg download\*.jpeg 2>nul | findstr . >nul
if errorlevel 1 (
    echo.
    echo WARNING: No images found in download\ folder!
    echo Please add your network monitoring screenshots to:
    echo %CD%\download\
    echo.
    echo Supported formats: PNG, JPG, JPEG, TIFF, BMP
    echo.
    choice /C YN /M "Continue anyway (Y/N)"
    if errorlevel 2 exit /b 0
)

echo.
echo Choose an option:
echo 1. Process all images in download folder
echo 2. Process single image
echo 3. Watch folder for new images
echo 4. Show current data summary
echo 5. Exit
echo.

choice /C 12345 /M "Enter your choice (1-5)"

if errorlevel 5 exit /b 0
if errorlevel 4 goto summary
if errorlevel 3 goto watch
if errorlevel 2 goto single
if errorlevel 1 goto batch

:batch
echo.
echo Processing all images in download folder...
echo.
python utils\network_ocr_processor.py
goto end

:single
echo.
set /p imagename="Enter image filename (in download folder): "
echo.
echo Processing single image: %imagename%
echo.
python utils\network_ocr_processor.py --single "%imagename%"
goto end

:watch
echo.
echo Starting watch mode...
echo This will monitor the download folder for new images.
echo Press Ctrl+C to stop.
echo.
python utils\network_ocr_processor.py --watch
goto end

:summary
echo.
echo Showing current data summary...
echo.
python utils\network_ocr_processor.py --summary
goto end

:end
echo.
echo =======================================================
echo Processing complete!
echo.
echo Output file: data_staging\network_connections_consolidated.xlsx
echo Log file: logs\network_ocr_processor.log
echo Processed images: download\processed\
echo.
pause