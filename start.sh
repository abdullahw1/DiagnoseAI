#!/bin/bash
# Run database migrations
echo "Running database migrations..."
flask db upgrade

# Start the application
echo "Starting application..."
exec gunicorn --bind 0.0.0.0:${PORT:-8000} main:app
