#!/bin/bash

set -e

echo "Validating Cloudformation Templates via cfn-lint docker..."
docker run --rm -i 
cfn-lint cicd/1-setup/*.template.yml
cfn-lint cicd/2-cicd/*.template.yml
cfn-lint cicd/3-app/aiproxy/template.yml

echo "Validating Dockerfile..."
docker run --rm -i hadolint/hadolint < Dockerfile
