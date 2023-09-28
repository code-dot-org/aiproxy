# AiProxy CI/CD
## CI/CD Implementation Overview

There are three phases of the CI/CD configuration. They are best explained in reverse order from the way they flow in practice.

### 3 - App

All of the application resources are defined in a CloudFormation template. We could manually update the CloudFormation stack with an updated template every time we have a code change, but it is considerably less effort and less risky to automate this with a CI/CD pipeline. By using parameters, we can use the same code to deploy multiple environments.

We also keep some CodeBuild configuration here, as this code tends to be more coupled to current application code, than the CI/CD code in the next section.

* **aiproxy/**
  * "template.yml" - AWS resources for the aiproxy application
  * "buildspec.yml" - Main build/verify instructions, used during pipeline builds
  * "pr-buildspec.yml" - Similar build/verify instructions, used during PR verification
  * "integration-test-buildspec.yml" - Instructions for integration tests run against a deployed environment
  * **config/** - JSON configuration for each environment

### 2 - CI/CD

In order to trigger the application resources to be updated upon changes to the source code, we need CI/CD resources. This is accomplished by a CloudFormation template that defines a stack of resources, primarily including a CodeBuild project and a CodePipeline pipeline which update the [App Stack](#3---app). These CI/CD resources only need to be created once per deployable branch, `main` in our case (we might choose to create development environments by launching a new CI/CD stack targeting a different branch).

These resources are deployed manually when changes occur. We could make yet another CodePipeline resource in the [Setup](#1---setup) section, but not today.

* "deploy-cicd.sh" - Shell script to create/update this stack
* "cicd.template.yml" - AWS resources for the CI/CD infrastructure

### 1 - Setup

Finally, all of the above need some Roles to exist in the AWS accounts before we can run things with appropriate permisions. These roles are exported and used elsewhere. Elevated permissions are required to update these (likely by an Infra Engineer). This only needs to be created once, as roles and other resources can be shared by all CI/CD stacks for this application.

* "deploy-setup.sh" - Shell script to create/update this stack
* "setup.template.yml" - AWS resources for the Setup infrastructure

## Deploying CI/CD resources

### Deploying the `main` CI/CD Pipeline

_Note: If you receive errors with the 'aws-google' gem, you may need to switch to Ruby 3.1 first, via `rbenv local 3.1`._

1. Create/Update the Setup stack (one time, or when changes to the Setup stack occur)
   `cicd/1-setup/deploy-cicd-dependencies.sh` (with elevated AWS permissions)
2. Create/Update the CI/CD stack (one time, or when changes to the CI/CD stack occur)
   `cicd/2-cicd/deploy-cicd.sh`
3. Trigger an update of the Pipeline by doing one of the following.
   1. Merge a PR
   2. Push a commit to `main`
   3. Press the "Release Change" button on the Pipeline overview page in the AWS Console.

### Deploying a Development environment

You can create a Development (aka 'adhoc') environment by setting the `ENVIRONMENT_TYPE` flag on the cicd deploy script. This will create a CI/CD pipeline that will watch for updates to your `TARGET_BRANCH`. The difference between a production and a development pipeline can be seen in "cicd.template.yml" by following where the `Conditions` are used. In short, an development pipeline creates a single environment using "dev.config.yml", while a production deployment will create a Test environment and a Prod environment using the relevent config files, running automated tests between them.

Notes:

* branch names are used as a unique identifier (stack name, among others). Therefore we can only deploy one CI/CD pipeline per branch per AWS Account.
* your branch name cannot contain the character `/`, as this causes issues in AWS. Note that resources will be deployed with the tags `{EnvType = development}`.
* for now, these must deployed to the production AWS account. There is planned work to enable these to be deployed to the Dev AWS account.

Steps

- First, login to the AWS production account. You can follow steps 1-3 [here](https://docs.google.com/document/d/1mMQK6HhniLsz9lynzhUcm7Tcw_2WVLBxADe0WzqL6rM/edit#bookmark=id.wtrskofu4rb9) to do so.
- Then, run the following command with your branch name:
   ```
   TARGET_BRANCH=mybranch ENVIRONMENT_TYPE=development cicd/2-cicd/deploy-cicd.sh
   ```

### Deploying a full CI/CD pipeline for a different branch

By setting the `TARGET_BRANCH` you can create a new CI/CD pipeline that watches for PR's and changes to the specified branch, deploying a Test and Production environment just like the standard pipeline. Note that resources will be deployed with the tags `{EnvType = production}` or `{EnvType = test}`.

```
TARGET_BRANCH=mybranch cicd/2-cicd/deploy-cicd.sh
```

## Debugging & Troubleshooting

### Debugging `template.yml.erb`

If you are are updating the template file and don't want to wait for a full deploy cycle to validate the syntax, you can do the following from `cicd/3-app/aiproxy`:

```
erb -T - template.yml.erb > app-template-test.yml
cfn-lint app-template-test.yml
```

This will run cloudformation lint on you template changes and give you a quicker feedback cycle when fixing up syntax.
Just delete app-template-test.yml when you are done.

### Resolving "Error when retrieving credentials" when running deploy commands

Because of some nuances of our AWS SSO integration and tooling, you might need to temporarily change Ruby versions when running scripts that interact with the AWS CLI. You might receive an error like the following.

```
Error when retrieving credentials from custom-process: rbenv: aws-google: command not found

The `aws-google' command exists in these Ruby versions:
  2.7.5
```

If this occurs, you can simply run `rbenv local 2.7.5` or whatever version is suggested (should be the same version used in the code-dot-org/code-dot-org repository) and try running the script again.
