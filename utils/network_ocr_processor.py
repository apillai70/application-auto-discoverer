#!/usr/bin/env python3
r"""
Application Auto Discoverer - Standalone Network OCR Processor
==============================================================
Standalone script to process network monitoring screenshots and extract
connection data with duplicate prevention.

Location: C:/Users/AjayPillai/application_auto_discoverer/utils/network_ocr_processor.py
Input: download/ folder (screenshot images)
Output: data_staging/network_connections_consolidated.xlsx

Usage:
    python utils/network_ocr_processor.py
    python utils/network_ocr_processor.py --single image.png
    python utils/network_ocr_processor.py --watch

Author: Application Auto Discoverer Team
"""

import os
import sys
import re
import hashlib
import shutil
import time
import argparse
from datetime import datetime
from pathlib import Path
import logging

# Third-party imports with error handling
try:
    import pandas as pd
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
except ImportError as e:
    print(f"❌ Missing required package: {e}")
    print("Install with: pip install pytesseract pillow opencv-python pandas openpyxl")
    sys.exit(1)

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DOWNLOAD_FOLDER = PROJECT_ROOT / "download"
DATA_STAGING_FOLDER = PROJECT_ROOT / "data_staging"
PROCESSED_FOLDER = DOWNLOAD_FOLDER / "processed"
LOGS_FOLDER = PROJECT_ROOT / "logs"

# OCR Configuration
OCR_CONFIG = {
    'tesseract_cmd': {
        'windows': r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        'fallback': 'tesseract'
    },
    'custom_config': '--oem 3 --psm 6',
    'supported_formats': ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
}

