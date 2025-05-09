import os
import json
import pytest
from unittest.mock import patch, MagicMock
from authorizer.authorizer import handler

# Helper to build a minimal PR event
def make_event(login, ref="main"):
    return {
        "detail": {
            "pull_request": {
                "base": {"ref": ref},
                "user": {"login": login}
            }
        }
    }

@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN_SECRET_ARN', 'arn:aws:secretsmanager:us-east-1:123:secret:test')
    monkeypatch.setenv('GitHubOwner', 'code-dot-org')
    monkeypatch.setenv('GitHubRepo', 'aiproxy')
    monkeypatch.setenv('GitHubBranch', 'main')
    monkeypatch.setenv('CODEBUILD_PROJECT', 'pr-build-project')

@patch('authorizer.authorizer.boto3')
@patch('authorizer.authorizer.request.urlopen')
def test_handler_auth_start_build(mock_urlopen, mock_boto3):
    # Mock SecretsManager get_secret_value
    sm = MagicMock()
    sm.get_secret_value.return_value = {'SecretString': json.dumps({'token': 'fake'})}
    # Mock CodeBuild client
    cb = MagicMock()
    # Configure boto3.client side effects
    def client_factory(name, **kwargs):
        if name == 'secretsmanager':
            return sm
        if name == 'codebuild':
            return cb
        raise ValueError(f"Unexpected client {name}")
    mock_boto3.client.side_effect = client_factory

    # Mock GitHub API response: permission = write
    response = MagicMock()
    response.read.return_value = json.dumps({'permission': 'write'}).encode()
    mock_urlopen.return_value.__enter__.return_value = response

    # Invoke handler
    evt = make_event(login='octocat', ref='main')
    handler(evt, None)

    # Assert start_build was called
    cb.start_build.assert_called_once_with(projectName='pr-build-project')

@patch('authorizer.authorizer.boto3')
@patch('authorizer.authorizer.request.urlopen')
def test_handler_no_build_on_wrong_branch(mock_urlopen, mock_boto3):
    # Wrong branch: should not call build
    cb = MagicMock()
    sm = MagicMock()
    mock_boto3.client.side_effect = lambda name, **kwargs: sm if name=='secretsmanager' else cb

    evt = make_event(login='octocat', ref='feature')
    handler(evt, None)
    cb.start_build.assert_not_called()

@patch('authorizer.authorizer.boto3')
@patch('authorizer.authorizer.request.urlopen')
def test_handler_no_build_on_insufficient_permission(mock_urlopen, mock_boto3):
    # Insufficient GitHub permission: read only
    sm = MagicMock()
    sm.get_secret_value.return_value = {'SecretString': json.dumps({'token': 'fake'})}
    cb = MagicMock()
    mock_boto3.client.side_effect = lambda name, **kwargs: sm if name=='secretsmanager' else cb

    # Mock GitHub API permission read
    resp = MagicMock()
    resp.read.return_value = json.dumps({'permission': 'read'}).encode()
    mock_urlopen.return_value.__enter__.return_value = resp

    evt = make_event(login='octocat', ref='main')
    handler(evt, None)
    cb.start_build.assert_not_called()
