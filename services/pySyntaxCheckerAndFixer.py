#!/usr/bin/env python3
"""
Python Syntax Checker and Fixer
Helps identify and fix common syntax issues in Python files
"""

import ast
import sys
import re

def check_python_syntax(filename):
    """Check Python file for syntax errors"""
    
    print(f"🔍 Checking syntax for: {filename}")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to compile the code
        ast.parse(content)
        print("✅ Syntax is valid!")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax Error found:")
        print(f"   Line {e.lineno}: {e.text.strip() if e.text else 'Unknown'}")
        print(f"   Error: {e.msg}")
        print(f"   Position: {' ' * (e.offset - 1) if e.offset else ''}^")
        return False
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

def fix_common_issues(filename):
    """Fix common Python syntax issues"""
    
    print(f"🔧 Attempting to fix common issues in: {filename}")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed_lines = []
        fixes_applied = 0
        
        for i, line in enumerate(lines, 1):
            original_line = line
            
            # Fix 1: Remove invalid docstring syntax like '""":' 
            if '""":' in line:
                line = line.replace('""":"', '"""')
                if line != original_line:
                    print(f"   Fixed line {i}: Removed invalid docstring syntax")
                    fixes_applied += 1
            
            # Fix 2: Convert mixed indentation to spaces
            if line.startswith('\t'):
                spaces = '    ' * line.count('\t')
                line = line.replace('\t', '', line.count('\t')) 
                line = spaces + line
                if line != original_line:
                    print(f"   Fixed line {i}: Converted tabs to spaces")
                    fixes_applied += 1
            
            # Fix 3: Fix markdown headers in docstrings (change ## to #)
            if '##' in line and ('"""' in ''.join(lines[max(0, i-5):i]) or 
                                "'''" in ''.join(lines[max(0, i-5):i])):
                line = line.replace('##', '#')
                if line != original_line:
                    print(f"   Fixed line {i}: Fixed markdown in docstring")
                    fixes_applied += 1
            
            # Fix 4: Remove invalid characters in comments
            if line.strip().startswith('#') and '*' in line:
                # Remove markdown bold formatting from comments
                line = re.sub(r'\*([^*]+)\*', r'\1', line)
                if line != original_line:
                    print(f"   Fixed line {i}: Cleaned comment formatting")
                    fixes_applied += 1
            
            fixed_lines.append(line)
        
        if fixes_applied > 0:
            # Backup original file
            backup_filename = filename + '.backup'
            with open(backup_filename, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"📄 Created backup: {backup_filename}")
            
            # Write fixed file
            with open(filename, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)
            
            print(f"✅ Applied {fixes_applied} fixes to {filename}")
            return True
        else:
            print("ℹ️ No common issues found to fix")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing file: {e}")
        return False

def validate_indentation(filename):
    """Check for indentation issues"""
    
    print(f"📏 Checking indentation in: {filename}")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        issues = []
        
        for i, line in enumerate(lines, 1):
            # Check for mixed tabs and spaces
            if '\t' in line and ' ' * 4 in line:
                issues.append(f"Line {i}: Mixed tabs and spaces")
            
            # Check for odd indentation (not multiple of 4)
            if line.startswith(' '):
                leading_spaces = len(line) - len(line.lstrip(' '))
                if leading_spaces % 4 != 0:
                    issues.append(f"Line {i}: Indentation not multiple of 4 ({leading_spaces} spaces)")
        
        if issues:
            print("❌ Indentation issues found:")
            for issue in issues[:10]:  # Show first 10 issues
                print(f"   {issue}")
            if len(issues) > 10:
                print(f"   ... and {len(issues) - 10} more issues")
            return False
        else:
            print("✅ Indentation looks good!")
            return True
            
    except Exception as e:
        print(f"❌ Error checking indentation: {e}")
        return False

def main():
    """Main function"""
    
    if len(sys.argv) != 2:
        print("Usage: python syntax_checker.py <python_file>")
        print("Example: python syntax_checker.py enhancedDiagramGeneratorFinal.py")
        return
    
    filename = sys.argv[1]
    
    print("🐍 Python Syntax Checker and Fixer")
    print("=" * 40)
    
    # Step 1: Check current syntax
    syntax_ok = check_python_syntax(filename)
    
    if not syntax_ok:
        print("\n🔧 Attempting to fix common issues...")
        
        # Step 2: Try to fix common issues
        fixes_applied = fix_common_issues(filename)
        
        if fixes_applied:
            print("\n🔍 Re-checking syntax after fixes...")
            syntax_ok = check_python_syntax(filename)
    
    # Step 3: Check indentation
    print("\n" + "=" * 40)
    validate_indentation(filename)
    
    # Step 4: Final result
    print("\n" + "=" * 40)
    if syntax_ok:
        print("🎉 File is ready to run!")
        print(f"✅ Try: python {filename} --help")
    else:
        print("❌ File still has syntax errors")
        print("💡 Manual fixes may be needed")

if __name__ == "__main__":
    main()