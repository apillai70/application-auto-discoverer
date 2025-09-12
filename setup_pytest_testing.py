# setup_pytest_testing.py
"""
Setup script to configure pytest testing environment for comprehensive logging system
Creates all necessary configuration files and test structure
"""

import os
from pathlib import Path

def create_pytest_config():
    """Create pytest.ini configuration file"""
    
    pytest_config = """[tool:pytest]
testpaths = .
python_files = test_*.py *_test.py test_comprehensive_logging_pytest.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --strict-config
    --tb=short
    --durations=10
markers =
    asyncio: async test marker
    unit: unit test marker  
    integration: integration test marker
    slow: slow running test marker
    mock: test using mocks
    real: test using real implementations
asyncio_mode = auto
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
    ignore::UserWarning:aiohttp.*
log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)8s] %(name)s: %(message)s
log_cli_date_format = %Y-%m-%d %H:%M:%S
log_file = tests.log
log_file_level = DEBUG
log_file_format = %(asctime)s [%(levelname)8s] %(filename)s:%(lineno)d %(funcName)s(): %(message)s
log_file_date_format = %Y-%m-%d %H:%M:%S
"""
    
    with open("pytest.ini", "w") as f:
        f.write(pytest_config)
    print("✅ Created pytest.ini")

def create_coverage_config():
    """Create .coveragerc configuration file"""
    
    coverage_config = """[run]
source = .
omit = 
    */venv/*
    */env/*
    */.venv/*
    */tests/*
    */test_*
    */__pycache__/*
    */migrations/*
    */node_modules/*
    */static/*
    setup.py
    manage.py
    */conftest.py
    */settings/*
    demo_*.py
    setup_*.py
branch = True
parallel = True

[report]
precision = 2
show_missing = True
skip_covered = False
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug:
    if settings.DEBUG
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
    class .*\\bProtocol\\):
    @(abc\\.)?abstractmethod
sort = Cover
fail_under = 75

[html]
directory = htmlcov
title = Comprehensive Logging System Coverage Report

[xml]
output = coverage.xml

[json]
output = coverage.json
"""
    
    with open(".coveragerc", "w") as f:
        f.write(coverage_config)
    print("✅ Created .coveragerc")

def create_gitignore_entries():
    """Add testing-related entries to .gitignore"""
    
    gitignore_entries = """
# Testing and Coverage
htmlcov/
.coverage
.coverage.*
coverage.xml
coverage.json
test-results.xml
test_report.html
tests.log
.pytest_cache/
__pycache__/
*.pyc
.tox/

# Test artifacts
test_logs_pytest/
test_logs/
demo_logs/
"""
    
    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        with open(gitignore_path, "a") as f:
            f.write(gitignore_entries)
        print("✅ Updated .gitignore")
    else:
        with open(gitignore_path, "w") as f:
            f.write(gitignore_entries)
        print("✅ Created .gitignore")

def create_test_requirements():
    """Create test-specific requirements file"""
    
    test_requirements = """# Testing Dependencies
pytest>=7.4.3,<8.0.0
pytest-asyncio>=0.21.1,<1.0.0
pytest-cov>=4.1.0,<5.0.0
pytest-html>=4.1.0,<5.0.0
pytest-xdist>=3.3.0,<4.0.0
pytest-mock>=3.12.0,<4.0.0
pytest-timeout>=2.2.0,<3.0.0

# Coverage reporting
coverage[toml]>=7.3.0,<8.0.0
coverage-badge>=1.1.0,<2.0.0

# Additional testing utilities
factory-boy>=3.3.0,<4.0.0
faker>=20.1.0,<21.0.0
responses>=0.24.0,<1.0.0
"""
    
    with open("requirements-test.txt", "w") as f:
        f.write(test_requirements)
    print("✅ Created requirements-test.txt")

def create_conftest_py():
    """Create conftest.py for shared test configuration"""
    
    conftest_content = '''# conftest.py
"""
Shared pytest configuration and fixtures
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil

# Configure asyncio for testing
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Cleanup test files after each test"""
    yield
    
    # Clean up any test log directories
    test_dirs = [
        "test_logs",
        "test_logs_pytest", 
        "demo_logs"
    ]
    
    for test_dir in test_dirs:
        if Path(test_dir).exists():
            shutil.rmtree(test_dir, ignore_errors=True)

# Test configuration
pytest.register_assert_rewrite("test_comprehensive_logging_pytest")
'''
    
    with open("conftest.py", "w") as f:
        f.write(conftest_content)
    print("✅ Created conftest.py")

