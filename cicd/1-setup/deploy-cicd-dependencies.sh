#!/bin/bash

set -e

echo Deploying AiProxy CICD Dependencies

# Create/Update the AiProxy setup/dependencies stack. This is manually created and maintained, and does not require elevated permissions

TEMPLATE_FILE=cicd/1-setup/cicd-dependencies.template.yml
STACK_NAME="aiproxy-cicd-deps"
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
  --capabilities CAPABILITY_IAM \
  --tags Key=EnvType,Value=infrastructure \
  --change-set-name $CHANGESET_NAME \
  --change-set-type $CHANGESET_TYPE \
  "$@"

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
  --output table
echo ""

read -r -p "Execute this change set? [y/N] " response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
  echo "Executing change set..."
  echo "Follow along at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks?filteringText=aiproxy-cicd-deps&filteringStatus=active&viewNested=true&hideStacks=false"
  aws cloudformation execute-change-set \
    --stack-name $STACK_NAME \
    --change-set-name $CHANGESET_NAME

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
