#!/bin/bash

set -e

if [ -n "$CODEBUILD_BUILD_ID" ]; then
    # CodeBuild environment
    IMAGE_TAG=${CODEBUILD_RESOLVED_SOURCE_VERSION:0:7}
else
    # Local Git repository
    IMAGE_TAG=$(git rev-parse --short HEAD)
fi

IMAGE_NAME=aiproxy

echo "Building Docker Image ${IMAGE_NAME}:${IMAGE_TAG}..."
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
