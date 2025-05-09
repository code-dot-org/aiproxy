import os
import json
import boto3
import pytest
from moto import mock_secretsmanager, mock_codebuild
from authorizer.authorizer import handler
from urllib.error import URLError

# Simulated HTTP response for GitHub API
class DummyResponse:
    def __init__(self, data):
        self._data = data
    def read(self):
        return json.dumps(self._data).encode('utf-8')
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN_SECRET_ARN', 'arn:aws:secretsmanager:us-east-1:123456:secret:githtoken')
    monkeypatch.setenv('GitHubOwner', 'code-dot-org')
    monkeypatch.setenv('GitHubRepo', 'aiproxy')
    monkeypatch.setenv('GitHubBranch', 'main')
    monkeypatch.setenv('CODEBUILD_PROJECT', 'pr-build-project')

@mock_secretsmanager
@mock_codebuild
def test_integration_starts_codebuild(monkeypatch):
    # Setup SecretsManager
    sm = boto3.client('secretsmanager', region_name='us-east-1')
    sm.create_secret(Name='githtoken', SecretString=json.dumps({'token':'fakepat'}))

    # Create CodeBuild project
    cb = boto3.client('codebuild', region_name='us-east-1')
    cb.create_project(
        name='pr-build-project',
        source={'type':'CODEPIPELINE'},
        artifacts={'type':'NO_ARTIFACTS'},
        environment={'type':'LINUX_CONTAINER','computeType':'BUILD_GENERAL1_SMALL','image':'aws/codebuild/amazonlinux2-x86_64-standard:5.0'}
    )

    # Stub urlopen to return write permission
    def fake_urlopen(req):
        return DummyResponse({'permission':'maintain'})
    monkeypatch.setattr('authorizer.authorizer.request.urlopen', fake_urlopen)

    # Simulate event
    event = { 'detail': { 'pull_request': { 'base': { 'ref': 'main' }, 'user': { 'login': 'octocat' } } } }
    handler(event, None)

    # List builds to confirm start
    builds = cb.list_builds_for_project(projectName='pr-build-project')['ids']
    assert len(builds) == 1

@mock_secretsmanager
@mock_codebuild
def test_integration_no_start_on_bad_permission(monkeypatch):
    # Setup SecretsManager
    sm = boto3.client('secretsmanager', region_name='us-east-1')
    sm.create_secret(Name='githtoken', SecretString=json.dumps({'token':'fakepat'}))

    # Create CodeBuild project
    cb = boto3.client('codebuild', region_name='us-east-1')
    cb.create_project(
        name='pr-build-project',
        source={'type':'CODEPIPELINE'},
        artifacts={'type':'NO_ARTIFACTS'},
        environment={'type':'LINUX_CONTAINER','computeType':'BUILD_GENERAL1_SMALL','image':'aws/codebuild/amazonlinux2-x86_64-standard:5.0'}
    )

    # Stub urlopen to return read permission
    def fake_urlopen(req):
        return DummyResponse({'permission':'read'})
    monkeypatch.setattr('authorizer.authorizer.request.urlopen', fake_urlopen)

    event = { 'detail': { 'pull_request': { 'base': { 'ref': 'main' }, 'user': { 'login': 'octocat' } } } }
    handler(event, None)

    builds = cb.list_builds_for_project(projectName='pr-build-project')['ids']
    assert len(builds) == 0

@mock_secretsmanager
@mock_codebuild
def test_integration_no_start_on_wrong_branch(monkeypatch):
    # Setup SecretsManager and CodeBuild
    sm = boto3.client('secretsmanager', region_name='us-east-1')
    sm.create_secret(Name='githtoken', SecretString=json.dumps({'token':'fakepat'}))
    cb = boto3.client('codebuild', region_name='us-east-1')
    cb.create_project(
        name='pr-build-project',
        source={'type':'CODEPIPELINE'},
        artifacts={'type':'NO_ARTIFACTS'},
        environment={'type':'LINUX_CONTAINER','computeType':'BUILD_GENERAL1_SMALL','image':'aws/codebuild/amazonlinux2-x86_64-standard:5.0'}
    )

    # Stub urlopen
    monkeypatch.setattr('authorizer.authorizer.request.urlopen', lambda req: DummyResponse({'permission':'admin'}))

    # Wrong branch
    event = { 'detail': { 'pull_request': { 'base': { 'ref': 'feature' }, 'user': { 'login': 'octocat' } } } }
    handler(event, None)

    builds = cb.list_builds_for_project(projectName='pr-build-project')['ids']
    assert len(builds) == 0
