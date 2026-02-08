#!/bin/bash
set -e

# Run database migrations
echo "Running database migrations..."
echo "Current directory: $(pwd)"
echo "Checking migrations directory..."
ls -la migrations/versions/ || echo "Migrations directory not found"

# Show current database revision
echo "Current database revision:"
flask db current || echo "No current revision (fresh database)"

# Run migrations
echo "Applying migrations..."
flask db upgrade

echo "Migration complete. Current revision:"
flask db current

# Start the application with increased timeout for AI processing
echo "Starting application..."
exec gunicorn --bind 0.0.0.0:${PORT:-8000} --timeout 300 --workers 2 main:app
