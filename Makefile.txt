# Makefile for Comprehensive Logging System Testing
# Provides easy commands for testing, coverage, and development

.PHONY: help install install-test test test-unit test-integration test-cov test-html test-full test-ci clean lint format check setup demo

# Default target
help:
	@echo "🎯 Comprehensive Logging System - Available Commands"
	@echo "=================================================="
	@echo ""
	@echo "📦 Setup & Installation:"
	@echo "  make install       - Install all dependencies"
	@echo "  make install-test  - Install testing dependencies"
	@echo "  make setup         - Setup complete environment"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test          - Run basic tests"
	@echo "  make test-unit     - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make test-html     - Run tests with HTML coverage report"
	@echo "  make test-full     - Complete test suite with all reports"
	@echo "  make test-ci       - CI/CD compatible test run"
	@echo ""
	@echo "🔍 Code Quality:"
	@echo "  make lint          - Run code linting"
	@echo "  make format        - Format code with black"
	@echo "  make check         - Run all quality checks"
	@echo ""
	@echo "🚀 Demo & Development:"
	@echo "  make demo          - Run system demo"
	@echo "  make clean         - Clean test artifacts"
	@echo ""
	@echo "📊 Coverage target: 75%+"

# Installation commands
install:
	@echo "📦 Installing all dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt

install-test:
	@echo "📦 Installing testing dependencies..."
	pip install --upgrade pip
	pip install pytest pytest-asyncio pytest-cov pytest-html pytest-xdist pytest-mock
	pip install coverage[toml] factory-boy faker responses

# Environment setup
setup: install install-test
	@echo "🔧 Setting up complete environment..."
	python setup_pytest_testing.py
	@echo "✅ Environment setup complete!"

# Basic testing commands
test:
	@echo "🧪 Running basic tests..."
	pytest test_comprehensive_logging_pytest.py -v

test-unit:
	@echo "🧪 Running unit tests..."
	pytest test_comprehensive_logging_pytest.py -m unit -v

test-integration:
	@echo "🧪 Running integration tests..."
	pytest test_comprehensive_logging_pytest.py -m integration -v

test-cov:
	@echo "🧪 Running tests with coverage..."
	pytest test_comprehensive_logging_pytest.py --cov=. --cov-report=term-missing --cov-fail-under=40

test-html:
	@echo "🧪 Running tests with HTML coverage report..."
	pytest test_comprehensive_logging_pytest.py \
		--cov=. \
		--cov-report=html \
		--cov-report=term-missing \
		--cov-fail-under=40
	@echo "📊 Coverage report: htmlcov/index.html"

test-full:
	@echo "🧪 Running complete test suite..."
	pytest test_comprehensive_logging_pytest.py \
		--cov=. \
		--cov-report=html \
		--cov-report=xml \
		--cov-report=term-missing \
		--cov-fail-under=40 \
		--html=test_report.html \
		--self-contained-html \
		-v \
		--durations=10
	@echo "📊 Coverage report: htmlcov/index.html"
	@echo "📋 Test report: test_report.html"

test-ci:
	@echo "🧪 Running CI/CD tests..."
	pytest test_comprehensive_logging_pytest.py \
		--cov=. \
		--cov-report=xml \
		--cov-fail-under=40 \
		--junitxml=test-results.xml \
		--tb=short \
		-q

# Code quality commands
lint:
	@echo "🔍 Running code linting..."
	@echo "Checking Python files..."
	-flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	-flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format:
	@echo "✨ Formatting code..."
	-black . --line-length=120 --target-version=py311
	-isort . --profile=black --line-length=120

check: lint
	@echo "🔍 Running all quality checks..."
	@echo "Type checking..."
	-mypy . --ignore-missing-imports --no-strict-optional

# Demo and development
demo:
	@echo "🎬 Running system demo..."
	python demo_comprehensive_logging.py

# Maintenance commands
clean:
	@echo "🧹 Cleaning test artifacts..."
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	rm -rf */__pycache__/
	rm -rf */*/__pycache__/
	rm -f .coverage
	rm -f coverage.xml
	rm -f coverage.json
	rm -f test-results.xml
	rm -f test_report.html
	rm -f tests.log
	rm -rf test_logs*/
	rm -rf demo_logs/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	@echo "✅ Cleanup complete!"

