#!/bin/bash

echo Deploying AiProxy CICD Pipeline

# Create/Update the AiProxy build/deploy pipeline stack. This is manually created and maintained, but should not require elevated permissions.
# Options include:
# - TARGET_BRANCH: Defaults to `main`, passed as a Parameter for "cicd/2-cicd/cicd.template.yml"
# - ENVIRONMENT_TYPE: Can be 'production' (default) or 'development', passed as a Parameter for "cicd/2-cicd/cicd.template.yml"
# - GITHUB_BADGE_ENABLED: defaults to true, passed as a Parameter for "cicd/2-cicd/cicd.template.yml"

# The branch name may become part of a domain name, so we need to validate it.
validate_branch_name() {
  local branch_name=$1
  if [[ ! $branch_name =~ ^[a-z0-9]([-a-z0-9]*[a-z0-9])$ ]]; then
    echo "Invalid branch name '${branch_name}', branches must be alphanumeric and may contain hyphens."
    exit 1
  fi
}

# 'Developer' role requires a specific service role for all CloudFormation operations.
if [[ $(aws sts get-caller-identity --query Arn --output text) =~ "assumed-role/Developer/" ]]; then
  # Append the role-arn option to the positional parameters $@ passed to cloudformation deploy.
  set -- "$@" --role-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/admin/CloudFormationService"
fi

ENVIRONMENT_TYPE=${ENVIRONMENT_TYPE:-'production'}
GITHUB_BADGE_ENABLED=${GITHUB_BADGE_ENABLED:-'true'}
TARGET_BRANCH=${TARGET_BRANCH:-'main'}

if [ "$TARGET_BRANCH" == "main" ]
then
  STACK_NAME="aiproxy-cicd"
else
  validate_branch_name "$TARGET_BRANCH"
  STACK_NAME="aiproxy-${TARGET_BRANCH}-cicd"
fi

TEMPLATE_FILE=cicd/2-cicd/cicd.template.yml

echo Validating cloudformation template...
aws cloudformation validate-template \
  --template-body file://${TEMPLATE_FILE} \
  > /dev/null

ACCOUNT=$(aws sts get-caller-identity --query "Account" --output text)
REGION=$(aws configure get region)

read -r -p "Would you like to create a change set for this template in AWS account $ACCOUNT? [y/N] " response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]
then
  echo Creating change set...
  CHANGE_SET_NAME="${STACK_NAME}-changeset-$(date +%s)"
  aws cloudformation create-change-set \
    --stack-name $STACK_NAME \
    --change-set-name $CHANGE_SET_NAME \
    --template-body file://${TEMPLATE_FILE} \
    --parameters ParameterKey=GitHubBranch,ParameterValue=$TARGET_BRANCH ParameterKey=GitHubBadgeEnabled,ParameterValue=$GITHUB_BADGE_ENABLED ParameterKey=EnvironmentType,ParameterValue=$ENVIRONMENT_TYPE \
    --capabilities CAPABILITY_IAM \
    --tags Key=EnvType,Value=${ENVIRONMENT_TYPE} \
    "$@"

  echo "Change set created. You can review it at:"
  echo "https://console.aws.amazon.com/cloudformation/home?region=$REGION#/stacks/changesets/changes?stackId=arn:aws:cloudformation:$REGION:$ACCOUNT:stack/$STACK_NAME/*&changeSetId=arn:aws:cloudformation:$REGION:$ACCOUNT:changeSet/$CHANGE_SET_NAME"

  read -r -p "Would you like to execute the change set? [y/N] " response
  if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]
  then
    echo Executing change set...
    aws cloudformation execute-change-set \
      --stack-name $STACK_NAME \
      --change-set-name $CHANGE_SET_NAME
    echo Complete!
  else
    echo Exiting...
  fi
else
  echo Exiting...
fi
