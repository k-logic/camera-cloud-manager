#!/bin/bash
set -e

# 1. Alembic migration
echo "Running Alembic migrations..."
alembic upgrade head

# 2. Seed initial data (admin user, test users, etc.)
echo "Seeding initial data..."
python seed.py

# 3. Start uvicorn
echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
