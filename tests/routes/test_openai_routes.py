import os

from unittest.mock import ANY
from types import SimpleNamespace

import pytest
import openai


@pytest.fixture(autouse=True)
def mock_requests(requests_mock):
    """ Ensure no network request goes out during route tests, here.
    """

    yield requests_mock

class TestGetOpenAiModels:
    """ Tests GET to '/openai/models' to list the available models.

    This is a way to test the openai connection and gather capability or access
    of the api key.
    """

    def test_should_return_the_result_given_by_openai(self, mocker, client):
        mocker.patch('openai.Model.list').return_value = SimpleNamespace(data=['data'])
        response = client.get('/openai/models')
        assert response.status_code == 200
        assert response.json == ['data']

    def test_should_set_the_openai_api_key_to_the_environment_var(self, mocker, client, randomstring):
        # Set the key into the environment
        openai_api_key = f"sk-{randomstring(48)}"
        os.environ['OPENAI_API_KEY'] = openai_api_key

        mocker.patch('openai.Model.list').return_value = SimpleNamespace(data=['data'])
        response = client.get('/openai/models')

        assert openai.api_key == openai_api_key


class TestPostOpenAi:
    def test_should_set_the_openai_api_key_to_the_environment_var(self, mocker, client, randomstring):
        # Set the key into the environment
        openai_api_key = f"sk-{randomstring(48)}"
        os.environ['OPENAI_API_KEY'] = openai_api_key

        mocker.patch('openai.ChatCompletion.create').return_value = SimpleNamespace(
            choices=[
              SimpleNamespace(message='foo')
            ]
        )
        response = client.post('/test/openai')

        assert openai.api_key == openai_api_key

    def test_should_use_the_api_key_in_the_environment_var(self, mocker, client, randomstring):
        # Set the key into the environment
        openai_api_key = f"sk-{randomstring(48)}"
        os.environ['OPENAI_API_KEY'] = openai_api_key

        create_mock = mocker.patch('openai.ChatCompletion.create')
        create_mock.return_value = SimpleNamespace(
            choices=[
              SimpleNamespace(message='foo')
            ]
        )
        response = client.post('/test/openai')

        create_mock.assert_called_with(model=ANY, api_key=openai_api_key, messages=ANY)

    def test_should_return_400_on_openai_error(self, mocker, client, randomstring):
        # Set the key into the environment
        openai_api_key = f"sk-{randomstring(48)}"
        os.environ['OPENAI_API_KEY'] = openai_api_key

        create_mock = mocker.patch('openai.ChatCompletion.create')
        create_mock.side_effect = openai.error.InvalidRequestError('', '')

        response = client.post('/test/openai')
        assert response.status_code == 400
