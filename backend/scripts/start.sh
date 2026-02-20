#!/usr/bin/env bash
# start.sh — run seed (idempotent), then start the API server

set -e

echo "Running database seeder..."
python -m scripts.seed

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
