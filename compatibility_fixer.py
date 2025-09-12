#!/usr/bin/env python3
"""
Fixed Compatibility Fixer - Windows Compatible
==============================================
Automatically fixes compatibility issues between auth, audit, and other modules
Fixed for Windows Unicode issues and improved fix logic
"""

import os
import re
import ast
import sys
from pathlib import Path
from typing import Dict, List, Any, Set
from datetime import datetime
import importlib.util

class CompatibilityFixer:
    """Fix compatibility issues between modules"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.routers_dir = self.project_root / "routers"
        self.storage_dir = self.project_root / "storage"
        self.issues_found = []
        self.fixes_applied = []
        
    def scan_for_issues(self) -> Dict[str, List[str]]:
        """Scan all modules for compatibility issues"""
        issues = {
            "missing_imports": [],
            "auth_integration": [],
            "pydantic_issues": [],
            "async_issues": [],
            "dependency_issues": []
        }
        
        print("Scanning for compatibility issues...")
        
        # Scan router files
        if self.routers_dir.exists():
            for py_file in self.routers_dir.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                    
                file_issues = self.scan_file(py_file)
                for category, file_specific_issues in file_issues.items():
                    issues[category].extend(file_specific_issues)
        
        # Scan storage files
        if self.storage_dir.exists():
            for py_file in self.storage_dir.glob("*.py"):
                file_issues = self.scan_file(py_file)
                for category, file_specific_issues in file_issues.items():
                    issues[category].extend(file_specific_issues)
        
        # Scan main.py
        main_file = self.project_root / "main.py"
        if main_file.exists():
            file_issues = self.scan_file(main_file)
            for category, file_specific_issues in file_issues.items():
                issues[category].extend(file_specific_issues)
        
        self.issues_found = issues
        return issues
    
    def scan_file(self, file_path: Path) -> Dict[str, List[str]]:
        """Scan a single file for issues"""
        issues = {
            "missing_imports": [],
            "auth_integration": [],
            "pydantic_issues": [],
            "async_issues": [],
            "dependency_issues": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for Pydantic issues
            pydantic_issues = self.check_pydantic_issues(content, file_path)
            issues["pydantic_issues"].extend(pydantic_issues)
            
            # Check for async issues
            async_issues = self.check_async_issues(content, file_path)
            issues["async_issues"].extend(async_issues)
            
            # Check for auth integration issues (skip auth.py itself)
            if file_path.name != "auth.py":
                auth_issues = self.check_auth_integration_issues(content, file_path)
                issues["auth_integration"].extend(auth_issues)
            
            # Check for missing imports
            import_issues = self.check_missing_imports(content, file_path)
            issues["missing_imports"].extend(import_issues)
            
            # Check for dependency issues
            dep_issues = self.check_dependency_issues(content, file_path)
            issues["dependency_issues"].extend(dep_issues)
            
        except Exception as e:
            print(f"Warning: Error scanning {file_path}: {e}")
        
        return issues
    
    def check_pydantic_issues(self, content: str, file_path: Path) -> List[str]:
        """Check for Pydantic compatibility issues"""
        issues = []
        
        # Check for deprecated regex parameter
        if re.search(r'Field\([^)]*regex\s*=', content):
            issues.append(f"{file_path}: Uses deprecated 'regex' parameter in Field() - should be 'pattern'")
        
        return issues
    
    def check_async_issues(self, content: str, file_path: Path) -> List[str]:
        """Check for async/await issues"""
        issues = []
        
        # Check for asyncio.create_task() in __init__
        if re.search(r'def __init__.*\n[^}]*asyncio\.create_task', content, re.DOTALL):
            issues.append(f"{file_path}: Uses asyncio.create_task() in __init__ - can cause event loop issues")
        
        return issues
    
    def check_auth_integration_issues(self, content: str, file_path: Path) -> List[str]:
        """Check for authentication integration issues"""
        issues = []
        
        # Check if file uses auth functions without importing them
        auth_functions = ['verify_token', 'get_current_user', 'check_permission', 'require_admin']
        for func in auth_functions:
            if func in content:
                if not re.search(rf'from.*auth.*import.*{func}', content):
                    if 'routers.auth' not in content and 'from .auth' not in content:
                        issues.append(f"{file_path}: Uses {func} but doesn't import from auth module")
        
        return issues
    
    def check_missing_imports(self, content: str, file_path: Path) -> List[str]:
        """Check for missing imports - SIMPLE VERSION"""
        issues = []
        
        # Common missing imports
        import_checks = {
            'HTTPException': ('fastapi', 'HTTPException'),
            'Depends': ('fastapi', 'Depends'), 
            'APIRouter': ('fastapi', 'APIRouter'),
            'BaseModel': ('pydantic', 'BaseModel'),
            'Field': ('pydantic', 'Field'),
            'List[': ('typing', 'List'),
            'Dict[': ('typing', 'Dict'),
            'Optional[': ('typing', 'Optional'),
            'datetime': ('datetime', 'datetime'),
            'timedelta': ('datetime', 'timedelta')
        }
        
        for pattern, (module, import_name) in import_checks.items():
            if pattern in content:
                # Simple string checks for imports
                import_found = (
                    f'from {module} import' in content and import_name in content
                ) or (
                    f'import {module}' in content
                )
                
                if not import_found:
                    issues.append(f"{file_path}: Uses {pattern} but missing import: from {module} import {import_name}")
        
        return issues
    
    def check_dependency_issues(self, content: str, file_path: Path) -> List[str]:
        """Check for dependency issues"""
        issues = []
        
        # Check if audit router depends on auth but doesn't declare it
        if 'audit' in str(file_path) and 'Depends(' in content:
            if 'auth' not in content.lower() and 'verify_token' not in content:
                issues.append(f"{file_path}: Audit router uses Depends() but no auth integration found")
        
        return issues
    
    def fix_pydantic_issues(self) -> List[str]:
        """Fix Pydantic compatibility issues"""
        fixes = []
        
        for issue in self.issues_found.get("pydantic_issues", []):
            if "regex" in issue and "pattern" in issue:
                file_path_str = issue.split(":")[0]
                file_path = Path(file_path_str)
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Replace regex= with pattern=
                        old_pattern = r'(Field\([^)]*?)regex(\s*=\s*["\'][^"\']*["\'])'
                        new_content = re.sub(old_pattern, r'\1pattern\2', content)
                        
                        if new_content != content:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            fixes.append(f"Fixed Pydantic regex -> pattern in {file_path}")
                    except Exception as e:
                        print(f"Error fixing Pydantic issue in {file_path}: {e}")
        
        return fixes
    
    def fix_async_issues(self) -> List[str]:
        """Fix async/await issues"""
        fixes = []
        
        for issue in self.issues_found.get("async_issues", []):
            if "asyncio.create_task() in __init__" in issue:
                file_path_str = issue.split(":")[0]
                file_path = Path(file_path_str)
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Replace asyncio.create_task with lazy initialization
                        if 'asyncio.create_task(self._initialize_storage())' in content:
                            old_line = 'asyncio.create_task(self._initialize_storage())'
                            new_lines = '''# Lazy initialization flags
        self._initialized = False
        self._initialization_lock = asyncio.Lock()
        
        # Initialize storage synchronously (directory creation only)
        self._ensure_directories_exist()'''
                            
                            new_content = content.replace(old_line, new_lines)
                            
                            # Add lazy initialization method if not present
                            if '_ensure_initialized' not in content:
                                lazy_method = '''
    async def _ensure_initialized(self):
        """Ensure storage is initialized (lazy initialization)"""
        if not self._initialized:
            async with self._initialization_lock:
                if not self._initialized:
                    await self._initialize_storage()
                    self._initialized = True
    
    def _ensure_directories_exist(self):
        """Ensure required directories exist (synchronous)"""
        try:
            self.audit_dir.mkdir(parents=True, exist_ok=True)
            self.events_dir.mkdir(parents=True, exist_ok=True)
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.reports_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error creating directories: {e}")'''
                                
                                # Insert before the last method
                                lines = new_content.split('\n')
                                for i in range(len(lines) - 1, 0, -1):
                                    if lines[i].strip().startswith('def ') and not lines[i].strip().startswith('def __'):
                                        lines.insert(i, lazy_method)
                                        break
                                new_content = '\n'.join(lines)
                            
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            fixes.append(f"Fixed async initialization in {file_path}")
                    except Exception as e:
                        print(f"Error fixing async issue in {file_path}: {e}")
        
        return fixes
    
    def fix_missing_imports(self) -> List[str]:
        """Fix missing imports"""
        fixes = []
        
        for issue in self.issues_found.get("missing_imports", []):
            file_path_str = issue.split(":")[0]
            file_path = Path(file_path_str)
            
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract the required import from the issue
                    if "missing import:" in issue:
                        required_import = issue.split("missing import:")[-1].strip()
                        
                        # Check if import already exists (case-insensitive)
                        if required_import.lower() not in content.lower():
                            # Add the import at the top after existing imports
                            lines = content.split('\n')
                            insert_index = 0
                            
                            # Find the best place to insert (after last import)
                            for i, line in enumerate(lines):
                                if line.strip().startswith(('from ', 'import ')):
                                    insert_index = i + 1
                                elif line.strip() and not line.strip().startswith('#'):
                                    break
                            
                            lines.insert(insert_index, required_import)
                            new_content = '\n'.join(lines)
                            
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            fixes.append(f"Added missing import to {file_path.name}: {required_import}")
                except Exception as e:
                    print(f"Error fixing import in {file_path}: {e}")
        
        return fixes
    
    def apply_all_fixes(self) -> Dict[str, Any]:
        """Apply all available fixes"""
        print("Applying compatibility fixes...")
        
        all_fixes = []
        
        # Fix Pydantic issues
        pydantic_fixes = self.fix_pydantic_issues()
        all_fixes.extend(pydantic_fixes)
        
        # Fix async issues
        async_fixes = self.fix_async_issues()
        all_fixes.extend(async_fixes)
        
        # Fix missing imports
        import_fixes = self.fix_missing_imports()
        all_fixes.extend(import_fixes)
        
        self.fixes_applied = all_fixes
        
        return {
            "total_fixes": len(all_fixes),
            "pydantic_fixes": len(pydantic_fixes),
            "async_fixes": len(async_fixes),
            "import_fixes": len(import_fixes),
            "details": all_fixes
        }
    
    def generate_compatibility_report(self) -> str:
        """Generate a comprehensive compatibility report"""
        report = []
        report.append("COMPATIBILITY REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Project Root: {self.project_root}")
        report.append("")
        
        # Issues summary
        total_issues = sum(len(issues) for issues in self.issues_found.values())
        report.append(f"ISSUES FOUND: {total_issues}")
        for category, issues in self.issues_found.items():
            if issues:
                report.append(f"  {category}: {len(issues)}")
        report.append("")
        
        # Show first few issues in each category
        for category, issues in self.issues_found.items():
            if issues:
                report.append(f"{category.upper().replace('_', ' ')}")
                report.append("-" * 30)
                for issue in issues[:5]:  # Show first 5 issues
                    report.append(f"  - {issue}")
                if len(issues) > 5:
                    report.append(f"  ... and {len(issues) - 5} more")
                report.append("")
        
        # Fixes applied
        if self.fixes_applied:
            report.append(f"FIXES APPLIED: {len(self.fixes_applied)}")
            report.append("-" * 30)
            for fix in self.fixes_applied:
                report.append(f"  - {fix}")
            report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 30)
        report.append("  - Review remaining missing imports manually")
        report.append("  - Test the application after fixes")
        report.append("  - Consider adding proper import organization")
        report.append("")
        
        return "\n".join(report)

def main():
    """Main compatibility fixing function"""
    fixer = CompatibilityFixer()
    
    print("SCANNING FOR COMPATIBILITY ISSUES")
    print("=" * 40)
    
    # Scan for issues
    issues = fixer.scan_for_issues()
    
    total_issues = sum(len(issue_list) for issue_list in issues.values())
    print(f"Found {total_issues} compatibility issues")
    
    if total_issues == 0:
        print("No compatibility issues found!")
        return
    
    # Show summary of issues
    for category, issue_list in issues.items():
        if issue_list:
            print(f"\n{category.upper().replace('_', ' ')} ({len(issue_list)} issues):")
            for issue in issue_list[:3]:  # Show first 3
                # Remove Windows path and just show filename
                clean_issue = issue.replace(str(fixer.project_root), "").replace("\\", "/")
                print(f"  - {clean_issue}")
            if len(issue_list) > 3:
                print(f"  ... and {len(issue_list) - 3} more")
    
    # Ask user if they want to apply fixes
    try:
        response = input(f"\nApply automatic fixes for {total_issues} issues? [Y/n]: ").strip().lower()
        if response and response not in ['y', 'yes']:
            print("Fixes cancelled by user")
            return
    except (EOFError, KeyboardInterrupt):
        print("\nFixes cancelled by user")
        return
    
    # Apply fixes
    print(f"\nAPPLYING AUTOMATIC FIXES")
    print("-" * 30)
    
    fix_results = fixer.apply_all_fixes()
    
    print(f"Applied {fix_results['total_fixes']} fixes:")
    print(f"  - Pydantic fixes: {fix_results['pydantic_fixes']}")
    print(f"  - Async fixes: {fix_results['async_fixes']}")
    print(f"  - Import fixes: {fix_results['import_fixes']}")
    
    if fix_results['details']:
        print(f"\nDetailed fixes:")
        for fix in fix_results['details']:
            print(f"  - {fix}")
    
    # Generate report (save without emojis for Windows compatibility)
    report = fixer.generate_compatibility_report()
    report_file = Path("compatibility_report.txt")
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\nDetailed report saved to: {report_file}")
    except Exception as e:
        print(f"Could not save report: {e}")
    
    # Final recommendations
    remaining_issues = total_issues - fix_results['total_fixes']
    if remaining_issues > 0:
        print(f"\nREMAINING ISSUES: {remaining_issues}")
        print("Some issues require manual attention:")
        print("  1. Review missing imports in routers")
        print("  2. Add proper auth imports where needed")
        print("  3. Test the application after fixes")
    else:
        print(f"\nALL ISSUES FIXED!")
        print("Recommendations:")
        print("  1. Test your application: python start_audit_server.py")
        print("  2. Run auth tests: python auth_verification_test.py")

if __name__ == "__main__":
    main()