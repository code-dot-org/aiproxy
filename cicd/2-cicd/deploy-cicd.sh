#!/bin/bash

set -e

echo Deploying AiProxy CICD Pipeline

# Create/Update the AiProxy build/deploy pipeline stack. This is manually created and maintained, but should not require elevated permissions.
# Options include:
# - TARGET_BRANCH: Defaults to `main`, passed as a Parameter for "cicd/2-cicd/cicd.template.yml"
# - ENVIRONMENT_TYPE: Can be 'production' (default) or 'development', passed as a Parameter for "cicd/2-cicd/cicd.template.yml"
# - GITHUB_BADGE_ENABLED: defaults to true, passed as a Parameter for "cicd/2-cicd/cicd.template.yml"

# 'Developer' role requires a specific service role for all CloudFormation operations.
if [[ $(aws sts get-caller-identity --query Arn --output text) =~ "assumed-role/Developer/" ]]; then
  # Append the role-arn option to the positional parameters $@ passed to cloudformation commands.
  set -- "$@" --role-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/admin/CloudFormationService"
fi

# Default to main branch, but support pipelines using other branches
TARGET_BRANCH=${TARGET_BRANCH-'main'}

if [ "$TARGET_BRANCH" == "main" ]
then
  STACK_NAME="aiproxy-cicd"
else
  # only allow alphanumeric branch names that may contain an internal hyphen.
  # to avoid complicated logic elsewhere, we're constraining it here.
  if [[ "$TARGET_BRANCH" =~ ^[a-z0-9]([-a-z0-9]*[a-z0-9])$ ]]; then
    STACK_NAME="aiproxy-${TARGET_BRANCH}-cicd"
  else
    echo "Invalid branch name '${TARGET_BRANCH}', branches must be alphanumeric and may contain hyphens."
    exit
  fi
fi

ENVIRONMENT_TYPE=${ENVIRONMENT_TYPE-'production'}
GITHUB_BADGE_ENABLED=${GITHUB_BADGE_ENABLED-'true'}

TEMPLATE_FILE=cicd/2-cicd/cicd.template.yml
CHANGESET_NAME="deploy-$(date +%Y%m%d%H%M%S)"

echo Validating cloudformation template...
aws cloudformation validate-template \
  --template-body file://${TEMPLATE_FILE} \
  | cat

ACCOUNT=$(aws sts get-caller-identity --query "Account" --output text)

if aws cloudformation describe-stacks --stack-name $STACK_NAME &>/dev/null; then
  CHANGESET_TYPE="UPDATE"
else
  CHANGESET_TYPE="CREATE"
fi

echo "Creating change set '$CHANGESET_NAME' for stack '$STACK_NAME' in account $ACCOUNT..."
aws cloudformation create-change-set \
  --stack-name $STACK_NAME \
  --template-body file://${TEMPLATE_FILE} \
  --parameters \
    ParameterKey=GitHubBranch,ParameterValue=$TARGET_BRANCH \
    ParameterKey=GitHubBadgeEnabled,ParameterValue=$GITHUB_BADGE_ENABLED \
    ParameterKey=EnvironmentType,ParameterValue=$ENVIRONMENT_TYPE \
  --capabilities CAPABILITY_IAM \
  --tags Key=EnvType,Value=${ENVIRONMENT_TYPE} \
  --change-set-name $CHANGESET_NAME \
  --change-set-type $CHANGESET_TYPE \
  "$@" \
  | cat

echo Waiting for change set to be ready...
set +e
aws cloudformation wait change-set-create-complete \
  --stack-name $STACK_NAME \
  --change-set-name $CHANGESET_NAME
WAIT_EXIT=$?
set -e

if [ $WAIT_EXIT -ne 0 ]; then
  STATUS=$(aws cloudformation describe-change-set \
    --stack-name $STACK_NAME \
    --change-set-name $CHANGESET_NAME \
    --query "StatusReason" --output text)
  echo "Change set failed: $STATUS"
  aws cloudformation delete-change-set \
    --stack-name $STACK_NAME \
    --change-set-name $CHANGESET_NAME
  exit 0
fi

echo ""
echo "=== Change Set ==="
aws cloudformation describe-change-set \
  --stack-name $STACK_NAME \
  --change-set-name $CHANGESET_NAME \
  --query "Changes[*].ResourceChange.{Action:Action,Resource:LogicalResourceId,Type:ResourceType,Replacement:Replacement}" \
  --output table \
  | cat
echo ""

read -r -p "Execute this change set? [y/N] " response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
  echo "Executing change set..."
  aws cloudformation execute-change-set \
    --stack-name $STACK_NAME \
    --change-set-name $CHANGESET_NAME \
    "$@"

  echo "Waiting for stack to complete..."
  if [ "$CHANGESET_TYPE" = "CREATE" ]; then
    aws cloudformation wait stack-create-complete --stack-name $STACK_NAME
  else
    aws cloudformation wait stack-update-complete --stack-name $STACK_NAME
  fi

  echo Complete!
else
  echo "Discarding change set..."
  aws cloudformation delete-change-set \
    --stack-name $STACK_NAME \
    --change-set-name $CHANGESET_NAME
  echo Exiting...
fi
