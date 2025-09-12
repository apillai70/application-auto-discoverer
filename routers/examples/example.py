#!/usr/bin/env python3
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
