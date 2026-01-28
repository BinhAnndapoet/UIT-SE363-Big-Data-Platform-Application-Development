#!/bin/bash

# Script to run tests with options
# Usage: bash scripts/test_runner.sh [option]
# Options: all, ingestion, spark, db, verify

# Ensure we are in the streaming directory
if [[ $(basename $(pwd)) == "scripts" ]]; then
    cd ..
fi

# Add current directory to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Function to run pytest
run_pytest() {
    local target=$1
    echo "---------------------------------------------------"
    echo "🚀 Running Tests: $target"
    echo "---------------------------------------------------"
    pytest $target -v
}

# Function to verify docker
run_verify() {
    echo "---------------------------------------------------"
    echo "🐳 Verifying Docker Configuration"
    echo "---------------------------------------------------"
    bash scripts/verify_docker_build.sh
}

# Function to display menu
show_menu() {
    echo "========================================="
    echo "      TikTok Safety Project - Test Runner"
    echo "========================================="
    echo "1) Run ALL Unit Tests"
    echo "2) Run Ingestion Layer Tests"
    echo "3) Run Spark/AI Layer Tests"
    echo "4) Run Database Layer Tests"
    echo "5) Verify Docker Configuration"
    echo "q) Quit"
    echo "-----------------------------------------"
    read -p "Select an option [1-5/q]: " choice
    
    case $choice in
        1) run_pytest "tests/" ;;
        2) run_pytest "tests/test_ingestion_layer.py" ;;
        3) run_pytest "tests/test_spark_layer.py" ;;
        4) run_pytest "tests/test_db_layer.py" ;;
        5) run_verify ;;
        q) exit 0 ;;
        *) echo "❌ Invalid option!"; exit 1 ;;
    esac
}

# Check if argument is provided
if [ -n "$1" ]; then
    case $1 in
        all) run_pytest "tests/" ;;
        ingestion) run_pytest "tests/test_ingestion_layer.py" ;;
        spark) run_pytest "tests/test_spark_layer.py" ;;
        db) run_pytest "tests/test_db_layer.py" ;;
        verify) run_verify ;;
        *) echo "❌ Usage: $0 {all|ingestion|spark|db|verify}"; exit 1 ;;
    esac
else
    # No argument -> Show Interactive Menu
    show_menu
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Done."
else
    echo ""
    echo "❌ Test run failed."
fi
