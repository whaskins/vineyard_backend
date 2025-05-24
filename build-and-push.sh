#!/bin/bash
set -e

# Define variables
ECR_REPOSITORY="283282846400.dkr.ecr.us-east-1.amazonaws.com/vineyard/backend"
DATE_TAG=$(date +"%Y%m%d")
LATEST_VERSION=$(aws ecr describe-images --repository-name vineyard/backend --region us-east-1 --query 'sort_by(imageDetails,& imagePushedAt)[-1].imageTags[0]' --output text | grep -oE '[0-9]+\.[0-9]+' || echo "1.27")
MAJOR_VERSION=$(echo $LATEST_VERSION | cut -d. -f1)
MINOR_VERSION=$(echo $LATEST_VERSION | cut -d. -f2)
NEW_MINOR=$((MINOR_VERSION + 1))
NEW_VERSION="${MAJOR_VERSION}.${NEW_MINOR}"
DATE_VERSION_TAG="${ECR_REPOSITORY}:${NEW_VERSION}-${DATE_TAG}"
VERSION_TAG="${ECR_REPOSITORY}:${NEW_VERSION}"
LATEST_TAG="${ECR_REPOSITORY}:latest"
PLATFORM="linux/amd64"  # Match the platform in docker-compose.yml

echo "Current latest version: ${LATEST_VERSION}"
echo "Building new version: ${NEW_VERSION}"

# Build the Docker image
echo "Building Docker image for vineyard backend..."
docker buildx build --platform ${PLATFORM} --load -t ${VERSION_TAG} -t ${DATE_VERSION_TAG} -t ${LATEST_TAG} .

# Log in to Amazon ECR
echo "Logging in to Amazon ECR..."
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 283282846400.dkr.ecr.us-east-1.amazonaws.com

# Push the images to ECR
echo "Pushing images to ECR..."
docker push ${VERSION_TAG}
docker push ${DATE_VERSION_TAG}
docker push ${LATEST_TAG}

echo "Images successfully pushed to ECR:"
echo "- ${VERSION_TAG}"
echo "- ${DATE_VERSION_TAG}"
echo "- ${LATEST_TAG}"
echo "Remember to update the docker-compose.yml file with the new version: ${NEW_VERSION}"