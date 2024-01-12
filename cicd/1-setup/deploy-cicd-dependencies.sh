#!/bin/bash

set -e

echo Deploying AiProxy CICD Dependencies

# Create/Update the AiProxy setup/dependencies stack. This is manually created and maintained, and does not require elevated permissions

TEMPLATE_FILE=cicd/1-setup/cicd-dependencies.template.yml

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
  CHANGE_SET_NAME="aiproxy-cicd-deps-changeset-$(date +%s)"
  aws cloudformation create-change-set \
    --stack-name aiproxy-cicd-deps \
    --change-set-name $CHANGE_SET_NAME \
    --template-body file://${TEMPLATE_FILE} \
    --capabilities CAPABILITY_IAM \
    --tags EnvType=infrastructure \
    "$@"

  echo "Change set created. You can review it at:"
  echo "https://console.aws.amazon.com/cloudformation/home?region=$REGION#/stacks/changesets/changes?stackId=arn:aws:cloudformation:$REGION:$ACCOUNT:stack/aiproxy-cicd-deps/*&changeSetId=arn:aws:cloudformation:$REGION:$ACCOUNT:changeSet/$CHANGE_SET_NAME"

  read -r -p "Would you like to execute the change set? [y/N] " response
  if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]
  then
    echo Executing change set...
    aws cloudformation execute-change-set \
      --stack-name aiproxy-cicd-deps \
      --change-set-name $CHANGE_SET_NAME
    echo Complete!
  else
    echo Exiting...
  fi
else
  echo Exiting...
fi