class NetworkOCRProcessor:
    """
    Standalone Network OCR Processor for Application Auto Discoverer
    Processes network monitoring screenshots and consolidates data
    """
    
    def __init__(self):
        self.setup_directories()
        self.setup_logging()
        self.setup_tesseract()
        
        # Output file path
        self.excel_file_path = DATA_STAGING_FOLDER / "network_connections_consolidated.xlsx"
        
        # Load existing data
        self.df_existing = self.load_existing_data()
        
        self.logger.info(f"Network OCR Processor initialized - {len(self.df_existing)} existing records")
        print(f"🚀 Network OCR Processor Ready")
        print(f"📁 Input folder: {DOWNLOAD_FOLDER}")
        print(f"💾 Output file: {self.excel_file_path}")
        print(f"📊 Existing records: {len(self.df_existing)}")
    
    def setup_directories(self):
        """Create necessary directories"""
        directories = [DOWNLOAD_FOLDER, DATA_STAGING_FOLDER, PROCESSED_FOLDER, LOGS_FOLDER]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def setup_logging(self):
        """Setup logging"""
        log_file = LOGS_FOLDER / "network_ocr_processor.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('NetworkOCR')
    
    def setup_tesseract(self):
        """Setup Tesseract OCR"""
        if os.name == 'nt':  # Windows
            tesseract_path = OCR_CONFIG['tesseract_cmd']['windows']
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
            else:
                print("⚠️  Tesserac path not found, using system PATH")
        
        # Test Tesseract
        try:
            version = pytesseract.get_tesseract_version()
            self.logger.info(f"Tesseract OCR v{version} ready")
        except Exception as e:
            self.logger.error(f"Tesseract error: {e}")
            print("❌ Tesseract OCR not found. Please install Tesseract OCR.")
            sys.exit(1)
    
    def load_existing_data(self):
        """Load existing Excel data"""
        try:
            if self.excel_file_path.exists():
                df = pd.read_excel(self.excel_file_path, engine='openpyxl')
                self.logger.info(f"Loaded {len(df)} existing records")
                return df
            else:
                self.logger.info("No existing data file found")
                return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Error loading existing data: {e}")
            return pd.DataFrame()
    
    def preprocess_image(self, image_path):
        """Enhance image for better OCR accuracy"""
        try:
            # Read image
            img = cv2.imread(str(image_path))
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold for better contrast
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Clean up with morphological operations
            kernel = np.ones((1,1), np.uint8)
            processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            return processed
            
        except Exception as e:
            self.logger.error(f"Image preprocessing error: {e}")
            return None
    
    def extract_text_from_image(self, image_path):
        """Extract text using OCR"""
        try:
            processed_img = self.preprocess_image(image_path)
            if processed_img is None:
                return None
            
            # Extract text
            text = pytesseract.image_to_string(processed_img, config=OCR_CONFIG['custom_config'])
            
            self.logger.debug(f"Extracted {len(text)} characters from {image_path.name}")
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"OCR extraction error for {image_path}: {e}")
            return None
    
    def parse_network_monitoring_data(self, text):
        """
        ENHANCED: Parse network monitoring table data with better OCR handling
        Handles IPv6, VMware devices, protocols, and traffic data
        """
        parsed_data = []
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        print(f"🔍 Processing {len(lines)} lines for network data...")
        
        # First, let's see what we're working with
        self.logger.debug(f"Sample lines from OCR:")
        for i, line in enumerate(lines[:5]):
            self.logger.debug(f"  L{i+1}: {line}")
        
        for line_num, line in enumerate(lines, 1):
            # Skip header lines and short lines - be more lenient
            if (len(line) < 15 or 
                any(header in line.lower()[:30] for header in ['ip', 'name', 'protocol', 'bytes', 'peer']) or
                line.startswith('--') or 
                line.count('|') > 4):  # Table separators
                self.logger.debug(f"Skipping L{line_num}: {line[:40]}...")
                continue
            
            try:
                record = self.parse_network_line_enhanced(line, line_num)
                if record:
                    parsed_data.append(record)
                    self.logger.debug(f"✅ L{line_num}: Parsed {record.get('Device_Name', 'Unknown')}")
            except Exception as e:
                self.logger.debug(f"❌ L{line_num}: Parse error - {str(e)}")
                continue
        
        self.logger.info(f"Parsed {len(parsed_data)} network connections")
        return parsed_data
    
    def parse_network_line_enhanced(self, line, line_num):
        """
        ENHANCED: Parse individual network line with multiple fallback strategies
        """
        original_line = line
        
        # Clean common OCR errors
        ocr_fixes = {
            'fe8O': 'fe80',
            'fe8o': 'fe80', 
            'VMvvare': 'VMware',
            'VMware8': 'VMware',
            'VMvvarE': 'VMware',
            'udp;': 'udp:',
            'SSL;': 'SSL:',
            '|': 'I',
        }
        
        for wrong, correct in ocr_fixes.items():
            line = line.replace(wrong, correct)
        
        # Strategy 1: Try original strict IPv6 pattern first
        ipv6_match = re.match(r'^(fe80::[a-f0-9:]+)\s+', line, re.IGNORECASE)
        if ipv6_match:
            ip_address = ipv6_match.group(1)
            remaining = line[len(ipv6_match.group(0)):].strip()
            
            # Use enhanced parsing logic for the rest
            record = self.parse_remaining_fields_enhanced(ip_address, remaining, original_line)
            if record:
                return record
        
        # Strategy 2: Look for IPv6 anywhere in the line
        ipv6_anywhere = re.search(r'\b(fe80::[a-f0-9:]+)\b', line, re.IGNORECASE)
        if ipv6_anywhere:
            ip_address = ipv6_anywhere.group(1)
            # Remove IP from line and treat rest as remaining
            remaining = line.replace(ip_address, '', 1).strip()
            
            record = self.parse_remaining_fields_enhanced(ip_address, remaining, original_line)
            if record:
                return record
        
        # Strategy 3: Look for VMware devices even without IPv6
        vmware_match = re.search(r'(VMware\s+[A-Z0-9]+)', line, re.IGNORECASE)
        if vmware_match:
            device_name = vmware_match.group(1)
            
            # Extract other info
            peer_match = re.search(r'(\d+\.\d+\.\d+\.\d+(?:\([^)]+\))?)', line)
            peer_info = peer_match.group(1) if peer_match else "Unknown Peer"
            
            protocol_match = re.search(r'(SSL:\d+|TLS:\d+|udp:\d+|tcp:\d+|NTP|SNMPv?[123]?)', line, re.IGNORECASE)
            protocol = protocol_match.group(1) if protocol_match else "Unknown"
            
            # Extract numbers for bytes
            numbers = [int(x) for x in re.findall(r'\b\d{1,10}\b', line)]
            bytes_in = numbers[-2] if len(numbers) >= 2 else 0
            bytes_out = numbers[-1] if len(numbers) >= 1 else 0
            
            # Create record even without IPv6
            record = {
                'IP_Address': 'Unknown',
                'Device_Name': device_name,
                'Peer_Info': peer_info,
                'Protocol': protocol,
                'Bytes_In': bytes_in,
                'Bytes_Out': bytes_out,
                'Total_Bytes': bytes_in + bytes_out,
                'Extraction_Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Raw_Line': original_line,
                'Line_Number': line_num,
                'Connection_Hash': hashlib.md5(f"unknown_{device_name}_{protocol}".encode()).hexdigest()
            }
            
            return record
        
        # Strategy 4: If we have substantial numeric data, try to extract what we can
        numbers = [int(x) for x in re.findall(r'\b\d{4,}\b', line)]  # Look for 4+ digit numbers
        if len(numbers) >= 2:
            # Might be a data row, try to extract anything useful
            protocol_match = re.search(r'(SSL:\d+|TLS:\d+|udp:\d+|tcp:\d+|NTP|SNMPv?[123]?)', line, re.IGNORECASE)
            if protocol_match:
                protocol = protocol_match.group(1)
                bytes_in = numbers[-2]
                bytes_out = numbers[-1]
                
                record = {
                    'IP_Address': 'Unknown',
                    'Device_Name': 'Unknown Device',
                    'Peer_Info': 'Unknown Peer',
                    'Protocol': protocol,
                    'Bytes_In': bytes_in,
                    'Bytes_Out': bytes_out,
                    'Total_Bytes': bytes_in + bytes_out,
                    'Extraction_Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'Raw_Line': original_line,
                    'Line_Number': line_num,
                    'Connection_Hash': hashlib.md5(f"unknown_unknown_{protocol}".encode()).hexdigest()
                }
                
                return record
        
        # If nothing worked, log the line for debugging
        self.logger.debug(f"No parsing strategy worked for: {original_line[:50]}...")
        return None
    
    def parse_remaining_fields_enhanced(self, ip_address, remaining, original_line):
        """
        ENHANCED: Parse remaining fields after IP extraction with better error handling
        """
        # Extract device name (VMware, etc.)
        device_patterns = [
            r'(VMware\s+[A-Z0-9]+)',
            r'(Cisco\s+[A-Z0-9]+)',
            r'([A-Za-z]+\s+[A-Z0-9]+)'
        ]
        
        device_name = "Unknown Device"
        for pattern in device_patterns:
            match = re.search(pattern, remaining, re.IGNORECASE)
            if match:
                device_name = match.group(1)
                remaining = remaining.replace(match.group(0), '', 1).strip()
                break
        
        # Extract peer info (IP with hostname)
        peer_patterns = [
            r'(\d+\.\d+\.\d+\.\d+\([^)]+\))',  # IP with hostname in parentheses
            r'(\d+\.\d+\.\d+\.\d+)',          # Just IP address
        ]
        
        peer_info = "Unknown Peer"
        for pattern in peer_patterns:
            match = re.search(pattern, remaining)
            if match:
                peer_info = match.group(1)
                remaining = remaining.replace(match.group(0), '', 1).strip()
                break
        
        # Extract protocol - be more flexible
        protocol_patterns = [
            r'(SSL:\d+)', r'(TLS:\d+)', r'(udp:\d+)', r'(tcp:\d+)',
            r'\b(NTP)\b', r'\b(SNMPv?[123]?)\b', r'\b(TFTP)\b', 
            r'\b(HTTP)\b', r'\b(HTTPS)\b', r'\b(FTP)\b', r'\b(SSH)\b',
            r'\b(DNS)\b', r'\b(DHCP)\b'
        ]
        
        protocol = "Unknown"
        for pattern in protocol_patterns:
            match = re.search(pattern, remaining, re.IGNORECASE)
            if match:
                protocol = match.group(1)
                remaining = remaining.replace(match.group(0), '', 1).strip()
                break
        
        # Extract traffic data (bytes in/out) - be more flexible with number extraction
        numbers = re.findall(r'\b\d+\b', remaining)
        numbers = [int(n) for n in numbers if int(n) < 999999999]  # Filter out unreasonably large numbers
        
        bytes_in = numbers[-2] if len(numbers) >= 2 else 0
        bytes_out = numbers[-1] if len(numbers) >= 1 else 0
        
        # Create record
        record = {
            'IP_Address': ip_address,
            'Device_Name': device_name,
            'Peer_Info': peer_info,
            'Protocol': protocol,
            'Bytes_In': bytes_in,
            'Bytes_Out': bytes_out,
            'Total_Bytes': bytes_in + bytes_out,
            'Extraction_Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Raw_Line': original_line,
            'Connection_Hash': hashlib.md5(f"{ip_address}_{peer_info}_{protocol}".encode()).hexdigest()
        }
        
        return record
    
    def debug_ocr_output(self, image_path):
        """
        DEBUG: Show what OCR is actually extracting
        Call this method to see the raw OCR output
        """
        extracted_text = self.extract_text_from_image(image_path)
        
        if not extracted_text:
            print("❌ No text extracted!")
            return
        
        print(f"📝 OCR Output from {image_path.name}:")
        print("=" * 50)
        print(extracted_text)
        print("=" * 50)
        
        lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]
        print(f"📊 {len(lines)} non-empty lines extracted")
        
        # Quick pattern check
        has_ipv6 = bool(re.search(r'fe80', extracted_text, re.IGNORECASE))
        has_vmware = bool(re.search(r'vmware', extracted_text, re.IGNORECASE))
        has_numbers = bool(re.search(r'\d{4,}', extracted_text))
        
        print(f"🔍 Pattern Detection:")
        print(f"   IPv6 (fe80): {'✅' if has_ipv6 else '❌'}")
        print(f"   VMware: {'✅' if has_vmware else '❌'}")
        print(f"   Large numbers: {'✅' if has_numbers else '❌'}")
        
        return extracted_text
    
    def list_download_files(self):
        """DEBUG: List all files found in download folder"""
        print(f"🔍 Analyzing files in: {DOWNLOAD_FOLDER}")
        print("=" * 50)
        
        all_files = list(DOWNLOAD_FOLDER.iterdir())
        print(f"📁 Total items in folder: {len(all_files)}")
        
        # Show all files
        for file in sorted(all_files):
            if file.is_file():
                size_kb = file.stat().st_size / 1024
                print(f"📄 {file.name} ({size_kb:.1f} KB)")
            else:
                print(f"📁 {file.name}/ (directory)")
        
        # Show what glob patterns find
        print(f"\n🔍 File Detection Results:")
        print("-" * 30)
        
        for ext in OCR_CONFIG['supported_formats']:
            lower_files = list(DOWNLOAD_FOLDER.glob(f"*{ext}"))
            upper_files = list(DOWNLOAD_FOLDER.glob(f"*{ext.upper()}"))
            
            print(f"{ext}: {len(lower_files)} files")
            print(f"{ext.upper()}: {len(upper_files)} files")
            
            if lower_files:
                for f in lower_files:
                    print(f"   📷 {f.name}")
            if upper_files:
                for f in upper_files:
                    print(f"   📷 {f.name}")
            print()
        
        return all_files
    
    def check_duplicates(self, new_data):
        """Check for duplicates using connection hash"""
        if self.df_existing.empty or not new_data:
            return new_data
        
        unique_data = []
        existing_hashes = set(self.df_existing.get('Connection_Hash', []))
        
        for record in new_data:
            connection_hash = record.get('Connection_Hash')
            if connection_hash not in existing_hashes:
                unique_data.append(record)
                existing_hashes.add(connection_hash)
            else:
                self.logger.debug(f"Duplicate connection found: {record.get('IP_Address', 'Unknown')}")
        
        duplicates_found = len(new_data) - len(unique_data)
        if duplicates_found > 0:
            self.logger.info(f"Filtered out {duplicates_found} duplicates")
        
        return unique_data
    
    def save_to_excel(self, new_data):
        """Save data to Excel file"""
        if not new_data:
            self.logger.info("No new data to save")
            return
        
        try:
            df_new = pd.DataFrame(new_data)
            
            # Combine with existing data
            if not self.df_existing.empty:
                df_combined = pd.concat([self.df_existing, df_new], ignore_index=True, sort=False)
            else:
                df_combined = df_new
            
            # Save to Excel
            df_combined.to_excel(self.excel_file_path, index=False, engine='openpyxl')
            
            # Update internal data
            self.df_existing = df_combined
            
            self.logger.info(f"Saved {len(new_data)} new records. Total: {len(df_combined)}")
            
        except Exception as e:
            self.logger.error(f"Error saving to Excel: {e}")
    
    def move_processed_image(self, image_path):
        """Move processed image to processed folder"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name = f"{timestamp}_{image_path.name}"
            dest_path = PROCESSED_FOLDER / new_name
            
            shutil.move(str(image_path), str(dest_path))
            self.logger.info(f"Moved {image_path.name} to processed folder")
            
        except Exception as e:
            self.logger.warning(f"Could not move processed image: {e}")
    
    def process_single_image(self, image_path):
        """Process a single image file"""
        image_path = Path(image_path)
        
        if not image_path.exists():
            print(f"❌ Image not found: {image_path}")
            return 0
        
        print(f"🔍 Processing: {image_path.name}")
        
        try:
            # Extract text
            extracted_text = self.extract_text_from_image(image_path)
            if not extracted_text:
                print("⚠️  No text extracted from image")
                print("💡 Try running debug mode:")
                print(f"   processor.debug_ocr_output(Path('{image_path}'))")
                return 0
            
            # Show basic OCR stats
            lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]
            print(f"   📝 OCR extracted {len(extracted_text)} chars, {len(lines)} lines")
            
            # Parse network data
            parsed_data = self.parse_network_monitoring_data(extracted_text)
            if not parsed_data:
                print("⚠️  No network data found in image")
                print("💡 Run debug to see OCR output:")
                print(f"   processor.debug_ocr_output(Path('{image_path}'))")
                return 0
            
            # Add source info
            for record in parsed_data:
                record['Source_Image'] = image_path.name
                record['Source_Path'] = str(image_path)
            
            # Check duplicates
            unique_data = self.check_duplicates(parsed_data)
            
            # Save to Excel
            self.save_to_excel(unique_data)
            
            # Move processed image
            self.move_processed_image(image_path)
            
            records_added = len(unique_data)
            print(f"✅ Added {records_added} new network connections")
            
            return records_added
            
        except Exception as e:
            self.logger.error(f"Error processing {image_path}: {e}")
            print(f"❌ Error: {e}")
            return 0
    
    def process_download_folder(self):
        """Process all images in download folder - ENHANCED with duplicate prevention"""
        if not DOWNLOAD_FOLDER.exists():
            print(f"❌ Download folder not found: {DOWNLOAD_FOLDER}")
            return
        
        # Find image files with duplicate prevention
        image_files = []
        seen_files = set()  # Track files we've already found
        
        for ext in OCR_CONFIG['supported_formats']:
            # Only search lowercase to avoid case sensitivity issues
            found_files = list(DOWNLOAD_FOLDER.glob(f"*{ext}"))
            
            for file in found_files:
                # Use absolute path to avoid duplicates
                file_key = str(file.resolve()).lower()
                if file_key not in seen_files:
                    image_files.append(file)
                    seen_files.add(file_key)
        
        # Also check for uppercase extensions separately
        for ext in OCR_CONFIG['supported_formats']:
            found_files = list(DOWNLOAD_FOLDER.glob(f"*{ext.upper()}"))
            
            for file in found_files:
                file_key = str(file.resolve()).lower()
                if file_key not in seen_files:
                    image_files.append(file)
                    seen_files.add(file_key)
        
        if not image_files:
            print(f"📁 No images found in {DOWNLOAD_FOLDER}")
            print(f"Supported formats: {', '.join(OCR_CONFIG['supported_formats'])}")
            return
        
        # Show what files were actually found
        print(f"📸 Found {len(image_files)} unique images to process")
        print("📋 Files detected:")
        for i, img_file in enumerate(image_files, 1):
            size_kb = img_file.stat().st_size / 1024
            print(f"   [{i}] {img_file.name} ({size_kb:.1f} KB)")
        
        print("-" * 50)
        
        successful = 0
        total_records = 0
        
        for i, image_file in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] ", end="")
            records_added = self.process_single_image(image_file)
            
            if records_added > 0:
                successful += 1
                total_records += records_added
        
        # Summary
        print("\n" + "=" * 50)
        print("🎉 BATCH PROCESSING COMPLETE!")
        print(f"📊 Successfully processed: {successful}/{len(image_files)} images")
        print(f"📝 Total new records: {total_records}")
        print(f"💾 Output saved to: {self.excel_file_path.relative_to(PROJECT_ROOT)}")
        
        if total_records > 0:
            self.show_summary()
    
    def watch_download_folder(self, check_interval=5):
        """Watch download folder for new images"""
        processed_files = set()
        
        print(f"👀 Watching {DOWNLOAD_FOLDER} for new images...")
        print(f"⏱️  Check interval: {check_interval} seconds")
        print("Press Ctrl+C to stop watching")
        print("-" * 40)
        
        try:
            while True:
                # Find current image files
                current_files = set()
                for ext in OCR_CONFIG['supported_formats']:
                    current_files.update(DOWNLOAD_FOLDER.glob(f"*{ext}"))
                    current_files.update(DOWNLOAD_FOLDER.glob(f"*{ext.upper()}"))
                
                # Process new files
                new_files = current_files - processed_files
                
                for new_file in new_files:
                    print(f"\n🆕 New file detected: {new_file.name}")
                    records_added = self.process_single_image(new_file)
                    
                    if records_added > 0:
                        processed_files.add(new_file)
                        print("✅ Processing complete")
                    else:
                        print("❌ No data extracted")
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n👋 Stopped watching folder")
    
    def show_summary(self):
        """Show summary of accumulated data"""
        if self.df_existing.empty:
            print("📊 No data accumulated yet")
            return
        
        df = self.df_existing
        
        print(f"\n📈 DATA SUMMARY:")
        print(f"🔗 Total network connections: {len(df):,}")
        print(f"📊 Total bytes in: {df['Bytes_In'].sum():,}")
        print(f"📊 Total bytes out: {df['Bytes_Out'].sum():,}")
        print(f"🌐 Unique protocols: {df['Protocol'].nunique()}")
        
        # Top protocols
        if len(df) > 0:
            top_protocols = df['Protocol'].value_counts().head(5)
            print(f"\n🔝 Top protocols:")
            for protocol, count in top_protocols.items():
                print(f"   {protocol}: {count} connections")
        
        # Recent activity
        if 'Extraction_Timestamp' in df.columns and not df.empty:
            latest = df['Extraction_Timestamp'].max()
            print(f"\n🕒 Last update: {latest}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Network OCR Processor for Application Auto Discoverer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  python utils/network_ocr_processor.py
  python utils/network_ocr_processor.py --single screenshot.png
  python utils/network_ocr_processor.py --watch
  python utils/network_ocr_processor.py --summary
  python utils/network_ocr_processor.py --list-files

Folders:
  Input:  {DOWNLOAD_FOLDER}
  Output: {DATA_STAGING_FOLDER}
        """
    )
    
    parser.add_argument('--single', '-s', 
                       help='Process single image file (in download folder)')
    parser.add_argument('--watch', '-w', action='store_true',
                       help='Watch download folder for new images')
    parser.add_argument('--summary', action='store_true',
                       help='Show current data summary')
    parser.add_argument('--list-files', action='store_true',
                       help='List all files in download folder (debug)')
    parser.add_argument('--interval', type=int, default=5,
                       help='Watch interval in seconds (default: 5)')
    
    args = parser.parse_args()
    
    # Initialize processor
    try:
        processor = NetworkOCRProcessor()
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        sys.exit(1)
    
    # Execute action
    if args.single:
        # Process single image
        image_path = DOWNLOAD_FOLDER / args.single
        processor.process_single_image(image_path)
        
    elif args.watch:
        # Watch folder mode
        processor.watch_download_folder(args.interval)
        
    elif args.summary:
        # Show summary only
        processor.show_summary()
        
    elif args.list_files:
        # List files in download folder
        processor.list_download_files()
        
    else:
        # Default: process all images in download folder
        processor.process_download_folder()

if __name__ == "__main__":
    main()