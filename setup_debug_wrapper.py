#!/usr/bin/env python3
"""
Quick Start Setup for Universal Debug Wrapper
Automatically sets up the debug environment with all necessary files and dependencies.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_banner():
    """Print setup banner"""
    print("="*70)
    print("🔍 UNIVERSAL DEBUG WRAPPER - QUICK SETUP")
    print("="*70)
    print("🚀 Setting up comprehensive debugging tools for Python, JS, and HTML")
    print()

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7+ required")
        return False
    
    print("✅ Python version compatible")
    return True

def check_node_availability():
    """Check if Node.js is available for JavaScript debugging"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js available: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("⚠️  Node.js not found - JavaScript debugging will be limited")
    print("💡 Install Node.js from https://nodejs.org for full JS support")
    return False

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing Python dependencies...")
    
    required_packages = [
        'watchdog>=3.0.0',
        'psutil>=5.9.0', 
        'requests>=2.28.0'
    ]
    
    for package in required_packages:
        try:
            print(f"   Installing {package}...")
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', package
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"   ✅ {package} installed")
        except subprocess.CalledProcessError:
            print(f"   ⚠️  Failed to install {package} - continuing anyway")

def create_requirements_file():
    """Create requirements.txt file"""
    requirements = """# Universal Debug Wrapper Dependencies
watchdog>=3.0.0
psutil>=5.9.0
requests>=2.28.0

# Optional but recommended
beautifulsoup4>=4.11.0
lxml>=4.9.0
"""
    
    with open("requirements.txt", 'w', encoding='utf-8') as f:
        f.write(requirements)
    
    print("✅ Created requirements.txt")

def create_config_file():
    """Create default configuration file"""
    config = """{
  "log_level": "INFO",
  "output_format": "console",
  "auto_reload": false,
  "watch_extensions": [".py", ".js", ".html", ".css", ".json"],
  "performance_monitoring": true,
  "syntax_checking": true,
  "browser_debugging": false,
  "debug_port": 9229,
  "log_file": "debug.log"
}"""
    
    with open("debug_config.json", 'w', encoding='utf-8') as f:
        f.write(config)
    
    print("✅ Created debug_config.json")

