import json
import io
import openai
import os

from lib.assessment.label import Label, RequestTooLargeError

class TestPostAssessment:
    """ Tests POST to '/assessment' to start an assessment.

    These tests attempt to cover the /assessment route end-to-end, stubbing out only the bedrock client.
    """

    def test_succeeds_when_bedrock_returns_valid_response(self, mocker, client, stub_code, stub_prompt, lesson_11_rubric, claude_model, lesson_11_claude_request_data, lesson_11_claude_response_body):
        # stub the bedrock response
        response_body = lesson_11_claude_response_body
        invoke_model_response = {'ResponseMetadata': {'HTTPStatusCode': 200}, 'body': io.StringIO(response_body)}
        class mock_bedrock_client:
            def invoke_model(body, modelId, accept, contentType):
                assert stub_code in body
                assert stub_prompt in body
                rubric_headers = lesson_11_rubric.split('\n')[0]
                assert rubric_headers in body
                assert modelId == claude_model
                assert accept == 'application/json'
                assert contentType == 'application/json'
                return invoke_model_response
        get_bedrock_client_mock = mocker.patch.object(
            Label,
            'get_bedrock_client',
            return_value=mock_bedrock_client
        )

        # send the flask request
        request_data = lesson_11_claude_request_data
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/assessment', query_string=request_data, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})

        assert response.status_code == 200

        # validate response data
        response_data = response.json
        assert response_data['metadata']['agent'] == 'anthropic'
        learning_goal = response_data['data'][2]
        assert learning_goal['Key Concept'] == "Position - Elements and the Coordinate System"
        assert learning_goal['Label'] == "Limited Evidence"

        get_bedrock_client_mock.assert_called_once()

    def test_returns_4xx_when_bedrock_returns_mismatched_key_concept(self, mocker, client, lesson_11_claude_request_data, lesson_11_claude_response_body_mismatched):
        # stub the bedrock response
        response_body = lesson_11_claude_response_body_mismatched
        invoke_model_response = {'ResponseMetadata': {'HTTPStatusCode': 200}, 'body': io.StringIO(response_body)}
        class mock_bedrock_client:
            def invoke_model(body, modelId, accept, contentType):
                return invoke_model_response
        get_bedrock_client_mock = mocker.patch.object(
            Label,
            'get_bedrock_client',
            return_value=mock_bedrock_client
        )

        # send the flask request
        request_data = lesson_11_claude_request_data
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/assessment', query_string=request_data, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})

        assert response.status_code == 400

        # check that get_bedrock_client_mock was called
        get_bedrock_client_mock.assert_called_once()


    def test_should_return_413_on_request_too_large_error(self, mocker, client, randomstring, lesson_11_rubric, bedrock_claude_model, lesson_11_claude_response_body_too_large):
        # stub the bedrock response
        response_body = lesson_11_claude_response_body_too_large
        invoke_model_response = {'ResponseMetadata': {'HTTPStatusCode': 200}, 'body': io.StringIO(response_body)}
        class mock_bedrock_client:
            def invoke_model(body, modelId, accept, contentType):
                return invoke_model_response
        get_bedrock_client_mock = mocker.patch.object(
            Label,
            'get_bedrock_client',
            return_value=mock_bedrock_client
        )

        # send the flask request
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/assessment', query_string={
          "code": randomstring(10),
          "prompt": randomstring(10),
          "rubric": lesson_11_rubric,
          "api-key": randomstring(10),
          "examples": "[]",
          "model": bedrock_claude_model,
          "remove-comments": "1",
          "num-responses": "1",
          "temperature": "0.2",
        }, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})
        assert response.status_code == 413

        get_bedrock_client_mock.assert_called_once()

    def test_succeeds_when_openai_returns_valid_response(self, requests_mock, client, lesson_11_openai_request_data, lesson_11_openai_response_data):
        # stub the openai response
        requests_mock.post(
            'https://api.openai.com/v1/chat/completions',
            json=lesson_11_openai_response_data
        )

        # send the flask request
        request_data = lesson_11_openai_request_data
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/assessment', query_string=request_data, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})

        assert response.status_code == 200

    def test_uses_code_feature_extractor_when_requested(self, client, mocker, lesson_11_claude_request_data, lesson_11_claude_response_body):
        # stub the bedrock response
        response_body = lesson_11_claude_response_body
        invoke_model_response = {'ResponseMetadata': {'HTTPStatusCode': 200}, 'body': io.StringIO(response_body)}
        class mock_bedrock_client:
            def invoke_model(body, modelId, accept, contentType):
                assert accept == 'application/json'
                assert contentType == 'application/json'
                return invoke_model_response
        get_bedrock_client_mock = mocker.patch.object(
            Label,
            'get_bedrock_client',
            return_value=mock_bedrock_client
        )

        # send the flask request
        request_data = lesson_11_claude_request_data
        request_data['code-feature-extractor'] = ["Position - Elements and the Coordinate System"],
        request_data['lesson'] = 'csd3-2023-L11'
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/assessment', query_string=request_data, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})

        assert response.status_code == 200

        # validate response data
        response_data = response.json
        assert response_data['metadata']['agent'] == 'anthropic, code feature extractor'
        learning_goal = response_data['data'][2]
        assert learning_goal['Key Concept'] == "Position - Elements and the Coordinate System"
        # LLM value overridden by CFE
        assert learning_goal['Label'] == "No Evidence"

        get_bedrock_client_mock.assert_called_once()


