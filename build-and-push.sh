#!/bin/bash

# Configuration
ACR_NAME="<your-acr-name>"  # Replace with your Azure Container Registry name
IMAGE_NAME="gnuboard6"
TAG="latest"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== GNUBOARD6 Docker Build and Push ===${NC}"
echo ""

# Check if ACR_NAME is set
if [ "$ACR_NAME" == "<your-acr-name>" ]; then
    echo -e "${RED}Error: Please set your Azure Container Registry name in this script${NC}"
    echo "Edit ACR_NAME variable at the top of this script"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found!${NC}"
    echo "The Docker image will use example.env as fallback."
    echo "It's recommended to configure .env before building."
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Build cancelled."
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env file found, will be included in image${NC}"
    echo ""
fi

# Build the image
echo -e "${YELLOW}Step 1: Building Docker image...${NC}"
docker build -t ${IMAGE_NAME}:${TAG} .

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Docker build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Build successful${NC}"
echo ""

# Tag for ACR
echo -e "${YELLOW}Step 2: Tagging image for Azure Container Registry...${NC}"
docker tag ${IMAGE_NAME}:${TAG} ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${TAG}

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Docker tag failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Tagged as ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${TAG}${NC}"
echo ""

# Login to ACR (optional, comment out if already logged in)
echo -e "${YELLOW}Step 3: Logging in to Azure Container Registry...${NC}"
az acr login --name ${ACR_NAME}

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: ACR login failed. Trying docker login...${NC}"
    docker login ${ACR_NAME}.azurecr.io
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Login failed${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Login successful${NC}"
echo ""

# Push to ACR
echo -e "${YELLOW}Step 4: Pushing to Azure Container Registry...${NC}"
docker push ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${TAG}

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Docker push failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Push successful${NC}"
echo ""

# Summary
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "Image pushed to: ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${TAG}"
echo ""
echo "Next steps on your server:"
echo "  1. docker login ${ACR_NAME}.azurecr.io"
echo "  2. docker pull ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${TAG}"
echo "  3. docker run -d --name gnuboard6 --restart unless-stopped -p 8000:8000 \\"
echo "       -v ~/gnuboard6/data:/app/data \\"
echo "       -v ~/gnuboard6/.env:/app/.env:ro \\"
echo "       ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${TAG}"
echo ""