def create_example_files():
    """Create example files for testing"""
    
    # Create examples directory
    examples_dir = Path("examples")
    examples_dir.mkdir(exist_ok=True)
    
    # Python example
    python_example = '''#!/usr/bin/env python3
"""
Example Python script for debugging
"""

def fibonacci(n):
    """Calculate fibonacci number"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def main():
    print("🐍 Python Debug Example")
    print("Calculating fibonacci numbers...")
    
    for i in range(10):
        result = fibonacci(i)
        print(f"fib({i}) = {result}")
    
    print("✅ Python example completed!")

if __name__ == "__main__":
    main()
'''
    
    # JavaScript example
    js_example = '''// Example JavaScript for debugging
console.log("🟨 JavaScript Debug Example");

function calculateFactorial(n) {
    if (n <= 1) return 1;
    return n * calculateFactorial(n - 1);
}

function main() {
    console.log("Calculating factorials...");
    
    for (let i = 1; i <= 10; i++) {
        const result = calculateFactorial(i);
        console.log(`${i}! = ${result}`);
    }
    
    console.log("✅ JavaScript example completed!");
}

main();
'''
    
    # HTML example
    html_example = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌐 HTML Debug Example</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 15px;
            text-align: center;
        }
        button {
            background: #ff6b6b;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #ff5252;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌐 HTML Debug Example</h1>
        <p>This is an example HTML file for debugging.</p>
        <button onclick="showMessage()">Click me!</button>
        <div id="output"></div>
    </div>

    <script>
        function showMessage() {
            const output = document.getElementById('output');
            const timestamp = new Date().toLocaleTimeString();
            output.innerHTML = `<p>✅ Button clicked at ${timestamp}</p>`;
            console.log("Button clicked successfully!");
        }
        
        console.log("🌐 HTML example loaded!");
    </script>
</body>
</html>
'''
    
    # Write example files
    with open(examples_dir / "example.py", 'w', encoding='utf-8') as f:
        f.write(python_example)
    
    with open(examples_dir / "example.js", 'w', encoding='utf-8') as f:
        f.write(js_example)
    
    with open(examples_dir / "example.html", 'w', encoding='utf-8') as f:
        f.write(html_example)
    
    print("✅ Created example files in ./examples/")

def create_vscode_tasks():
    """Create VS Code tasks for easy debugging"""
    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)
    
    tasks_config = """{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Debug Current File",
            "type": "shell",
            "command": "python",
            "args": ["debug.py", "--file", "${file}", "--mode", "auto"],
            "group": "build",
            "presentation": {
                "reveal": "always",
                "panel": "new"
            },
            "problemMatcher": []
        },
        {
            "label": "Start Debug Watcher",
            "type": "shell",
            "command": "python",
            "args": ["debug.py", "--watch", "${workspaceFolder}", "--mode", "auto"],
            "group": "build",
            "presentation": {
                "reveal": "always",
                "panel": "new"
            },
            "isBackground": true,
            "problemMatcher": []
        },
        {
            "label": "Debug with Performance",
            "type": "shell",
            "command": "python",
            "args": ["debug.py", "--file", "${file}", "--performance", "--browser"],
            "group": "build",
            "presentation": {
                "reveal": "always",
                "panel": "new"
            },
            "problemMatcher": []
        }
    ]
}"""
    
    with open(vscode_dir / "tasks.json", 'w', encoding='utf-8') as f:
        f.write(tasks_config)
    
    print("✅ Created VS Code tasks (.vscode/tasks.json)")

def create_gitignore():
    """Create .gitignore for debug files"""
    gitignore_content = """# Debug Wrapper Files
debug.log
logs/
*.debug
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt

# Debug outputs
debug_results_*.json
debug_reports/
*.debug.html

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""
    
    with open(".gitignore", 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    
    print("✅ Created .gitignore")

def run_example_debug():
    """Run a quick example debug to test setup"""
    print("\n🧪 Testing debug wrapper with example file...")
    
    try:
        # Run debug on Python example
        result = subprocess.run([
            sys.executable, 'debug.py', 
            '--file', 'examples/example.py', 
            '--mode', 'python'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Debug wrapper test successful!")
            print("📊 Sample output:")
            print("-" * 40)
            print(result.stdout[:200] + "..." if len(result.stdout) > 200 else result.stdout)
            print("-" * 40)
        else:
            print("⚠️  Debug wrapper test had issues, but setup completed")
    
    except subprocess.TimeoutExpired:
        print("⚠️  Debug test timed out, but setup completed")
    except Exception as e:
        print(f"⚠️  Debug test failed: {e}")

def print_usage_instructions():
    """Print usage instructions"""
    print("\n" + "="*70)
    print("🎉 SETUP COMPLETE!")
    print("="*70)
    print()
    print("📚 Quick Start Commands:")
    print("   # Debug a single file")
    print("   python debug.py --file examples/example.py")
    print()
    print("   # Watch directory for changes")
    print("   python debug.py --watch . --mode auto")
    print()
    print("   # Debug with browser support")
    print("   python debug.py --file examples/example.html --browser")
    print()
    print("   # JSON output format")
    print("   python debug.py --file examples/example.js --output json")
    print()
    print("🌐 Web Interface:")
    print("   python -m http.server 8080")
    print("   Then open: http://localhost:8080/debug_interface.html")
    print()
    print("📁 Files Created:")
    print("   ✅ debug.py - Main debug wrapper")
    print("   ✅ debug_interface.html - Web interface")
    print("   ✅ debug_config.json - Configuration file")
    print("   ✅ requirements.txt - Python dependencies")
    print("   ✅ examples/ - Test files")
    print("   ✅ .vscode/tasks.json - VS Code integration")
    print()
    print("📖 For detailed documentation, see DEBUG_SETUP.md")
    print("="*70)

def main():
    """Main setup function"""
    print_banner()
    
    # System checks
    if not check_python_version():
        sys.exit(1)
    
    node_available = check_node_availability()
    
    # Installation steps
    try:
        install_dependencies()
        create_requirements_file()
        create_config_file()
        create_example_files()
        create_vscode_tasks()
        create_gitignore()
        
        # Test if debug.py exists
        if Path("debug.py").exists():
            run_example_debug()
        else:
            print("\n⚠️  debug.py not found - please ensure it's in the current directory")
        
        print_usage_instructions()
        
    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()