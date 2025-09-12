## 📚 API Reference

### DebugResult Class
```python
@dataclass
class DebugResult:
    success: bool              # Overall success status
    execution_time: float      # Time taken to execute
    memory_usage: float        # Memory used (MB)
    syntax_valid: bool         # Syntax validation result
    syntax_errors: List[str]   # List of syntax errors
    runtime_errors: List[str]  # List of runtime errors
    warnings: List[str]        # List of warnings
    output: str               # Program output
    file_path: str            # Path to debugged file
    language: str             # Detected language
    timestamp: str            # ISO timestamp
```

### CLI Arguments
```
--file, -f          File to debug
--mode, -m          Debug mode (auto/python/javascript/html)
--watch, -w         Directory to watch for changes
--output, -o        Output format (console/json)
--log-level         Logging level (DEBUG/INFO/WARNING/ERROR)
--browser, -b       Enable browser debugging
--performance, -p   Enable performance monitoring
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - feel free to use and modify as needed.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the examples
3. Create an issue with detailed information
4. Include debug output and system information