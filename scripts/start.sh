#!/bin/bash
set -e

echo "======================================"
echo "  Content Factory - Starting..."
echo "======================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "!!! IMPORTANT !!!"
    echo "Please edit .env file and add your API keys before continuing."
    echo "Then run this script again."
    echo ""
    exit 1
fi

# Create media directories
mkdir -p backend/media/{videos,audio,thumbnails,temp}

# Start services
echo "Starting Docker containers..."
docker-compose up -d

echo ""
echo "======================================"
echo "  Content Factory is running!"
echo "======================================"
echo ""
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "  To view logs: docker-compose logs -f"
echo "  To stop:      docker-compose down"
echo ""