class TestPostAssessmentUnitTests:
    """ Tests POST to '/assessment' to start an assessment.

    These tests stub out the Label class to test the API endpoint in isolation.
    """

    def test_should_return_400_when_no_code(self, client, randomstring):
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/assessment', query_string={
            "prompt": randomstring(10),
            "rubric": randomstring(10),
            "api-key": randomstring(10),
            "examples": "[]",
            "model": randomstring(10),
            "remove-comments": "1",
            "num-responses": "1",
            "temperature": "0.2",
        }, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})
        assert response.status_code == 400

    def test_should_return_400_when_no_prompt(self, client, randomstring):
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/assessment', query_string={
            "code": randomstring(10),
            "rubric": randomstring(10),
            "api-key": randomstring(10),
            "examples": "[]",
            "model": randomstring(10),
            "remove-comments": "1",
            "num-responses": "1",
            "temperature": "0.2",
        }, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})
        assert response.status_code == 400

    def test_should_return_400_when_no_rubric(self, client, randomstring):
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/assessment', query_string={
            "code": randomstring(10),
            "prompt": randomstring(10),
            "api-key": randomstring(10),
            "examples": "[]",
            "model": randomstring(10),
            "remove-comments": "1",
            "num-responses": "1",
            "temperature": "0.2",
        }, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})
        assert response.status_code == 400

    def test_should_return_400_when_passing_not_a_number_to_num_responses(self, client, randomstring):
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/assessment', query_string={
            "code": randomstring(10),
            "prompt": randomstring(10),
            "rubric": randomstring(10),
            "api-key": randomstring(10),
            "examples": "[]",
            "model": randomstring(10),
            "remove-comments": "1",
            "num-responses": "x",
            "temperature": "0.2",
        }, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})
        assert response.status_code == 400

    def test_should_return_400_when_passing_not_a_number_to_temperature(self, client, randomstring):
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/assessment', query_string={
            "code": randomstring(10),
            "prompt": randomstring(10),
            "rubric": randomstring(10),
            "api-key": randomstring(10),
            "examples": "[]",
            "model": randomstring(10),
            "remove-comments": "1",
            "num-responses": "2",
            "temperature": "x",
        }, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})
        assert response.status_code == 400

    def test_should_return_400_when_the_label_function_does_not_return_data(self, mocker, client, randomstring):
        label_mock = mocker.patch('lib.assessment.assess.validate_and_label')
        label_mock.return_value = []

        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/assessment', query_string={
          "code": randomstring(10),
          "prompt": randomstring(10),
          "rubric": randomstring(10),
          "api-key": randomstring(10),
          "examples": "[]",
          "model": randomstring(10),
          "remove-comments": "1",
          "num-responses": "2",
          "temperature": "0.2",
        }, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})

        assert response.status_code == 400

    def test_should_return_400_when_the_label_function_does_not_return_the_right_structure(self, mocker, client, randomstring):
        label_mock = mocker.patch('lib.assessment.assess.validate_and_label')
        label_mock.return_value = {
            'metadata': {},
            'data': {}
        }

        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/assessment', query_string={
          "code": randomstring(10),
          "prompt": randomstring(10),
          "rubric": randomstring(10),
          "api-key": randomstring(10),
          "examples": "[]",
          "model": randomstring(10),
          "remove-comments": "1",
          "num-responses": "2",
          "temperature": "x",
        }, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})

        assert response.status_code == 400

    def test_should_pass_arguments_to_label_function(self, mocker, client, randomstring):
        response_type = 'json'
        label_mock = mocker.patch('lib.assessment.assess.validate_and_label')
        data = {
          "code": randomstring(10),
          "prompt": randomstring(10),
          "rubric": randomstring(10),
          "api-key": randomstring(10),
          "examples": "[]",
          "model": randomstring(10),
          "remove-comments": "1",
          "num-responses": "2",
          "temperature": "0.2", 
          "response-type": response_type,
        }

        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/assessment', query_string=data, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})

        label_mock.assert_called_with(
            code=data["code"],
            prompt=data["prompt"],
            rubric=data["rubric"],
            examples=[],
            api_key=data["api-key"],
            llm_model=data["model"],
            remove_comments=True,
            num_responses=2,
            temperature=0.2,
            response_type=response_type,
            code_feature_extractor=None,
            lesson=None
        )

    def test_should_return_the_result_from_label_function_when_valid(self, mocker, client, randomstring):
        label_mock = mocker.patch('lib.assessment.assess.validate_and_label')
        label_mock.return_value = {
            'metadata': {},
            'data': [
                {
                    'Key Concept': randomstring(10),
                    'Observations': 'foo',
                    'Label': 'No Evidence',
                    'Reason': 'bar'
                }
            ]
        }
        data = {
          "code": randomstring(10),
          "prompt": randomstring(10),
          "rubric": randomstring(10),
          "api-key": randomstring(10),
          "examples": "[]",
          "model": randomstring(10),
          "remove-comments": "1",
          "num-responses": "2",
          "temperature": "0.2",
        }

        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/assessment', query_string=data, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})

        assert response.status_code == 200
        assert response.json == label_mock.return_value


