#!/usr/bin/env python3
"""
Universal Debug Wrapper for Python, JavaScript, and HTML
A comprehensive debugging tool for multi-language development

Usage:
    python debug.py --file script.py --mode python
    python debug.py --file app.js --mode javascript  
    python debug.py --file index.html --mode html
    python debug.py --watch ./src --mode auto
"""

import os
import sys
import json
import time
import subprocess
import traceback
import argparse
import logging
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Try to import optional dependencies
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# =================== CONFIGURATION ===================

@dataclass
class DebugConfig:
    """Debug configuration settings"""
    log_level: str = "INFO"
    output_format: str = "console"  # console, json, html
    auto_reload: bool = False
    watch_extensions: List[str] = None
    performance_monitoring: bool = True
    syntax_checking: bool = True
    browser_debugging: bool = False
    debug_port: int = 9229
    log_file: str = "debug.log"
    
    def __post_init__(self):
        if self.watch_extensions is None:
            self.watch_extensions = ['.py', '.js', '.html', '.css', '.json']

# =================== LOGGING SETUP ===================

class ColoredFormatter(logging.Formatter):
    """Colored logging formatter for better console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)

def setup_logging(config: DebugConfig):
    """Setup logging configuration"""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Setup logger
    logger = logging.getLogger("debug_wrapper")
    logger.setLevel(getattr(logging, config.log_level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(log_dir / config.log_file)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger

# =================== DEBUG RESULTS ===================

@dataclass
class DebugResult:
    """Debug execution result"""
    success: bool
    execution_time: float
    memory_usage: Optional[float]
    syntax_valid: bool
    syntax_errors: List[str]
    runtime_errors: List[str]
    warnings: List[str]
    output: str
    file_path: str
    language: str
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

# =================== PYTHON DEBUGGER ===================

class PythonDebugger:
    """Python script debugger"""
    
    def __init__(self, config: DebugConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
    
    def check_syntax(self, file_path: str) -> tuple[bool, List[str]]:
        """Check Python syntax"""
        errors = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            compile(source, file_path, 'exec')
            return True, []
            
        except SyntaxError as e:
            errors.append(f"Syntax Error: {e.msg} at line {e.lineno}")
            return False, errors
        except Exception as e:
            errors.append(f"Compilation Error: {str(e)}")
            return False, errors
    
    def run_with_debugging(self, file_path: str) -> DebugResult:
        """Run Python script with debugging"""
        start_time = time.time()
        initial_memory = self.get_memory_usage()
        
        # Check syntax first
        syntax_valid, syntax_errors = self.check_syntax(file_path)
        
        if not syntax_valid:
            return DebugResult(
                success=False,
                execution_time=time.time() - start_time,
                memory_usage=None,
                syntax_valid=False,
                syntax_errors=syntax_errors,
                runtime_errors=[],
                warnings=[],
                output="",
                file_path=file_path,
                language="python",
                timestamp=datetime.now().isoformat()
            )
        
        # Execute the script
        output = ""
        runtime_errors = []
        warnings = []
        success = False
        
        try:
            # Capture stdout and stderr
            import io
            import contextlib
            
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            with contextlib.redirect_stdout(stdout_capture), \
                 contextlib.redirect_stderr(stderr_capture):
                
                # Execute the script
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                # Create execution namespace
                exec_globals = {
                    '__file__': file_path,
                    '__name__': '__main__',
                }
                
                exec(compile(source, file_path, 'exec'), exec_globals)
            
            output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()
            
            if stderr_output:
                warnings.append(f"STDERR: {stderr_output}")
            
            success = True
            
        except Exception as e:
            runtime_errors.append(f"Runtime Error: {str(e)}")
            runtime_errors.append(f"Traceback: {traceback.format_exc()}")
        
        execution_time = time.time() - start_time
        final_memory = self.get_memory_usage()
        memory_usage = final_memory - initial_memory if initial_memory and final_memory else None
        
        return DebugResult(
            success=success,
            execution_time=execution_time,
            memory_usage=memory_usage,
            syntax_valid=syntax_valid,
            syntax_errors=syntax_errors,
            runtime_errors=runtime_errors,
            warnings=warnings,
            output=output,
            file_path=file_path,
            language="python",
            timestamp=datetime.now().isoformat()
        )
    
    def get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in MB"""
        if not PSUTIL_AVAILABLE:
            return None
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except:
            return None

