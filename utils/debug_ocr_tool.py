#!/usr/bin/env python3
"""
OCR Debug Tool - Troubleshoot text extraction and parsing
"""

import os
import sys
import re
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
except ImportError as e:
    print(f"❌ Missing package: {e}")
    sys.exit(1)

class OCRDebugger:
    """Debug OCR extraction and parsing issues"""
    
    def __init__(self):
        self.setup_tesseract()
    
    def setup_tesseract(self):
        """Setup Tesseract"""
        if os.name == 'nt':  # Windows
            tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    def extract_raw_text(self, image_path, save_debug=True):
        """Extract raw text with different OCR configurations"""
        image_path = Path(image_path)
        print(f"🔍 Analyzing: {image_path.name}")
        print("-" * 50)
        
        # Test different OCR configurations
        configs = [
            ('Default', ''),
            ('Table Mode', '--psm 6'),
            ('Single Block', '--psm 8'),
            ('Raw Line', '--psm 13'),
            ('Table + OEM', '--oem 3 --psm 6'),
            ('High DPI', '--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.:()/')
        ]
        
        best_text = ""
        best_config = ""
        max_length = 0
        
        for name, config in configs:
            try:
                # Process image
                processed_img = self.preprocess_image(image_path)
                
                # Extract text
                text = pytesseract.image_to_string(processed_img, config=config)
                text_length = len(text.strip())
                
                print(f"\n📝 {name} ({config or 'default'}):")
                print(f"   Length: {text_length} characters")
                print(f"   Lines: {len(text.strip().split(chr(10)))}")
                
                if text_length > max_length:
                    max_length = text_length
                    best_text = text
                    best_config = name
                
                # Show first few lines
                lines = text.strip().split('\n')[:5]
                for i, line in enumerate(lines):
                    if line.strip():
                        print(f"   L{i+1}: {line[:80]}{'...' if len(line) > 80 else ''}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print(f"\n🏆 Best result: {best_config} ({max_length} chars)")
        
        # Save debug output
        if save_debug and best_text:
            debug_file = image_path.parent / f"debug_{image_path.stem}_ocr.txt"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(f"OCR Debug Output for {image_path.name}\n")
                f.write(f"Best Config: {best_config}\n")
                f.write("=" * 50 + "\n\n")
                f.write(best_text)
            print(f"💾 Debug output saved: {debug_file.name}")
        
        return best_text
    
    def preprocess_image(self, image_path):
        """Enhanced image preprocessing"""
        # Read image
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Multiple preprocessing approaches
        # 1. Simple threshold
        _, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 2. Adaptive threshold 
        thresh2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # 3. Morphological operations
        kernel = np.ones((1,1), np.uint8)
        morph = cv2.morphologyEx(thresh1, cv2.MORPH_CLOSE, kernel)
        
        # 4. Noise removal
        denoised = cv2.medianBlur(morph, 3)
        
        # Return the best processed version
        return denoised
    
    def test_parsing_patterns(self, text):
        """Test parsing patterns against extracted text"""
        print("\n🔍 Testing Parsing Patterns")
        print("-" * 50)
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        print(f"📊 Found {len(lines)} text lines")
        
        # Test IPv6 pattern
        ipv6_pattern = r'fe80::[a-f0-9:]+'
        ipv6_matches = []
        
        # Test various patterns
        patterns = {
            'IPv6': r'fe80::[a-f0-9:]+',
            'IPv4': r'\d+\.\d+\.\d+\.\d+',
            'VMware': r'VMware\s+[A-Z0-9]+',
            'Protocols': r'(SSL|TLS|udp|tcp|NTP|SNMP):\d+',
            'Numbers': r'\b\d+\b'
        }
        
        for pattern_name, pattern in patterns.items():
            matches = []
            for line_num, line in enumerate(lines, 1):
                found = re.findall(pattern, line, re.IGNORECASE)
                if found:
                    matches.extend([(line_num, match) for match in found])
            
            print(f"\n{pattern_name} matches: {len(matches)}")
            for line_num, match in matches[:5]:  # Show first 5
                print(f"   L{line_num}: {match}")
            if len(matches) > 5:
                print(f"   ... and {len(matches) - 5} more")
        
        # Look for table-like structures
        print(f"\n📋 Table Structure Analysis:")
        table_lines = []
        for line_num, line in enumerate(lines, 1):
            # Count whitespace-separated fields
            fields = line.split()
            if len(fields) >= 5:  # Likely table row
                table_lines.append((line_num, len(fields), line))
        
        print(f"Potential table rows: {len(table_lines)}")
        for line_num, field_count, line in table_lines[:3]:
            print(f"   L{line_num} ({field_count} fields): {line[:80]}{'...' if len(line) > 80 else ''}")
    
    def suggest_fixes(self, text):
        """Suggest fixes based on analysis"""
        print(f"\n💡 Suggestions:")
        
        lines = text.split('\n')
        
        if len(text.strip()) < 100:
            print("❌ Very little text extracted:")
            print("   • Try different image format (PNG vs JPG)")
            print("   • Increase image resolution/DPI")
            print("   • Check image contrast and brightness")
        
        if not re.search(r'fe80::', text):
            print("❌ No IPv6 addresses found:")
            print("   • Image might be cropped or corrupted")
            print("   • OCR might need different preprocessing")
        
        if not re.search(r'VMware', text, re.IGNORECASE):
            print("❌ No VMware devices found:")
            print("   • Check if image contains the expected table")
            print("   • Verify table headers are visible")
        
        # Check for likely OCR errors
        common_errors = [
            ('fe8O', 'fe80'),  # O instead of 0
            ('VMvvare', 'VMware'),  # v instead of w
            ('|', 'I'),  # pipe instead of I
        ]
        
        ocr_errors = []
        for wrong, correct in common_errors:
            if wrong in text:
                ocr_errors.append((wrong, correct))
        
        if ocr_errors:
            print("⚠️  Possible OCR errors detected:")
            for wrong, correct in ocr_errors:
                print(f"   • '{wrong}' should be '{correct}'")

def main():
    """Main debug function"""
    if len(sys.argv) != 2:
        print("Usage: python debug_ocr.py <image_file>")
        print("Example: python debug_ocr.py cap1.png")
        return
    
    image_file = sys.argv[1]
    
    # Look in download folder if not found
    if not os.path.exists(image_file):
        download_folder = Path(__file__).parent.parent / "download"
        image_file = download_folder / image_file
    
    if not os.path.exists(image_file):
        print(f"❌ Image not found: {image_file}")
        return
    
    debugger = OCRDebugger()
    
    # Extract text
    text = debugger.extract_raw_text(image_file)
    
    if text.strip():
        # Test parsing
        debugger.test_parsing_patterns(text)
        
        # Suggest fixes
        debugger.suggest_fixes(text)
    else:
        print("❌ No text extracted at all!")
        print("Check Tesseract installation and image format")

if __name__ == "__main__":
    main()