def create_makefile():
    """Create Makefile for easy test commands"""
    
    makefile_content = """# Makefile for Comprehensive Logging System Testing

.PHONY: test test-cov test-html test-unit test-integration install-test clean

# Install testing dependencies
install-test:
	pip install -r requirements-test.txt

# Basic test run
test:
	pytest test_comprehensive_logging_pytest.py -v

# Test with coverage
test-cov:
	pytest test_comprehensive_logging_pytest.py --cov=. --cov-report=term-missing

# Test with HTML coverage report
test-html:
	pytest test_comprehensive_logging_pytest.py --cov=. --cov-report=html --cov-report=term-missing
	@echo "Coverage report: htmlcov/index.html"

# Run only unit tests
test-unit:
	pytest test_comprehensive_logging_pytest.py -m unit -v

# Run only integration tests
test-integration:
	pytest test_comprehensive_logging_pytest.py -m integration -v

# Full test suite with all reports
test-full:
	pytest test_comprehensive_logging_pytest.py \\
		--cov=. \\
		--cov-report=html \\
		--cov-report=xml \\
		--cov-report=term-missing \\
		--cov-fail-under=75 \\
		--html=test_report.html \\
		--self-contained-html \\
		-v \\
		--durations=10

# CI/CD testing
test-ci:
	pytest test_comprehensive_logging_pytest.py \\
		--cov=. \\
		--cov-report=xml \\
		--cov-fail-under=75 \\
		--junitxml=test-results.xml \\
		--tb=short \\
		-q

# Clean test artifacts
clean:
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	rm -f .coverage
	rm -f coverage.xml
	rm -f coverage.json
	rm -f test-results.xml
	rm -f test_report.html
	rm -f tests.log
	rm -rf test_logs*/
	rm -rf demo_logs/
"""
    
    with open("Makefile", "w") as f:
        f.write(makefile_content)
    print("✅ Created Makefile")

def create_tox_config():
    """Create tox.ini for multi-environment testing"""
    
    tox_config = """[tox]
envlist = py311, coverage, lint
isolated_build = true

[testenv]
deps = 
    -r requirements.txt
    -r requirements-test.txt
commands = 
    pytest test_comprehensive_logging_pytest.py -v

[testenv:coverage]
deps = 
    -r requirements.txt
    -r requirements-test.txt
commands = 
    pytest test_comprehensive_logging_pytest.py --cov=. --cov-report=html --cov-report=term-missing --cov-fail-under=75

[testenv:lint]
deps = 
    black
    flake8
    mypy
commands = 
    black --check .
    flake8 .
    mypy services/ middleware/ routers/ --ignore-missing-imports

[testenv:docs]
deps = 
    mkdocs
    mkdocs-material
commands = 
    mkdocs build
"""
    
    with open("tox.ini", "w") as f:
        f.write(tox_config)
    print("✅ Created tox.ini")

def create_github_workflow():
    """Create GitHub Actions workflow for testing"""
    
    workflow_dir = Path(".github/workflows")
    workflow_dir.mkdir(parents=True, exist_ok=True)
    
    workflow_content = """name: Tests and Coverage

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests with coverage
      run: |
        pytest test_comprehensive_logging_pytest.py \\
          --cov=. \\
          --cov-report=xml \\
          --cov-report=term-missing \\
          --cov-fail-under=75 \\
          --junitxml=test-results.xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
        fail_ci_if_error: false
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: test-results-${{ matrix.python-version }}
        path: test-results.xml
"""
    
    with open(workflow_dir / "tests.yml", "w") as f:
        f.write(workflow_content)
    print("✅ Created .github/workflows/tests.yml")

def display_instructions():
    """Display usage instructions"""
    
    instructions = """
🎉 PYTEST TESTING ENVIRONMENT SETUP COMPLETE!

📁 Files Created:
  ✅ pytest.ini - Pytest configuration
  ✅ .coveragerc - Coverage configuration  
  ✅ conftest.py - Shared test fixtures
  ✅ requirements-test.txt - Testing dependencies
  ✅ Makefile - Easy test commands
  ✅ tox.ini - Multi-environment testing
  ✅ .github/workflows/tests.yml - CI/CD workflow
  ✅ .gitignore - Updated with test artifacts

🚀 Quick Start Commands:

1. Install testing dependencies:
   pip install -r requirements-test.txt

2. Run basic tests:
   pytest test_comprehensive_logging_pytest.py -v

3. Run tests with coverage:
   pytest test_comprehensive_logging_pytest.py --cov=. --cov-report=html

4. Use Makefile shortcuts:
   make install-test    # Install test dependencies
   make test           # Basic test run
   make test-html      # Tests with HTML coverage
   make test-full      # Complete test suite
   make clean          # Clean test artifacts

5. View coverage report:
   Open htmlcov/index.html in your browser

📊 Coverage Goals:
  - Minimum: 75% overall coverage
  - Target: 85%+ for core components
  - Branch coverage enabled for complex logic

🔧 Configuration:
  - Tests automatically discover async functions
  - Detailed logging enabled (tests.log)
  - HTML and XML coverage reports
  - CI/CD ready with GitHub Actions

📖 Full Documentation:
  See the Pytest & Coverage Testing Guide artifact for complete instructions.
"""
    
    print(instructions)

def main():
    """Main setup function"""
    
    print("🔧 SETTING UP PYTEST TESTING ENVIRONMENT")
    print("=" * 60)
    
    # Create all configuration files
    create_pytest_config()
    create_coverage_config()
    create_gitignore_entries()
    create_test_requirements()
    create_conftest_py()
    create_makefile()
    create_tox_config()
    create_github_workflow()
    
    # Display instructions
    display_instructions()

if __name__ == "__main__":
    main()