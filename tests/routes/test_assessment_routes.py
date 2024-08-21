import io
import json
import openai
import os
import pytest

from lib.assessment.label import Label, RequestTooLargeError

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


@pytest.fixture
def lesson_11_rubric():
    """ Creates a rubric in CSV format, based on csd3-2023-L11.
    """

    output = """Key Concept,Extensive Evidence,Convincing Evidence,Limited Evidence,No Evidence
Program Development - Program Sequence,You sequenced the program well and and all elements on the screen appear as intended.,Your program may contain a few incorrectly sequenced code resulting in a few elements hidden behind others unintentionally.,"Your program has significant sequencing errors, resulting in many elements unintentionally hidden or overlapping others.","Errors in program sequencing are significant enough to keep the output from resembling the intended scene."
Modularity - Sprites and Sprite Properties,"At least 2 sprites created, each with at least one property updated after creation.","At least 1 sprite created with at least one property updated after creation.","At least 1 sprite created. No properties updated after creation.","No sprites are used in the program."
Position - Elements and the Coordinate System,"At least 2 shapes, 2 sprites, and 2 lines of text are placed correctly on the screen using the coordinate system.","At least 1 shape, 2 sprites, and 1 line of text are placed on the screen using the coordinate system.","A cumulative of at least a total of 3 elements are placed on the screen using the coordinate system (e.g 2 sprites & 1 line of text or 1 sprite, 1 shape, & 1 line of text)","No elements (shapes, sprites, or text) are placed on the screen using the coordinate system."
"""
    yield output

@pytest.fixture
def lesson_11_request_data(lesson_11_rubric):
    rubric = lesson_11_rubric
    request_data = {
        "code": 'test-code',
        "prompt": 'test-prompt',
        "rubric": rubric,
        "api-key": 'test-api-key',
        "examples": "[]",
        "model": 'bedrock.anthropic.claude-3-5-sonnet-20240620-v1:0',
        "remove-comments": "1",
        "num-responses": "2",
        "temperature": "0.2",
    }
    yield request_data

@pytest.fixture
def lesson_11_response_data():
    yield [
        {
            "Key Concept": "Program Development - Program Sequence",
            "Observations": "The program appears to be well-sequenced, with background set first, sprites created and positioned, sprite properties set, sprites drawn, and text added last.",
            "Evidence": "Lines 1-9: The program sets the background, creates and positions sprites, sets their properties, and draws them in the correct order.\n`background(\"black\");\nvar animalhead_duck1 = createSprite(352, 200);\nvar animalhead_frog_1 = createSprite(46, 200);\nanimalhead_duck1.setAnimation(\"animalhead_duck1\");\nanimalhead_frog_1.setAnimation(\"animalhead_frog_1\");\nanimalhead_frog_1.scale = 0.4;\nanimalhead_duck1.scale = 0.4;\ndrawSprites();`\n\nLines 10-12: Text is added after sprites are drawn.\n`textSize(20);\nfill(\"white\");\ntext(\"Fortnite\", 175, 200);`",
            "Reason": "The program demonstrates a logical sequence of operations. The background is set first, then sprites are created and their properties are set. The drawSprites() function is called to render the sprites, and finally, the text is added. This sequence ensures that all elements appear as intended, with no overlapping or hiding issues. Decision: Extensive Evidence",
            "Grade": "Extensive Evidence"
        },
        {
            "Key Concept": "Modularity - Sprites and Sprite Properties",
            "Observations": "The program creates two sprites and updates properties for both after creation.",
            "Evidence": "Lines 2-3: Two sprites are created.\n`var animalhead_duck1 = createSprite(352, 200);\nvar animalhead_frog_1 = createSprite(46, 200);`\n\nLines 4-7: Properties of both sprites are updated after creation.\n`animalhead_duck1.setAnimation(\"animalhead_duck1\");\nanimalhead_frog_1.setAnimation(\"animalhead_frog_1\");\nanimalhead_frog_1.scale = 0.4;\nanimalhead_duck1.scale = 0.4;`",
            "Reason": "The program creates two distinct sprites: animalhead_duck1 and animalhead_frog_1. For both sprites, it sets the animation and scale properties after creation. This meets the criteria for Extensive Evidence as there are at least 2 sprites created, each with at least one property updated after creation. Decision: Extensive Evidence",
            "Grade": "Extensive Evidence"
        },
        {
            "Key Concept": "Position - Elements and the Coordinate System",
            "Observations": "The program places two sprites and one line of text using the coordinate system. No shapes are created.",
            "Evidence": "Lines 2-3: Two sprites are positioned using coordinates.\n`var animalhead_duck1 = createSprite(352, 200);\nvar animalhead_frog_1 = createSprite(46, 200);`\n\nLine 12: One line of text is positioned using coordinates.\n`text(\"Fortnite\", 175, 200);`",
            "Reason": "The program demonstrates the use of the coordinate system to place elements on the screen. It positions two sprites (animalhead_duck1 and animalhead_frog_1) and one line of text (\"Fortnite\") using x and y coordinates. However, it does not create any shapes using functions like rect, ellipse, circle, quad, or triangle. According to the rubric, for Convincing Evidence, we need at least 1 shape, 2 sprites, and 1 line of text. While the program meets the criteria for sprites and text, it lacks any shapes. Therefore, it falls under the Limited Evidence category. Decision: Limited Evidence",
            "Grade": "Limited Evidence"
        }
    ]

