#!/bin/bash

# Script to run unit tests
# Usage: bash scripts/run_unit_tests.sh

echo "📦 Installing test dependencies..."
pip install pytest pytest-mock pandas psycopg2-binary

echo "🚀 Running Unit Tests..."
# Add current directory to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

pytest tests/ -v

if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed!"
    exit 1
fi
