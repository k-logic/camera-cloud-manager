#!/bin/bash
set -e

# 1. Alembic migration
echo "Running Alembic migrations..."
alembic upgrade head

# 2. Seed initial data (dev only)
if [ "$SEED_DB" = "1" ]; then
  echo "Seeding initial data..."
  python seed.py
fi

# 3. Start uvicorn
echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