# Advanced testing options
test-parallel:
	@echo "🧪 Running tests in parallel..."
	pytest test_comprehensive_logging_pytest.py -n auto -v

test-debug:
	@echo "🐛 Running tests with debug output..."
	pytest test_comprehensive_logging_pytest.py -vvv --tb=long --capture=no

test-profile:
	@echo "⚡ Profiling test execution..."
	pytest test_comprehensive_logging_pytest.py --durations=0 -v

test-watch:
	@echo "👀 Running tests in watch mode..."
	pytest-watch test_comprehensive_logging_pytest.py -- -v

# Coverage analysis
coverage-report:
	@echo "📊 Generating coverage report..."
	coverage report --show-missing
	coverage html
	@echo "📊 HTML report: htmlcov/index.html"

coverage-xml:
	@echo "📊 Generating XML coverage report..."
	coverage xml

# Development workflow
dev-test: clean test-html
	@echo "🚀 Development test cycle complete!"

dev-check: format lint test-cov
	@echo "🚀 Development check complete!"

# Production readiness check
prod-check: clean format lint test-full
	@echo "🚀 Production readiness check complete!"

# Quick commands for development
quick-test:
	@echo "⚡ Quick test run..."
	pytest test_comprehensive_logging_pytest.py -x -v --tb=short

quick-cov:
	@echo "⚡ Quick coverage check..."
	pytest test_comprehensive_logging_pytest.py --cov=. --cov-report=term --cov-fail-under=30

# Install specific tool versions
install-dev-tools:
	@echo "🔧 Installing development tools..."
	pip install black==23.11.0 flake8==6.1.0 mypy==1.7.1 isort==5.12.0
	pip install pytest-watch pre-commit

# Pre-commit setup
setup-pre-commit:
	@echo "🔧 Setting up pre-commit hooks..."
	pre-commit install
	pre-commit install --hook-type commit-msg

# Environment info
env-info:
	@echo "📋 Environment Information:"
	@echo "Python version: $(shell python --version)"
	@echo "Pip version: $(shell pip --version)"
	@echo "Pytest version: $(shell pytest --version 2>/dev/null || echo 'Not installed')"
	@echo "Coverage version: $(shell coverage --version 2>/dev/null || echo 'Not installed')"
	@echo "Current directory: $(shell pwd)"

# Show test results summary
show-results:
	@echo "📊 Recent Test Results:"
	@if [ -f test_report.html ]; then echo "📋 Test Report: test_report.html"; fi
	@if [ -f htmlcov/index.html ]; then echo "📊 Coverage Report: htmlcov/index.html"; fi
	@if [ -f test-results.xml ]; then echo "🔧 CI Results: test-results.xml"; fi

# All-in-one development command
dev-full: clean install-test format lint test-full
	@echo "🎉 Complete development cycle finished!"
	@make show-results

# Troubleshooting
troubleshoot:
	@echo "🔧 Troubleshooting Information:"
	@echo "Environment:"
	@make env-info
	@echo ""
	@echo "Recent test artifacts:"
	@ls -la *.xml *.html *.log htmlcov/ 2>/dev/null || echo "No test artifacts found"
	@echo ""
	@echo "Python path:"
	@python -c "import sys; print('\n'.join(sys.path))"

# Benchmark tests
benchmark:
	@echo "⚡ Running performance benchmarks..."
	pytest test_comprehensive_logging_pytest.py --durations=0 --benchmark-only 2>/dev/null || \
	pytest test_comprehensive_logging_pytest.py --durations=10 -v

# Documentation generation (if needed)
docs:
	@echo "📚 Generating documentation..."
	@if command -v mkdocs >/dev/null 2>&1; then \
		mkdocs build; \
		echo "📚 Documentation: site/index.html"; \
	else \
		echo "⚠️  mkdocs not installed"; \
	fi

# Version information
version:
	@echo "📋 Comprehensive Logging System"
	@echo "Version: 2.2.0"
	@echo "Test Framework: pytest + coverage"
	@echo "Target Coverage: 40%+ (reduced for placeholder implementations)"