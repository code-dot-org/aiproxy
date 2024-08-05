Here's the issue, we don't grant enough permissions for our application stack to include iam permissions, but it's totally appropriate for that stack to define roles and policies for it's own resources. We do need some protection, and don't want people defining policies in the ap template that allow permission escalation elsewhere, but this is all tracked by git and requires PR's, so I think it's an accpetable risk and we can tighten it up later.

Strategy:

eliminate imports from app template and define things as close to their use as possible

see what breaks

create new global iam roles as needed

GOAL:
- admin still required for setup
- anybody can deploy cicd


RISKS:

Application resources do bad things:
- the ecs task could execute malicious code
  - requires RCE or access to container
  - OR requires malicious code merged to `main`
  - OR requires admin AWS access
  - mitigated by using least-privilege role for task
  - AND mitigated by requiring PR to merge code
- the ecs task could be granted excess permissions
  - requires malicious code merged to `main`
  - OR requires admin AWS access
  - mitigated by requiring PR to merge code
- the app stack could deploy malicious resources
  - requires malicious code merged to `main`
  - OR requires admin AWS access
  - mitigated by least-privilege role for pipeline & cloudformation
  - BUT for convenience we like this role broad :(



NEXT STEPS:
solve the build failure https://us-east-1.console.aws.amazon.com/codesuite/codepipeline/pipelines/aiproxy-iam-refactor-cicd/view?region=us-east-1


An error occurred (AccessDeniedException) when calling the GetAuthorizationToken operation: User: arn:aws:sts::475661607190:assumed-role/aiproxy-iam-refactor-cicd-CodeBuildServiceRole-acpZXNrsWUoW/AWSCodeBuild-72a7bcfe-fee1-480b-8aad-2c1e7bfc9989 is not authorized to perform: ecr:GetAuthorizationToken on resource: * because no identity-based policy allows the ecr:GetAuthorizationToken action
Error: Cannot perform an interactive login from a non TTY device
[Container] 2024/08/03 05:12:48.191449 Command did not exit successfully aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY} exit status 1
[Container] 2024/08/03 05:12:48.197352 Phase complete: PRE_BUILD State: FAILED
[Container] 2024/08/03 05:12:48.197374 Phase context status code: COMMAND_EXECUTION_ERROR Message: Error while executing command: aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}. Reason: exit status 1
