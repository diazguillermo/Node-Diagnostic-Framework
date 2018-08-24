#!/bin/bash

docker build -t sdf-service . --rm
docker-compose build
docker-compose up -d

echo ""
echo "Ran docker build -t sdf-service . --rm"
echo "Ran docker-compose build"
echo "Ran docker-compose up -d"
echo "..."

echo "Finished setup\n"