class TestPostTestAssessment:
    """ Tests POST to '/test/assessment' to start an assessment.
    """

    def test_should_return_400_on_openai_error(self, mocker, client, randomstring):
        mocker.patch('lib.assessment.assess.validate_and_label').side_effect = openai.error.InvalidRequestError('', '')
        mock_open = mocker.mock_open(read_data='file data')
        mock_file = mocker.patch('builtins.open', mock_open)
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/test/assessment', query_string={
          "code": randomstring(10),
          "prompt": randomstring(10),
          "rubric": randomstring(10),
          "api-key": randomstring(10),
          "model": randomstring(10),
          "remove-comments": "1",
          "num-responses": "1",
          "temperature": "0.2",
        }, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})
        assert response.status_code == 400

    def test_should_return_400_when_passing_not_a_number_to_num_responses(self, mocker, client, randomstring):
        mock_open = mocker.mock_open(read_data='file data')
        mock_file = mocker.patch('builtins.open', mock_open)
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/test/assessment', query_string={
          "code": randomstring(10),
          "prompt": randomstring(10),
          "rubric": randomstring(10),
          "api-key": randomstring(10),
          "model": randomstring(10),
          "remove-comments": "1",
          "num-responses": "x",
          "temperature": "0.2",
        }, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})
        assert response.status_code == 400

    def test_should_return_400_when_passing_not_a_number_to_temperature(self, mocker, client, randomstring):
        mock_open = mocker.mock_open(read_data='file data')
        mock_file = mocker.patch('builtins.open', mock_open)
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/test/assessment', query_string={
          "code": randomstring(10),
          "prompt": randomstring(10),
          "rubric": randomstring(10),
          "api-key": randomstring(10),
          "model": randomstring(10),
          "remove-comments": "1",
          "num-responses": "2",
          "temperature": "x",
        }, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})
        assert response.status_code == 400

    def test_should_return_400_when_the_label_function_does_not_return_data(self, mocker, client, randomstring):
        label_mock = mocker.patch('lib.assessment.assess.validate_and_label')
        mock_open = mocker.mock_open(read_data='file data')
        mock_file = mocker.patch('builtins.open', mock_open)
        label_mock.return_value = []
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/test/assessment', query_string={
          "code": randomstring(10),
          "prompt": randomstring(10),
          "rubric": randomstring(10),
          "api-key": randomstring(10),
          "model": randomstring(10),
          "remove-comments": "1",
          "num-responses": "2",
          "temperature": "0.2",
        }, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})

        assert response.status_code == 400

    def test_should_return_400_when_the_label_function_does_not_return_the_right_structure(self, mocker, client, randomstring):
        label_mock = mocker.patch('lib.assessment.assess.validate_and_label')
        mock_open = mocker.mock_open(read_data='file data')
        mock_file = mocker.patch('builtins.open', mock_open)
        label_mock.return_value = {
            'metadata': {},
            'data': {}
        }
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/test/assessment', query_string={
          "code": randomstring(10),
          "prompt": randomstring(10),
          "rubric": randomstring(10),
          "api-key": randomstring(10),
          "model": randomstring(10),
          "remove-comments": "1",
          "num-responses": "2",
          "temperature": "x",
        }, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})

        assert response.status_code == 400

    def test_should_return_the_result_from_label_function_when_valid(self, mocker, client, randomstring):
        label_mock = mocker.patch('lib.assessment.assess.validate_and_label')
        mock_open = mocker.mock_open(read_data='file data')
        mock_file = mocker.patch('builtins.open', mock_open)
        label_mock.return_value = {
            'metadata': {},
            'data': [
                {
                    'Key Concept': randomstring(10),
                    'Observations': 'foo',
                    'Label': 'No Evidence',
                    'Reason': 'bar'
                }
            ]
        }
        data = {
          "code": randomstring(10),
          "prompt": randomstring(10),
          "rubric": randomstring(10),
          "api-key": randomstring(10),
          "model": randomstring(10),
          "remove-comments": "1",
          "num-responses": "2",
          "temperature": "0.2",
        }
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/test/assessment', query_string=data, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})

        assert response.status_code == 200
        assert response.json == label_mock.return_value


