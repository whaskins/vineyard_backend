#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
until PGPASSWORD=postgres psql -h db -U postgres -d postgres -c '\q'; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL is up - continuing"

# Create database if it doesn't exist
PGPASSWORD=postgres psql -h db -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'vineyard_inventory'" | grep -q 1 || PGPASSWORD=postgres psql -h db -U postgres -c "CREATE DATABASE vineyard_inventory"

# Set proper working directory
cd /app

# Check if alembic.ini exists and run migrations
if [ -f alembic.ini ]; then
  echo "Running database migrations..."
  alembic upgrade head
else
  echo "Warning: alembic.ini not found, skipping migrations"
  # Try to locate alembic.ini
  find / -name alembic.ini 2>/dev/null || echo "Could not find alembic.ini anywhere"
fi

# Check if we need to seed the database with sample vines
if [ "${SEED_DB:-false}" = "true" ]; then
  echo "Seeding database with sample vines..."
  python -m app.seed_vines
fi

# Start the application with proper shutdown handling
echo "Starting application server..."
uvicorn app.main:app --host 0.0.0.0 --port 8080 ${RELOAD_FLAG:-} --log-level info --timeout-keep-alive 30 --timeout-graceful-shutdown 10