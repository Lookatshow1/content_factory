#!/bin/bash
set -e

echo "======================================"
echo "  Content Factory - Initial Setup"
echo "======================================"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Please install Docker first."
    echo "https://docs.docker.com/engine/install/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose not found. Please install Docker Compose."
    exit 1
fi

echo "Docker found: $(docker --version)"
echo "Docker Compose found: $(docker-compose --version)"
echo ""

# Create .env if not exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Create directories
echo "Creating directories..."
mkdir -p backend/media/{videos,audio,thumbnails,temp}
mkdir -p frontend/.next

# Build containers
echo "Building Docker containers (this may take a few minutes)..."
docker-compose build

echo ""
echo "======================================"
echo "  Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file and add your API keys:"
echo "   - ANTHROPIC_API_KEY (required)"
echo "   - ELEVENLABS_API_KEY (required)"
echo "   - HEYGEN_API_KEY (required)"
echo "   - Plus any publishing platform keys"
echo ""
echo "2. Start the services:"
echo "   ./scripts/start.sh"
echo ""
echo "3. Open http://localhost:3000"
echo ""
