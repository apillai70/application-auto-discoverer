#!/usr/bin/env python3
"""
Master Setup & Validation Script
================================
One-stop script to set up, fix, test, and run your auth & audit system
"""

import subprocess
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

class MasterSetup:
    """Master setup coordinator for auth & audit systems"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.results = {}
        self.start_time = datetime.now()
        
    def print_header(self, title: str, char: str = "="):
        """Print a formatted header"""
        print(f"\n{char * 60}")
        print(f"🎯 {title}")
        print(f"{char * 60}")
    
    def print_step(self, step: str, description: str):
        """Print a step description"""
        print(f"\n🔸 Step {step}: {description}")
        print("-" * 40)
    
    def run_command(self, command: List[str], description: str, required: bool = True) -> bool:
        """Run a command and capture results"""
        print(f"⚡ Running: {description}...")
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                print(f"✅ {description} completed successfully")
                return True
            else:
                print(f"❌ {description} failed")
                if result.stderr:
                    print(f"   Error: {result.stderr.strip()}")
                if required:
                    print(f"   This is a required step. Please fix the issue and try again.")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {description} timed out")
            return False
        except FileNotFoundError:
            print(f"❌ Command not found for: {description}")
            if required:
                print(f"   Please ensure the script exists: {' '.join(command)}")
            return False
        except Exception as e:
            print(f"❌ Error running {description}: {e}")
            return False
    
    def check_prerequisites(self) -> bool:
        """Check if all required files exist"""
        self.print_step("1", "Checking Prerequisites")
        
        required_files = [
            "main.py",
            "routers/__init__.py",
            "routers/auth.py"
        ]
        
        optional_files = [
            "routers/audit.py",
            "storage/file_audit_storage.py"
        ]
        
        missing_required = []
        missing_optional = []
        
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_required.append(file_path)
        
        for file_path in optional_files:
            if not (self.project_root / file_path).exists():
                missing_optional.append(file_path)
        
        if missing_required:
            print(f"❌ Missing required files:")
            for file_path in missing_required:
                print(f"   - {file_path}")
            return False
        
        if missing_optional:
            print(f"⚠️ Missing optional files (features may be limited):")
            for file_path in missing_optional:
                print(f"   - {file_path}")
        
        print(f"✅ All required files present")
        return True
    
    def install_dependencies(self) -> bool:
        """Install required Python dependencies"""
        self.print_step("2", "Installing Dependencies")
        
        # Check if requirements file exists
        if (self.project_root / "requirements.txt").exists():
            return self.run_command(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                "Installing from requirements.txt",
                required=False
            )
        else:
            # Install common dependencies
            dependencies = [
                "fastapi", "uvicorn", "pydantic", "aiofiles", 
                "requests", "python-multipart"
            ]
            
            success = True
            for dep in dependencies:
                if not self.run_command(
                    [sys.executable, "-m", "pip", "install", dep],
                    f"Installing {dep}",
                    required=False
                ):
                    success = False
            
            return success
    
    def create_scripts(self) -> bool:
        """Create required scripts if they don't exist"""
        self.print_step("3", "Creating Required Scripts")
        
        scripts_created = []
        
        # Check if our enhancement scripts exist
        required_scripts = [
            "compatibility_fixer.py",
            "auth_verification_test.py", 
            "auth_audit_integration_test.py",
            "start_audit_server.py"
        ]
        
        missing_scripts = [
            script for script in required_scripts 
            if not (self.project_root / script).exists()
        ]
        
        if missing_scripts:
            print(f"⚠️ Missing enhancement scripts:")
            for script in missing_scripts:
                print(f"   - {script}")
            print(f"💡 Please ensure all artifacts from the integration guide are saved as files")
            return False
        else:
            print(f"✅ All enhancement scripts are available")
            return True
    
    def fix_compatibility(self) -> bool:
        """Run compatibility fixer"""
        self.print_step("4", "Fixing Compatibility Issues")
        
        return self.run_command(
            [sys.executable, "compatibility_fixer.py"],
            "Running compatibility fixer",
            required=True
        )
    
    def test_authentication(self) -> bool:
        """Test authentication system"""
        self.print_step("5", "Testing Authentication System")
        
        return self.run_command(
            [sys.executable, "auth_verification_test.py"],
            "Running authentication tests",
            required=False
        )
    
    def test_integration(self) -> bool:
        """Test auth-audit integration"""
        self.print_step("6", "Testing Auth-Audit Integration")
        
        # First start the server in background for testing
        print("🚀 Starting server for integration testing...")
        
        # Use the enhanced startup script to test
        return self.run_command(
            [sys.executable, "auth_audit_integration_test.py"],
            "Running integration tests",
            required=False
        )
    
    def create_directories(self) -> bool:
        """Create required directories"""
        self.print_step("3.5", "Creating Required Directories")
        
        directories = [
            "essentials/audit/events",
            "essentials/audit/config", 
            "essentials/audit/reports",
            "essentials/audit/indexes",
            "essentials/audit/archives",
            "essentials/audit/backups",
            "essentials/audit/temp"
        ]
        
        created_dirs = []
        for dir_path in directories:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                try:
                    full_path.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(dir_path)
                except Exception as e:
                    print(f"❌ Failed to create {dir_path}: {e}")
                    return False
        
        if created_dirs:
            print(f"✅ Created {len(created_dirs)} directories")
        else:
            print(f"✅ All directories already exist")
        
        return True
    
    def start_server(self) -> bool:
        """Start the enhanced server"""
        self.print_step("7", "Starting Enhanced Server")
        
        print("🚀 Starting server with enhanced validation...")
        print("📝 Note: Server will run interactively. Press Ctrl+C to stop.")
        print("⏰ Waiting 3 seconds before starting...")
        time.sleep(3)
        
        try:
            # Run the enhanced startup script
            subprocess.run([sys.executable, "start_audit_server.py"])
            return True
        except KeyboardInterrupt:
            print("\n👋 Server stopped by user")
            return True
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate a summary report of the setup process"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Count successes and failures
        total_steps = len(self.results)
        successful_steps = sum(1 for success in self.results.values() if success)
        
        report = {
            "setup_summary": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration.total_seconds(),
                "total_steps": total_steps,
                "successful_steps": successful_steps,
                "success_rate": (successful_steps / total_steps * 100) if total_steps > 0 else 0
            },
            "step_results": self.results,
            "system_status": {
                "prerequisites": self.results.get("prerequisites", False),
                "dependencies": self.results.get("dependencies", False),
                "compatibility": self.results.get("compatibility", False),
                "authentication": self.results.get("authentication", False),
                "integration": self.results.get("integration", False)
            },
            "next_steps": [],
            "recommendations": []
        }
        
        # Add recommendations based on results
        if not self.results.get("dependencies", False):
            report["recommendations"].append("Install missing Python dependencies")
        
        if not self.results.get("compatibility", False):
            report["recommendations"].append("Fix compatibility issues before production use")
        
        if not self.results.get("authentication", False):
            report["recommendations"].append("Review authentication system configuration")
        
        if not self.results.get("integration", False):
            report["recommendations"].append("Test auth-audit integration manually")
        
        # Add next steps
        if successful_steps == total_steps:
            report["next_steps"] = [
                "Server is ready for use",
                "Access API docs at http://localhost:8001/docs", 
                "Test login with admin/admin123",
                "Monitor audit logs in essentials/audit/"
            ]
        elif successful_steps >= total_steps * 0.7:
            report["next_steps"] = [
                "System is partially ready",
                "Review failed steps and fix issues",
                "Rerun setup after fixes",
                "Test system manually"
            ]
        else:
            report["next_steps"] = [
                "Multiple issues found",
                "Review error messages above",
                "Fix critical issues first",
                "Contact support if needed"
            ]
        
        return report
    
    def print_final_summary(self, report: Dict[str, Any]):
        """Print final setup summary"""
        self.print_header("SETUP COMPLETE", "=")
        
        summary = report["setup_summary"]
        print(f"⏰ Duration: {summary['duration_seconds']:.1f} seconds")
        print(f"✅ Successful steps: {summary['successful_steps']}/{summary['total_steps']}")
        print(f"📊 Success rate: {summary['success_rate']:.1f}%")
        
        print(f"\n📋 System Status:")
        status = report["system_status"]
        for component, working in status.items():
            status_icon = "✅" if working else "❌"
            print(f"   {status_icon} {component.title()}: {'Ready' if working else 'Issues'}")
        
        if report["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in report["recommendations"]:
                print(f"   • {rec}")
        
        print(f"\n🎯 Next Steps:")
        for step in report["next_steps"]:
            print(f"   • {step}")
        
        if summary["success_rate"] >= 80:
            print(f"\n🎉 Setup completed successfully! Your system is ready to use.")
        elif summary["success_rate"] >= 60:
            print(f"\n⚠️ Setup completed with some issues. System is functional but needs attention.")
        else:
            print(f"\n❌ Setup encountered significant issues. Please review and fix before use.")
    
    def run_interactive_mode(self):
        """Run interactive setup mode"""
        self.print_header("MASTER SETUP & VALIDATION", "=")
        print("🎯 This script will set up and validate your auth & audit system")
        print("📋 Steps: Prerequisites → Dependencies → Compatibility → Testing → Server")
        print("")
        
        response = input("🤔 Continue with automated setup? [Y/n]: ").strip().lower()
        if response and response != 'y' and response != 'yes':
            print("👋 Setup cancelled by user")
            return
        
        # Run all setup steps
        steps = [
            ("prerequisites", self.check_prerequisites),
            ("scripts", self.create_scripts),
            ("dependencies", self.install_dependencies), 
            ("directories", self.create_directories),
            ("compatibility", self.fix_compatibility),
            ("authentication", self.test_authentication),
            ("integration", self.test_integration)
        ]
        
        for step_name, step_function in steps:
            try:
                self.results[step_name] = step_function()
            except Exception as e:
                print(f"❌ Error in {step_name}: {e}")
                self.results[step_name] = False
        
        # Generate and save report
        report = self.generate_summary_report()
        
        # Save report to file
        report_file = self.project_root / "setup_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        self.print_final_summary(report)
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Ask about starting server
        if self.results.get("prerequisites", False) and self.results.get("compatibility", False):
            response = input(f"\n🚀 Start the enhanced server now? [Y/n]: ").strip().lower()
            if not response or response == 'y' or response == 'yes':
                self.start_server()
        else:
            print(f"\n⚠️ Please fix critical issues before starting the server")

def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Master Setup & Validation for Auth & Audit System")
    parser.add_argument("--auto", action="store_true", help="Run in automatic mode (no prompts)")
    parser.add_argument("--skip-server", action="store_true", help="Skip starting the server")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    setup = MasterSetup()
    
    if args.auto:
        print("🤖 Running in automatic mode...")
        # Run all steps automatically
        steps = [
            ("prerequisites", setup.check_prerequisites),
            ("scripts", setup.create_scripts),
            ("dependencies", setup.install_dependencies),
            ("directories", setup.create_directories), 
            ("compatibility", setup.fix_compatibility),
            ("authentication", setup.test_authentication),
            ("integration", setup.test_integration)
        ]
        
        for step_name, step_function in steps:
            setup.results[step_name] = step_function()
        
        report = setup.generate_summary_report()
        setup.print_final_summary(report)
        
        if not args.skip_server and setup.results.get("prerequisites", False):
            setup.start_server()
    else:
        # Run interactive mode
        setup.run_interactive_mode()

if __name__ == "__main__":
    main()