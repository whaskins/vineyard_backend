#!/bin/bash
set -e

# Define variables
ECR_REPOSITORY="283282846400.dkr.ecr.us-east-1.amazonaws.com/vineyard/backend"
VERSION="1.27"  # Fixed Pydantic v2 field_validator syntax
TAG="${ECR_REPOSITORY}:${VERSION}"
PLATFORM="linux/amd64"  # Match the platform in docker-compose.yml

# Build the Docker image
echo "Building Docker image for vineyard backend..."
docker buildx build --platform ${PLATFORM} --load -t ${TAG} .

# Log in to Amazon ECR
echo "Logging in to Amazon ECR..."
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 283282846400.dkr.ecr.us-east-1.amazonaws.com

# Push the image to ECR
echo "Pushing image to ECR..."
docker push ${TAG}

echo "Image successfully pushed to ECR: ${TAG}"
echo "Remember to update the docker-compose.yml file with the new version: ${VERSION}"