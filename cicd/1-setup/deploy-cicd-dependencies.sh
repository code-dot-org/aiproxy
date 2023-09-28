#!/bin/bash

set -e

echo Deploying AiProxy CICD Dependencies

# Create/Update the AiProxy setup/dependencies stack. This is manually created and maintained, and does not require elevated permissions

TEMPLATE_FILE=cicd/1-setup/cicd-dependencies.template.yml

echo Validating cloudformation template...
aws cloudformation validate-template \
  --template-body file://${TEMPLATE_FILE} \
  | cat

ACCOUNT=$(aws sts get-caller-identity --query "Account" --output text)

read -r -p "Would you like to deploy this template to AWS account $ACCOUNT? [y/N] " response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]
then
  echo Updating cloudformation stack...
  aws cloudformation deploy \
    --stack-name aiproxy-cicd-deps \
    --template-file ${TEMPLATE_FILE} \
    --capabilities CAPABILITY_IAM \
    --tags EnvType=infrastructure \
    "$@"

  echo Complete!
else
  echo Exiting...
fi
