#!/bin/bash

# Elite Command API Deployment Script
# This script helps deploy the application quickly

set -e

echo "🚀 Elite Command API Deployment Script"
echo "======================================"

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

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p src/database logs

# Build and start the application
echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting the application..."
docker-compose up -d

# Wait for the application to start
echo "⏳ Waiting for application to start..."
sleep 10

# Check if the application is running
if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "✅ Application is running successfully!"
    echo "🌐 Access your application at: http://localhost:5000"
    echo "📊 Health check endpoint: http://localhost:5000/api/health"
    echo ""
    echo "📝 To view logs: docker-compose logs -f"
    echo "🛑 To stop: docker-compose down"
else
    echo "❌ Application failed to start. Check logs with: docker-compose logs"
    exit 1
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "⚠️  IMPORTANT: Remember to update the following in your .env file:"
echo "   - SECRET_KEY (change from placeholder)"
echo "   - WORDSMIMIR_API_KEY (replace with real API key)"
echo "   - DATABASE_URL (if using external database)"
echo ""
echo "📖 For more deployment options, check the README.md file"

