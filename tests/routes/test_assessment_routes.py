import openai
import os

from lib.assessment.label import RequestTooLargeError

class TestPostAssessment:
    """ Tests POST to '/assessment' to start an assessment.
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

    def test_should_return_413_on_request_too_large_error(self, mocker, client, randomstring):
        mocker.patch('lib.assessment.assess.validate_and_label').side_effect = RequestTooLargeError('')
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/assessment', query_string={
          "code": randomstring(10),
          "prompt": randomstring(10),
          "rubric": randomstring(10),
          "api-key": randomstring(10),
          "examples": "[]",
          "model": randomstring(10),
          "remove-comments": "1",
          "num-responses": "1",
          "temperature": "0.2",
        }, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})
        assert response.status_code == 413

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

        print(response.data)

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
        print(response.data)
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
