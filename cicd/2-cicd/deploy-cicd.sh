#!/bin/bash

echo Deploying OpenAiProxy CICD Pipeline

# Create/Update the OpenAiProxy build/deploy pipeline stack. This is manually created and maintained, but should not require elevated permissions.
# Options include:
# - TARGET_BRANCH: Defaults to `main`, passed as a Parameter for "cicd/2-cicd/cicd.template.yml"
# - ENVIRONMENT_TYPE: Can be 'production' (default) or 'development', passed as a Parameter for "cicd/2-cicd/cicd.template.yml"
# - GITHUB_BADGE_ENABLED: defaults to true, passed as a Parameter for "cicd/2-cicd/cicd.template.yml"

# 'Developer' role requires a specific service role for all CloudFormation operations.
if [[ $(aws sts get-caller-identity --query Arn --output text) =~ "assumed-role/Developer/" ]]; then
  # Append the role-arn option to the positional parameters $@ passed to cloudformation deploy.
  set -- "$@" --role-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/admin/CloudFormationService"
fi

# Default to main branch, but support pipelines using other branches
TARGET_BRANCH=${TARGET_BRANCH-'main'}

if [ "$TARGET_BRANCH" == "main" ]
then
  STACK_NAME="openaiproxy-cicd"
else
  # only allow alphanumeric branch names that may contain an internal hyphen.
  # to avoid complicated logic elsewhere, we're constraining it here.
  if [[ "$TARGET_BRANCH" =~ ^[a-z0-9]([-a-z0-9]*[a-z0-9])$ ]]; then
    STACK_NAME="openaiproxy-${TARGET_BRANCH}-cicd"
  else
    echo "Invalid branch name '${TARGET_BRANCH}', branches must be alphanumeric and may contain hyphens."
    exit
  fi
fi

ENVIRONMENT_TYPE=${ENVIRONMENT_TYPE-'production'}
GITHUB_BADGE_ENABLED=${GITHUB_BADGE_ENABLED-'true'}

TEMPLATE_FILE=cicd/2-cicd/cicd.template.yml

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
    --stack-name $STACK_NAME \
    --template-file $TEMPLATE_FILE \
    --parameter-overrides GitHubBranch=$TARGET_BRANCH GitHubBadgeEnabled=$GITHUB_BADGE_ENABLED EnvironmentType=$ENVIRONMENT_TYPE \
    --capabilities CAPABILITY_IAM \
    --tags EnvType=${ENVIRONMENT_TYPE} \
    "$@"

  echo Complete!
else
  echo Exiting...
fi
