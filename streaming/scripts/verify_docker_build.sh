#!/bin/bash

# Script to verify Docker configuration
# Usage: bash scripts/verify_docker_build.sh

echo "🐳 Verifying Dockerfiles exist..."

FILES=(
    "spark/Dockerfile"
    "airflow/Dockerfile.airflow"
    "dashboard/Dockerfile.dashboard"
    "docker-compose.yml"
)

ERRORS=0

for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing: $file"
        ERRORS=$((ERRORS+1))
    else
        echo "✅ Found: $file"
    fi
done

echo "🐳 Verifying docker-compose syntax..."
if command -v docker-compose &> /dev/null; then
    docker-compose config > /dev/null
    if [ $? -eq 0 ]; then
        echo "✅ docker-compose.yml syntax is valid."
    else
        echo "❌ docker-compose.yml has syntax errors!"
        ERRORS=$((ERRORS+1))
    fi
else
    echo "⚠️ docker-compose not found, skipping syntax check."
fi

if [ $ERRORS -eq 0 ]; then
    echo "✅ All checks passed!"
else
    echo "❌ Found $ERRORS errors."
    exit 1
fi