# =================== JAVASCRIPT DEBUGGER ===================

class JavaScriptDebugger:
    """JavaScript debugger"""
    
    def __init__(self, config: DebugConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
    
    def check_syntax(self, file_path: str) -> tuple[bool, List[str]]:
        """Check JavaScript syntax using Node.js"""
        errors = []
        try:
            # Try to parse with Node.js
            result = subprocess.run(
                ['node', '--check', file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, []
            else:
                errors.append(f"Syntax Error: {result.stderr}")
                return False, errors
                
        except subprocess.TimeoutExpired:
            errors.append("Syntax check timed out")
            return False, errors
        except FileNotFoundError:
            # Node.js not available, try basic parsing
            self.logger.warning("Node.js not found, skipping JavaScript syntax check")
            return True, ["Warning: Node.js not available for syntax checking"]
        except Exception as e:
            errors.append(f"Syntax check failed: {str(e)}")
            return False, errors
    
    def run_with_debugging(self, file_path: str) -> DebugResult:
        """Run JavaScript with Node.js debugging"""
        start_time = time.time()
        
        # Check syntax first
        syntax_valid, syntax_errors = self.check_syntax(file_path)
        
        output = ""
        runtime_errors = []
        warnings = []
        success = False
        
        if syntax_valid:
            try:
                # Run with Node.js
                debug_args = []
                if self.config.browser_debugging:
                    debug_args = [f'--inspect={self.config.debug_port}']
                
                result = subprocess.run(
                    ['node'] + debug_args + [file_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                output = result.stdout
                if result.stderr:
                    if result.returncode == 0:
                        warnings.append(f"STDERR: {result.stderr}")
                    else:
                        runtime_errors.append(f"Runtime Error: {result.stderr}")
                
                success = result.returncode == 0
                
            except subprocess.TimeoutExpired:
                runtime_errors.append("Script execution timed out")
            except FileNotFoundError:
                runtime_errors.append("Node.js not found. Please install Node.js to debug JavaScript files.")
            except Exception as e:
                runtime_errors.append(f"Execution failed: {str(e)}")
        
        execution_time = time.time() - start_time
        
        return DebugResult(
            success=success,
            execution_time=execution_time,
            memory_usage=None,
            syntax_valid=syntax_valid,
            syntax_errors=syntax_errors,
            runtime_errors=runtime_errors,
            warnings=warnings,
            output=output,
            file_path=file_path,
            language="javascript",
            timestamp=datetime.now().isoformat()
        )

# =================== HTML DEBUGGER ===================

class HTMLDebugger:
    """HTML debugger and validator"""
    
    def __init__(self, config: DebugConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
    
    def check_syntax(self, file_path: str) -> tuple[bool, List[str]]:
        """Check HTML syntax and structure"""
        errors = []
        warnings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic HTML validation
            from html.parser import HTMLParser
            
            class HTMLValidator(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.errors = []
                    self.warnings = []
                    self.tags = []
                
                def handle_starttag(self, tag, attrs):
                    self.tags.append(tag)
                
                def handle_endtag(self, tag):
                    if self.tags and self.tags[-1] == tag:
                        self.tags.pop()
                    else:
                        self.errors.append(f"Mismatched closing tag: {tag}")
                
                def error(self, message):
                    self.errors.append(f"Parse error: {message}")
            
            validator = HTMLValidator()
            validator.feed(content)
            
            # Check for unclosed tags
            if validator.tags:
                warnings.extend([f"Unclosed tag: {tag}" for tag in validator.tags])
            
            errors.extend(validator.errors)
            
            # Additional checks
            if '<!DOCTYPE' not in content.upper():
                warnings.append("Missing DOCTYPE declaration")
            
            if '<html' not in content.lower():
                warnings.append("Missing <html> tag")
            
            if '<head' not in content.lower():
                warnings.append("Missing <head> tag")
            
            if '<body' not in content.lower():
                warnings.append("Missing <body> tag")
            
            return len(errors) == 0, errors + warnings
            
        except Exception as e:
            errors.append(f"HTML validation failed: {str(e)}")
            return False, errors
    
    def run_with_debugging(self, file_path: str) -> DebugResult:
        """Debug HTML file"""
        start_time = time.time()
        
        # Check syntax
        syntax_valid, syntax_errors = self.check_syntax(file_path)
        
        output = f"HTML file validated: {file_path}"
        warnings = []
        
        # Check for common issues
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for inline styles (recommend external CSS)
            if 'style=' in content:
                warnings.append("Inline styles detected - consider using external CSS")
            
            # Check for inline JavaScript
            if '<script>' in content and 'src=' not in content:
                warnings.append("Inline JavaScript detected - consider using external JS files")
            
            # Check for accessibility
            if 'alt=' not in content and '<img' in content:
                warnings.append("Images without alt attributes detected")
            
            if self.config.browser_debugging:
                # Open in browser for visual debugging
                file_url = f"file://{os.path.abspath(file_path)}"
                output += f"\nOpening in browser: {file_url}"
                webbrowser.open(file_url)
            
        except Exception as e:
            warnings.append(f"Additional checks failed: {str(e)}")
        
        execution_time = time.time() - start_time
        
        return DebugResult(
            success=syntax_valid,
            execution_time=execution_time,
            memory_usage=None,
            syntax_valid=syntax_valid,
            syntax_errors=syntax_errors,
            runtime_errors=[],
            warnings=warnings,
            output=output,
            file_path=file_path,
            language="html",
            timestamp=datetime.now().isoformat()
        )

# =================== FILE WATCHER ===================

class FileWatcher(FileSystemEventHandler):
    """File system watcher for auto-reload debugging"""
    
    def __init__(self, debugger_wrapper, config: DebugConfig, logger: logging.Logger):
        self.debugger = debugger_wrapper
        self.config = config
        self.logger = logger
        self.last_modified = {}
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext not in self.config.watch_extensions:
            return
        
        # Debounce: avoid multiple triggers for the same file
        now = time.time()
        if file_path in self.last_modified:
            if now - self.last_modified[file_path] < 1.0:  # 1 second debounce
                return
        
        self.last_modified[file_path] = now
        
        self.logger.info(f"File changed: {file_path}")
        
        # Auto-detect language and debug
        result = self.debugger.debug_file(file_path, mode="auto")
        self.debugger.display_result(result)

# =================== MAIN DEBUGGER WRAPPER ===================

class DebuggerWrapper:
    """Main debugger wrapper class"""
    
    def __init__(self, config: DebugConfig):
        self.config = config
        self.logger = setup_logging(config)
        
        # Initialize language-specific debuggers
        self.python_debugger = PythonDebugger(config, self.logger)
        self.js_debugger = JavaScriptDebugger(config, self.logger)
        self.html_debugger = HTMLDebugger(config, self.logger)
        
        # File watcher
        self.observer = None
    
    def detect_language(self, file_path: str) -> str:
        """Auto-detect file language"""
        extension = Path(file_path).suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.mjs': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'javascript',
            '.tsx': 'javascript',
            '.html': 'html',
            '.htm': 'html',
            '.xhtml': 'html'
        }
        
        return language_map.get(extension, 'unknown')
    
    def debug_file(self, file_path: str, mode: str = "auto") -> DebugResult:
        """Debug a file based on its type"""
        
        if not os.path.exists(file_path):
            return DebugResult(
                success=False,
                execution_time=0,
                memory_usage=None,
                syntax_valid=False,
                syntax_errors=[f"File not found: {file_path}"],
                runtime_errors=[],
                warnings=[],
                output="",
                file_path=file_path,
                language="unknown",
                timestamp=datetime.now().isoformat()
            )
        
        # Determine language
        if mode == "auto":
            language = self.detect_language(file_path)
        else:
            language = mode.lower()
        
        self.logger.info(f"Debugging {language} file: {file_path}")
        
        # Route to appropriate debugger
        if language == "python":
            return self.python_debugger.run_with_debugging(file_path)
        elif language == "javascript":
            return self.js_debugger.run_with_debugging(file_path)
        elif language == "html":
            return self.html_debugger.run_with_debugging(file_path)
        else:
            return DebugResult(
                success=False,
                execution_time=0,
                memory_usage=None,
                syntax_valid=False,
                syntax_errors=[f"Unsupported language: {language}"],
                runtime_errors=[],
                warnings=[],
                output="",
                file_path=file_path,
                language=language,
                timestamp=datetime.now().isoformat()
            )
    
    def display_result(self, result: DebugResult):
        """Display debug results"""
        
        if self.config.output_format == "json":
            print(result.to_json())
            return
        
        # Console output
        print("\n" + "="*70)
        print(f"🔍 DEBUG RESULTS: {result.file_path}")
        print("="*70)
        
        # Status
        status_icon = "✅" if result.success else "❌"
        print(f"{status_icon} Status: {'SUCCESS' if result.success else 'FAILED'}")
        print(f"📄 Language: {result.language.upper()}")
        print(f"⏱️  Execution Time: {result.execution_time:.3f}s")
        
        if result.memory_usage:
            print(f"💾 Memory Usage: {result.memory_usage:.2f} MB")
        
        # Syntax
        syntax_icon = "✅" if result.syntax_valid else "❌"
        print(f"{syntax_icon} Syntax: {'VALID' if result.syntax_valid else 'INVALID'}")
        
        # Errors and warnings
        if result.syntax_errors:
            print(f"\n🚨 SYNTAX ERRORS:")
            for error in result.syntax_errors:
                print(f"   • {error}")
        
        if result.runtime_errors:
            print(f"\n💥 RUNTIME ERRORS:")
            for error in result.runtime_errors:
                print(f"   • {error}")
        
        if result.warnings:
            print(f"\n⚠️  WARNINGS:")
            for warning in result.warnings:
                print(f"   • {warning}")
        
        # Output
        if result.output:
            print(f"\n📝 OUTPUT:")
            print("-" * 40)
            print(result.output)
            print("-" * 40)
        
        print(f"\n🕐 Timestamp: {result.timestamp}")
        print("="*70)
    
    def start_watching(self, watch_path: str):
        """Start file watching for auto-reload"""
        if self.observer:
            self.stop_watching()
        
        event_handler = FileWatcher(self, self.config, self.logger)
        self.observer = Observer()
        self.observer.schedule(event_handler, watch_path, recursive=True)
        self.observer.start()
        
        self.logger.info(f"👀 Watching for changes in: {watch_path}")
        print(f"👀 File watcher started for: {watch_path}")
        print("Press Ctrl+C to stop watching...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_watching()
    
    def stop_watching(self):
        """Stop file watching"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            self.logger.info("File watcher stopped")

# =================== CLI INTERFACE ===================

def create_debug_config_from_args(args) -> DebugConfig:
    """Create debug configuration from command line arguments"""
    config = DebugConfig()
    
    if hasattr(args, 'log_level') and args.log_level:
        config.log_level = args.log_level
    
    if hasattr(args, 'output_format') and args.output_format:
        config.output_format = args.output_format
    
    if hasattr(args, 'browser') and args.browser:
        config.browser_debugging = args.browser
    
    if hasattr(args, 'performance') and args.performance:
        config.performance_monitoring = args.performance
    
    if hasattr(args, 'watch') and args.watch:
        config.auto_reload = True
    
    return config

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Universal Debug Wrapper for Python, JavaScript, and HTML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python debug.py --file script.py --mode python
  python debug.py --file app.js --mode javascript --browser
  python debug.py --file index.html --mode html
  python debug.py --watch ./src --mode auto
  python debug.py --file test.py --output json
        """
    )
    
    parser.add_argument('--file', '-f', type=str, help='File to debug')
    parser.add_argument('--mode', '-m', choices=['python', 'javascript', 'html', 'auto'], 
                       default='auto', help='Debug mode (default: auto)')
    parser.add_argument('--watch', '-w', type=str, help='Directory to watch for changes')
    parser.add_argument('--output', '-o', choices=['console', 'json'], 
                       default='console', help='Output format')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Log level')
    parser.add_argument('--browser', '-b', action='store_true', 
                       help='Enable browser debugging for JS/HTML')
    parser.add_argument('--performance', '-p', action='store_true', 
                       help='Enable performance monitoring')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.file and not args.watch:
        parser.error("Either --file or --watch must be specified")
    
    # Create configuration
    config = create_debug_config_from_args(args)
    config.output_format = args.output
    
    # Initialize debugger
    debugger = DebuggerWrapper(config)
    
    try:
        if args.watch:
            # Watch mode
            debugger.start_watching(args.watch)
        elif args.file:
            # Single file debug
            result = debugger.debug_file(args.file, args.mode)
            debugger.display_result(result)
            
            # Exit with error code if debugging failed
            sys.exit(0 if result.success else 1)
        
    except KeyboardInterrupt:
        print("\n👋 Debug session interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()