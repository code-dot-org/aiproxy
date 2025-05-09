import os
import json
import boto3
from urllib import request

# Lambda handler for PR authorizer
# Fetches GitHub token from Secrets Manager, checks PR author permission,
# and starts CodeBuild if writer/maintainer/admin.

def handler(event, context):
    # Load env vars
    secret_arn = os.environ['GITHUB_TOKEN_SECRET_ARN']
    owner = os.environ['GitHubOwner']
    repo = os.environ['GitHubRepo']
    branch = os.environ['GitHubBranch']
    project = os.environ['CODEBUILD_PROJECT']

    # Fetch GitHub PAT from Secrets Manager
    sm = boto3.client('secretsmanager')
    secret = sm.get_secret_value(SecretId=secret_arn)
    token = json.loads(secret['SecretString'])['token']

    # Extract PR event details
    detail = event.get('detail', {})
    pr = detail.get('pull_request', {})

    # Only handle events on the configured branch
    if pr.get('base', {}).get('ref') != branch:
        return

    login = pr.get('user', {}).get('login')
    if not login:
        return

    # Build GitHub API URL for collaborator permission
    url = f"https://api.github.com/repos/{owner}/{repo}/collaborators/{login}/permission"
    req = request.Request(
        url,
        headers={
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    )
    # Call GitHub
    with request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())

    # Only allow write/maintain/admin
    if data.get('permission') in ['write', 'maintain', 'admin']:
        cb = boto3.client('codebuild')
        cb.start_build(projectName=project)
