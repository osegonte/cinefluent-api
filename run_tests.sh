#!/bin/bash

# Simple test runner for CineFluent API

echo "🧪 Running CineFluent API Tests"
echo "==============================="

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing test requirements..."
    pip install -r requirements-test.txt
fi

# Run tests
echo "Running tests..."
pytest tests/ -v

# Check if tests passed
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
else
    echo ""
    echo "❌ Some tests failed. Check the output above."
    exit 1
fi
