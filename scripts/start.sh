#!/bin/bash
set -e

echo "Starting Content Factory Deployment..."

if [ ! -f .env ]; then
    echo "Error: .env file not found. Please create it first."
    exit 1
fi

mkdir -p media/temp media/output

docker-compose down || true
docker-compose up -d --build

echo "Content Factory is running!"
echo "Frontend: http://77.232.128.173:3005"
echo "Backend Docs: http://77.232.128.173:8000/docs"
