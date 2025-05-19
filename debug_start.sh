#!/bin/bash
set -e

echo "=== Current directory ==="
pwd
echo ""

echo "=== Directory contents ==="
ls -la
echo ""

echo "=== Python path ==="
python3 -c "import sys; print(sys.path)"
echo ""

echo "=== Looking for main.py ==="
find / -name "main.py" 2>/dev/null || echo "No main.py found"
echo ""

echo "=== Looking for app directory ==="
find / -type d -name "app" 2>/dev/null || echo "No app directory found"
echo ""

echo "=== Python modules ==="
python3 -c "help('modules')" || echo "Failed to list modules"
echo ""

echo "=== Starting with direct file path ==="
if [ -f "/app/app/main.py" ]; then
  echo "Found main.py at /app/app/main.py"
  cd /app
  uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
elif [ -f "/app/main.py" ]; then
  echo "Found main.py at /app/main.py"
  cd /app
  uvicorn main:app --host 0.0.0.0 --port 8080 --reload
else
  echo "Cannot find main.py in expected locations"
  # Try without app prefix
  cd /
  echo "Trying from root directory..."
  find . -name "*.py" | grep -i main
fi