def get_bedrock_claude_response_body(response_data):
    response_json = json.dumps(response_data)
    body_data = {
        "id": "msg_bdrk_01234567890abcdefghijklm",
        "type": "message",
        "role": "assistant",
        "model": "claude-3-5-sonnet-20240620",
        "content": [
            {
                "type": "text",
                "text": response_json
            }
        ],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {
            "input_tokens": 1397,
            "output_tokens": 972
        }
    }
    return json.dumps(body_data, indent=2)

@pytest.fixture
def lesson_11_response_body(lesson_11_response_data):
    yield get_bedrock_claude_response_body(lesson_11_response_data)

@pytest.fixture
def lesson_11_response_body_mismatched(lesson_11_response_data):
    response_data = lesson_11_response_data
    response_data[0]["Key Concept"] = "Bogus Key Concept"
    yield get_bedrock_claude_response_body(response_data)

class TestIntegrationPostAssessment:
    """ Tests POST to '/assessment' to start an assessment.

    This is an integration test because it tests all the way to the AI API request, rather than just checking what gets passed to Label.
    """

    def test_succeeds_when_bedrock_returns_valid_response(self, mocker, client, lesson_11_request_data, lesson_11_response_body):
        # stub the bedrock response
        response_body = lesson_11_response_body
        invoke_model_response = {'ResponseMetadata': {'HTTPStatusCode': 200}, 'body': io.StringIO(response_body)}
        class mock_bedrock_client:
            def invoke_model(body, modelId, accept, contentType):
                assert modelId == 'anthropic.claude-3-5-sonnet-20240620-v1:0'
                assert accept == 'application/json'
                assert contentType == 'application/json'
                return invoke_model_response
        get_bedrock_client_mock = mocker.patch.object(
            Label,
            'get_bedrock_client',
            return_value=mock_bedrock_client
        )

        # send the flask request
        request_data = lesson_11_request_data
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/assessment', query_string=request_data, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})

        assert response.status_code == 200

        # check that get_bedrock_client_mock was called
        get_bedrock_client_mock.assert_called_once()

    def test_returns_4xx_when_bedrock_returns_mismatched_key_concept(self, mocker, client, lesson_11_request_data, lesson_11_response_body_mismatched):
        # stub the bedrock response
        response_body = lesson_11_response_body_mismatched
        invoke_model_response = {'ResponseMetadata': {'HTTPStatusCode': 200}, 'body': io.StringIO(response_body)}
        class mock_bedrock_client:
            def invoke_model(body, modelId, accept, contentType):
                assert modelId == 'anthropic.claude-3-5-sonnet-20240620-v1:0'
                assert accept == 'application/json'
                assert contentType == 'application/json'
                return invoke_model_response
        get_bedrock_client_mock = mocker.patch.object(
            Label,
            'get_bedrock_client',
            return_value=mock_bedrock_client
        )

        # send the flask request
        request_data = lesson_11_request_data
        os.environ['AIPROXY_API_KEY'] = 'test_key'
        response = client.post('/assessment', query_string=request_data, headers={"Content-type": "application/x-www-form-urlencoded", "Authorization": "test_key"})

        assert response.status_code == 400

        # check that get_bedrock_client_mock was called
        get_bedrock_client_mock.assert_called_once()


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
