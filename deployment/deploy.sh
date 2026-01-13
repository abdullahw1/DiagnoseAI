#!/bin/bash

# DiagnoseAI Deployment Script
set -e

echo "🏥 DiagnoseAI Deployment Script"
echo "================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.production .env
    echo "📝 Please edit .env file with your configuration before continuing."
    echo "   Required: SECRET_KEY, OPENAI_API_KEY"
    read -p "Press Enter after updating .env file..."
fi

# Validate required environment variables
source .env
if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your-very-secure-secret-key-here-change-this" ]; then
    echo "❌ Please set a secure SECRET_KEY in .env file"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your-openai-api-key-here" ]; then
    echo "❌ Please set your OPENAI_API_KEY in .env file"
    exit 1
fi

echo "✅ Environment configuration validated"

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run database migrations
echo "📊 Running database migrations..."
docker-compose exec web flask db upgrade

echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Application is now running at:"
echo "   http://localhost:5003"
echo ""
echo "📋 Useful commands:"
echo "   View logs:     docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart:       docker-compose restart"
echo ""
echo "🔧 For production with HTTPS:"
echo "   1. Configure SSL certificates in ./ssl/ directory"
echo "   2. Update nginx.conf with your domain"
echo "   3. Run: docker-compose --profile production up -d"