class TestPostBlankAssessment:
    """ Tests POST to '/test/assessment/blank' to start an assessment.
    """

    def test_should_return_400_on_openai_error(self, mocker, client, randomstring):
        mocker.patch('lib.assessment.assess.validate_and_label').side_effect = openai.error.InvalidRequestError('', '')
        mock_open = mocker.mock_open(read_data='file data')
        mock_file = mocker.patch('builtins.open', mock_open)
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/test/assessment/blank', query_string={
          "prompt": randomstring(10),
          "rubric": randomstring(10),
          "api-key": randomstring(10),
          "model": randomstring(10),
          "remove-comments": "1",
          "num-responses": "1",
          "temperature": "0.2",
        }, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})
        assert response.status_code == 400

    def test_should_return_400_when_passing_not_a_number_to_num_responses(self, mocker, client, randomstring):
        mock_open = mocker.mock_open(read_data='file data')
        mock_file = mocker.patch('builtins.open', mock_open)
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/test/assessment/blank', query_string={
          "prompt": randomstring(10),
          "rubric": randomstring(10),
          "api-key": randomstring(10),
          "model": randomstring(10),
          "remove-comments": "1",
          "num-responses": "x",
          "temperature": "0.2",
        }, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})
        assert response.status_code == 400

    def test_should_return_400_when_passing_not_a_number_to_temperature(self, mocker, client, randomstring):
        mock_open = mocker.mock_open(read_data='file data')
        mock_file = mocker.patch('builtins.open', mock_open)
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/test/assessment/blank', query_string={
          "prompt": randomstring(10),
          "rubric": randomstring(10),
          "api-key": randomstring(10),
          "model": randomstring(10),
          "remove-comments": "1",
          "num-responses": "2",
          "temperature": "x",
        }, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})
        assert response.status_code == 400

    def test_should_return_400_when_the_label_function_does_not_return_data(self, mocker, client, randomstring):
        label_mock = mocker.patch('lib.assessment.assess.validate_and_label')
        mock_open = mocker.mock_open(read_data='file data')
        mock_file = mocker.patch('builtins.open', mock_open)
        label_mock.return_value = []
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/test/assessment/blank', query_string={
          "prompt": randomstring(10),
          "rubric": randomstring(10),
          "api-key": randomstring(10),
          "model": randomstring(10),
          "remove-comments": "1",
          "num-responses": "2",
          "temperature": "0.2",
        }, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})

        assert response.status_code == 400

    def test_should_return_400_when_the_label_function_does_not_return_the_right_structure(self, mocker, client, randomstring):
        label_mock = mocker.patch('lib.assessment.assess.validate_and_label')
        mock_open = mocker.mock_open(read_data='file data')
        mock_file = mocker.patch('builtins.open', mock_open)
        label_mock.return_value = {
            'metadata': {},
            'data': {}
        }
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/test/assessment/blank', query_string={
          "prompt": randomstring(10),
          "rubric": randomstring(10),
          "api-key": randomstring(10),
          "model": randomstring(10),
          "remove-comments": "1",
          "num-responses": "2",
          "temperature": "x",
        }, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})

        assert response.status_code == 400

    def test_should_pass_arguments_including_blank_code_to_label_function(self, mocker, client, randomstring):
        label_mock = mocker.patch('lib.assessment.assess.validate_and_label')
        mock_open = mocker.mock_open(read_data='file data')
        mock_file = mocker.patch('builtins.open', mock_open)
        data = {
          "code": "",
          "prompt": randomstring(10),
          "rubric": randomstring(10),
          "api-key": randomstring(10),
          "model": randomstring(10),
          "remove-comments": "1",
          "num-responses": "2",
          "temperature": "0.2",
        }
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/test/assessment/blank', query_string=data, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})
        label_mock.assert_called_with(
            code='',
            prompt='file data',
            rubric='file data',
            api_key=data["api-key"],
            llm_model=data["model"],
            remove_comments=True,
            num_responses=2,
            temperature=0.2
        )

    def test_should_return_the_result_from_label_function_when_valid(self, mocker, client, randomstring):
        label_mock = mocker.patch('lib.assessment.assess.validate_and_label')
        mock_open = mocker.mock_open(read_data='file data')
        mock_file = mocker.patch('builtins.open', mock_open)
        label_mock.return_value = {
            'metadata': {},
            'data': [
                {
                    'Key Concept': randomstring(10),
                    'Observations': 'foo',
                    'Label': 'No Evidence',
                    'Reason': 'bar'
                }
            ]
        }
        data = {
          "prompt": randomstring(10),
          "rubric": randomstring(10),
          "api-key": randomstring(10),
          "model": randomstring(10),
          "remove-comments": "1",
          "num-responses": "2",
          "temperature": "0.2"
        }
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/test/assessment/blank', query_string=data, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})
        assert response.status_code == 200
        assert response.json == label_mock.return_value
