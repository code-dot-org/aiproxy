import os
import csv
import json
import logging
import random

from io import StringIO

import requests
import pytest

from lib.assessment.label import Label, InvalidResponseError


@pytest.fixture
def label():
    """ Creates a Label() instance for any test that has a 'label' parameter.
    """
    yield Label()


class TestRemoveJsComments:
    def test_remove_js_comments(self, label):
        # We combine a lot here... quotes escaped... comments in strings are ok, etc
        result = label.remove_js_comments("""
    function example() {
        var str0 = "\\"// Foo";
        var str1 = "This is a string w\\"ith /* not a comment */ inside.";
        var str2 = 'Another string with // not a comment.';
        // This is a real single-line comment
        /* This is a
           real multi-line comment */
        return str0 + str1 + str2;
    }
    """)

        assert result == """
    function example() {
        var str0 = "\\"// Foo";
        var str1 = "This is a string w\\"ith /* not a comment */ inside.";
        var str2 = 'Another string with // not a comment.';
        
        
        return str0 + str1 + str2;
    }
    """

class TestSanitizeCode:
    def test_should_call_remove_js_comments_if_wanted(self, mocker, label, code):
        remove_js_comments_mock = mocker.patch.object(Label, 'remove_js_comments')

        label.sanitize_code(code, remove_comments=True)

        remove_js_comments_mock.assert_called_with(code)

    def test_should_not_call_remove_js_comments_if_not_wanted(self, mocker, label, code):
        remove_js_comments_mock = mocker.patch.object(Label, 'remove_js_comments')

        label.sanitize_code(code, remove_comments=False)

        remove_js_comments_mock.assert_not_called()


class TestBlankCodeDetection:
    def test_should_return_no_evidence_on_blank_project(self, label, rubric, student_id, examples):
        result = label.test_for_blank_code(
            rubric, "", student_id
        )

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        # It should have a metadata and data section
        assert 'metadata' in result
        assert 'data' in result

        # It should return just as many labeled rows as there are in the rubric
        assert len(result['data']) == len(parsed_rubric)

        # It should return 'No Evidence' in every row
        assert all(x['Label'] == 'No Evidence' for x in result['data'])

        # It should match the concepts given in the rubric
        assert set(x['Key Concept'] for x in parsed_rubric) == set(x['Key Concept'] for x in result['data'])


class TestCodeFeatureExtractor:
    def test_should_return_assessed_learning_goal_when_cfe_flag_set(self, label, code):
        
        with open('tests/data/cfe_params.json', 'r') as f:
            params = json.load(f)

        with open('tests/data/cfe_rubric.csv', 'r') as f:
            rubric = f.read()
        
        result = label.cfe_label_student_work(
            rubric, code, params["code-feature-extractor"]
        )
        print(result)

        # It should have a metadata and data section
        assert 'metadata' in result
        assert 'data' in result

        # It should return just as many labeled rows as the number of learning goals listed in the code-feature-extractor param
        assert len(result['data']) == len(params["code-feature-extractor"])

        assert all(x['Label'] == 'No Evidence' for x in result['data'])


class TestComputeMessages:
    def test_should_structure_messages_based_on_input(self, label, prompt, rubric, code):
        result = label.compute_messages(prompt, rubric, code, examples=[])

        assert len(result) == 2
        assert 'role' in result[0]
        assert result[0]['role'] == 'system'
        assert 'content' in result[0]
        assert prompt in result[0]['content']
        assert rubric in result[0]['content']
        assert 'role' in result[1]
        assert result[1]['role'] == 'user'
        assert code in result[1]['content']

    def test_should_add_examples(self, label, prompt, rubric, code, examples):
        example_set = examples(rubric)
        result = label.compute_messages(prompt, rubric, code, examples=example_set)

        # The result should be the system and user message plus two per example
        assert len(result) == (2 + (len(example_set) * 2))

        # The examples should be between the system prompt and user code
        for i in range(0, len(example_set)):
            user_message = result[(i * 2) + 1]

            assert 'role' in user_message
            assert user_message['role'] == 'user'
            assert example_set[i][0] in user_message['content']

            assistant_message = result[(i * 2) + 2]
            assert 'role' in assistant_message
            assert assistant_message['role'] == 'assistant'
            assert example_set[i][1] in assistant_message['content']


class TestGetResponseDataIfValid:
    def test_should_return_none_if_the_response_is_blank(self, label, rubric, student_id):
        result = label.get_response_data_if_valid("", rubric, student_id)

        assert result is None

    def test_should_log_the_choice_index_if_the_response_is_blank(self, caplog, label, rubric, student_id):
        index = random.randint(0, 5)
        label.get_response_data_if_valid("", rubric, student_id, choice_index=index)

        assert any(filter(lambda x: (f'Choice {index}' in x.message) and x.levelno == logging.ERROR, caplog.records))

    @pytest.mark.parametrize("output_type", ['tsv', 'csv', 'markdown'])
    def test_should_work_for_different_output_types(self, label, rubric, student_id, openai_gpt_response, output_type):
        # We will generate fake openai gpt responses where it gave us the labeled
        # rubrics in CSV or markdown (even though we told it NOT TO grr)
        ai_response = openai_gpt_response(rubric, num_responses=1, output_type=output_type)
        response = ai_response['choices'][0]['message']['content']

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        # It should parse them out to get the same number of rows as the rubric
        result = label.get_response_data_if_valid(response, rubric, student_id)
        assert result is not None
        assert len(result) == len(parsed_rubric)

    def test_should_work_for_json_response_type(self, label, rubric, student_id, openai_gpt_response, output_type='json'):
        ai_response = openai_gpt_response(rubric, num_responses=1, output_type=output_type)
        response = ai_response['choices'][0]['message']['content']

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        # It should parse them out to get the same number of rows as the rubric
        result = label.get_response_data_if_valid(response, rubric, student_id, response_type='json')
        assert result is not None
        assert len(result) == len(parsed_rubric)


    @pytest.mark.parametrize("output_type", ['tsv', 'csv', 'markdown'])
    def test_should_work_for_different_output_types_with_leading_text(self, label, rubric, student_id, openai_gpt_response, output_type):
        # We will generate fake openai gpt responses where it gave us the labeled
        # rubrics in CSV or markdown (even though we told it NOT TO grr)
        ai_response = openai_gpt_response(rubric, num_responses=1, output_type=output_type)
        response = "Bogus Weasel lines\n" + ai_response['choices'][0]['message']['content']

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        # It should parse them out to get the same number of rows as the rubric
        result = label.get_response_data_if_valid(response, rubric, student_id)
        assert result is not None
        assert len(result) == len(parsed_rubric)

    def test_should_work_for_tsv_output_where_it_escapes_tabs(self, label, rubric, student_id, openai_gpt_response):
        # ChatGPT will sometimes give you tsv (yay!) but escape the tabs for some reason (boo!)
        ai_response = openai_gpt_response(rubric, num_responses=1, output_type='tsv')
        response = ai_response['choices'][0]['message']['content'].replace('\t', '\\t')

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        # It should parse them out to get the same number of rows as the rubric
        result = label.get_response_data_if_valid(response, rubric, student_id)
        assert result is not None
        assert len(result) == len(parsed_rubric)

    def test_should_strip_server_response(self, label, rubric, student_id, openai_gpt_response):
        # We will generate fake openai gpt responses where it gave us the labeled
        # rubrics in CSV or markdown (even though we told it NOT TO grr)
        ai_response = openai_gpt_response(rubric, num_responses=1, output_type='tsv')
        response = ai_response['choices'][0]['message']['content']

        # We can invalidate the response
        response = response.replace("Observations", " Observations ")

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        result = label.get_response_data_if_valid(response, rubric, student_id)
        assert result is not None
        assert len(result) == len(parsed_rubric)

    def test_should_work_when_there_are_weird_entries(self, mocker, label, rubric, student_id, openai_gpt_response):
        # We will occasionally get entries that place lines within the returned data
        # This is true with markdown responses that place a set of '-----' lines
        ai_response = openai_gpt_response(rubric, num_responses=1, output_type='tsv')
        response = ai_response['choices'][0]['message']['content']

        # Slide a nonsense line within the response (2nd to last entry)
        lines = response.splitlines()
        lines.append(lines[-1])
        lines[-2] = "--------\t---------\t--------\t---------"
        response = '\n'.join(lines)

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        # Should be fine
        result = label.get_response_data_if_valid(response, rubric, student_id)
        assert result is not None
        assert len(result) == len(parsed_rubric)

    def test_should_work_when_there_are_multiple_weird_entries(self, mocker, label, rubric, student_id, openai_gpt_response):
        # We will occasionally get entries that place lines within the returned data
        # This is true with markdown responses that place a set of '-----' lines
        ai_response = openai_gpt_response(rubric, num_responses=1, output_type='tsv')
        response = ai_response['choices'][0]['message']['content']

        # Slide a nonsense line within the response (2nd to last entry)
        lines = response.splitlines()
        delimiter = "\n--------\t---------\t--------\t---------\n"
        response = delimiter.join(lines)

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        # Should be fine
        result = label.get_response_data_if_valid(response, rubric, student_id)
        assert result is not None
        assert len(result) == len(parsed_rubric)

    def test_should_return_none_when_there_is_no_key_concept(self, mocker, label, rubric, student_id, openai_gpt_response):
        # We will generate fake openai gpt responses where it gave us the labeled
        # rubrics in CSV or markdown (even though we told it NOT TO grr)
        ai_response = openai_gpt_response(rubric, num_responses=1, output_type='tsv')
        response = ai_response['choices'][0]['message']['content']

        # We can invalidate the response
        response = response.replace("Key Concept", "Bogus Weasel")

        result = label.get_response_data_if_valid(response, rubric, student_id)
        assert result is None

    def test_should_return_none_when_the_columns_are_invalid(self, mocker, label, rubric, student_id, openai_gpt_response):
        # We will generate fake openai gpt responses where it gave us the labeled
        # rubrics in CSV or markdown (even though we told it NOT TO grr)
        ai_response = openai_gpt_response(rubric, num_responses=1, output_type='tsv')
        response = ai_response['choices'][0]['message']['content']

        # We can invalidate the response
        response = response.replace("Observations", "Things I notice")

        result = label.get_response_data_if_valid(response, rubric, student_id)
        assert result is None

    def test_should_return_none_when_a_key_concept_is_missing(self, mocker, label, rubric, student_id, openai_gpt_response):
        # We will generate fake openai gpt responses where it gave us the labeled
        # rubrics in CSV or markdown (even though we told it NOT TO grr)
        ai_response = openai_gpt_response(rubric, num_responses=1, output_type='tsv')
        response = ai_response['choices'][0]['message']['content']

        # Remove a random row from the response (ignoring the first row: the header)
        lines = response.splitlines()
        lines.remove(random.choice(lines[1:]))
        response = '\n'.join(lines)

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        result = label.get_response_data_if_valid(response, rubric, student_id)
        assert result is None

    def test_should_return_none_when_a_different_key_concept_is_found(self, mocker, label, rubric, student_id, openai_gpt_response):
        # We will generate fake openai gpt responses where it gave us the labeled
        # rubrics in CSV or markdown (even though we told it NOT TO grr)
        ai_response = openai_gpt_response(rubric, num_responses=1, output_type='tsv')
        response = ai_response['choices'][0]['message']['content']

        # Remove a random row from the response (ignoring the first row: the header)
        lines = response.splitlines()
        index = random.randint(1, len(lines) - 1)
        # We can corrupt by just adding a letter to the beginning, which is
        # where the key concept is written out in the TSV result.
        lines[index] = 'x' + lines[index]
        response = '\n'.join(lines)

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        result = label.get_response_data_if_valid(response, rubric, student_id)
        assert result is None

    def test_should_return_none_when_there_is_an_invalid_label(self, mocker, label, rubric, student_id, openai_gpt_response):
        # We will generate fake openai gpt responses where it gave us the labeled
        # rubrics in CSV or markdown (even though we told it NOT TO grr)
        ai_response = openai_gpt_response(rubric, num_responses=1, output_type='tsv')
        response = ai_response['choices'][0]['message']['content']

        # Remove a random row from the response (ignoring the first row: the header)
        lines = response.splitlines()
        index = random.randint(1, len(lines) - 1)
        # In this case, we can corrupt the third entry (the label)
        entries = lines[index].split('\t')
        entries[2] = 'x' + entries[2]
        lines[index] = '\t'.join(entries)
        response = '\n'.join(lines)

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        result = label.get_response_data_if_valid(response, rubric, student_id)
        assert result is None


class TestAiLabelStudentWork:
    def test_should_access_openai(self, requests_mock, openai_gpt_response, label, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        mock_gpt_response = openai_gpt_response(
            rubric=rubric,
            num_responses=num_responses
        )

        requests_mock.post(
            'https://api.openai.com/v1/chat/completions',
            json=mock_gpt_response
        )

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        result = label.ai_label_student_work(
            prompt, rubric, code, student_id, examples(rubric), num_responses, temperature, llm_model
        )

        # It should have a metadata and data section
        assert 'metadata' in result
        assert 'data' in result

        # It should return just as many labeled rows as there are in the rubric
        assert len(result['data']) == len(parsed_rubric)

        # It should contain the concepts given in the rubric
        assert set(x['Key Concept'] for x in parsed_rubric) == set(x['Key Concept'] for x in result['data'])
        
    def test_should_return_data_as_none_when_ai_result_is_empty(self, requests_mock, mocker, openai_gpt_response, label, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        mock_gpt_response = openai_gpt_response(
            rubric=rubric,
            num_responses=num_responses
        )

        requests_mock.post(
            'https://api.openai.com/v1/chat/completions',
            json=mock_gpt_response
        )

        # Mock the validator to invalidate everything
        mocker.patch.object(Label, 'get_response_data_if_valid').return_value = None

        with pytest.raises(InvalidResponseError):
            label.ai_label_student_work(
                prompt, rubric, code, student_id, examples(rubric), num_responses, temperature, llm_model
            )
        
    def test_should_return_the_choice_when_only_requesting_one_response(self, requests_mock, mocker, openai_gpt_response, label, prompt, rubric, code, student_id, examples, temperature, llm_model):
        num_responses = 1

        mock_gpt_response = openai_gpt_response(
            rubric=rubric,
            num_responses=num_responses
        )

        requests_mock.post(
            'https://api.openai.com/v1/chat/completions',
            json=mock_gpt_response
        )

        result = label.ai_label_student_work(
            prompt, rubric, code, student_id, examples(rubric), num_responses, temperature, llm_model
        )

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        # The data has an entry for every key concept
        assert len(result['data']) == len(parsed_rubric)

        # And none of the reasons state a vote
        assert all("Votes:" not in x['Reason'] for x in result['data'])

    def test_should_pass_api_key_from_env_var_to_header(self, requests_mock, openai_gpt_response, openai_api_key, label, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        # Set the key into the environment
        os.environ['OPENAI_API_KEY'] = openai_api_key

        requests_mock.post(
            'https://api.openai.com/v1/chat/completions',
            json=openai_gpt_response(rubric)
        )

        result = label.ai_label_student_work(
            prompt, rubric, code, student_id, examples(rubric), num_responses, temperature, llm_model
        )

        # Assert the the Bearer token header contains the API key
        assert requests_mock.last_request.headers['Authorization'].startswith("Bearer ")
        assert requests_mock.last_request.headers['Authorization'].index(openai_api_key) > 0

    def test_should_pass_arguments_to_openai(self, requests_mock, mocker, openai_gpt_response, label, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        mock_gpt_response = openai_gpt_response(
            rubric=rubric,
            num_responses=num_responses
        )

        requests_mock.post(
            'https://api.openai.com/v1/chat/completions',
            json=mock_gpt_response
        )

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        # Mock out compute_messages
        compute_messages = mocker.patch.object(Label, 'compute_messages')
        messages = ['messages']
        compute_messages.return_value = messages

        result = label.ai_label_student_work(
            prompt, rubric, code, student_id, examples(rubric), num_responses, temperature, llm_model
        )

        # It should have passed the model
        assert requests_mock.last_request.json()['model'] == llm_model
        assert requests_mock.last_request.json()['temperature'] == temperature
        assert requests_mock.last_request.json()['n'] == num_responses
        assert requests_mock.last_request.json()['messages'] == messages

    def test_should_raise_timeout(self, mocker, label, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        mocker.patch('lib.assessment.label.requests.post', side_effect = requests.exceptions.ReadTimeout())

        # Mock out compute_messages
        compute_messages = mocker.patch.object(Label, 'compute_messages')
        messages = ['messages']
        compute_messages.return_value = messages

        with pytest.raises(requests.exceptions.ReadTimeout):
            label.ai_label_student_work(
                prompt, rubric, code, student_id, examples(rubric), num_responses, temperature, llm_model
            )

    def test_should_log_status_error(self, requests_mock, caplog, label, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        requests_mock.post(
            'https://api.openai.com/v1/chat/completions',
            status_code=400
        )

        result = label.ai_label_student_work(
            prompt, rubric, code, student_id, examples(rubric), num_responses, temperature, llm_model
        )

        assert any(filter(lambda x: ('Error calling the API' in x.message) and x.levelno == logging.ERROR, caplog.records))
        assert result is None


class TestLabelStudentWork:
    @pytest.fixture
    def assessment_return_value(self, randomstring):
        """ Creates the return value for the *_label_student_work calls.
        """

        def gen_assessment(rubric, metadata={}):
            result_metadata = {"agent": ["openai"]}

            # Merge any metadata given to us
            result_metadata.update(metadata)

            # Form label sheet
            key_concepts = list(set(row['Key Concept'] for row in csv.DictReader(rubric.splitlines())))
            result_labels = list(
                map(lambda key_concept:
                    {
                        'Key Concept': key_concept,
                        'Observations': randomstring(10),
                        'Label': random.choice([
                            'Extensive Evidence',
                            'Convincing Evidence',
                            'Limited Evidence',
                            'No Evidence'
                        ]),
                        'Reason': randomstring(12)
                    },
                    key_concepts
                )
            )

            return {
                'metadata': result_metadata,
                'data': result_labels,
            }

        return gen_assessment

    def test_should_log_timeout(self, mocker, caplog, label, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        # Mock out static assessment
        mocker.patch.object(Label, 'test_for_blank_code').return_value = None

        # Mock out ai assessment to raise a timeout
        mocker.patch.object(Label, 'ai_label_student_work').side_effect = requests.exceptions.ReadTimeout()

        with pytest.raises(Exception):
            label.label_student_work(
                prompt, rubric, code, student_id,
                examples=examples(rubric),
                num_responses=num_responses,
                temperature=temperature,
                llm_model=llm_model,
                remove_comments=False
            )

        assert any(filter(lambda x: ('request timed out' in x.message) and x.levelno == logging.ERROR, caplog.records))

    def test_should_open_cached_responses_when_asked_and_they_exist(self, mocker, label, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        filename = f'cached_responses/{student_id}.json'

        # Mock the file read
        mock_open = mocker.mock_open(read_data='{"result": 42}')
        mock_file = mocker.patch('builtins.open', mock_open)

        # Mock the file exists
        exists_mock = mocker.patch('lib.assessment.label.os.path.exists', return_value=True)

        result = label.label_student_work(
            prompt, rubric, code, student_id,
            examples=examples(rubric),
            num_responses=num_responses,
            temperature=temperature,
            use_cached = True,
            llm_model=llm_model,
            remove_comments=False
        )

        exists_mock.assert_called_with(filename)

        mock_file.assert_called_with(filename, 'r')
        assert result == {"result": 42}

    def test_should_write_cached_responses_when_asked(self, mocker, label, assessment_return_value, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        filename = f'cached_responses/{student_id}.json'

        # Mock the file open / write
        mock_open = mocker.mock_open()
        mock_file = mocker.patch('builtins.open', mock_open)

        # Mock the file so it does not exist
        exists_mock = mocker.patch('lib.assessment.label.os.path.exists', return_value=False)

        # Get mocks
        test_for_blank_code_mock = mocker.patch.object(
            Label, 'test_for_blank_code',
            return_value=None
        )

        ai_label_student_work_mock = mocker.patch.object(
            Label, 'ai_label_student_work',
            return_value=assessment_return_value(rubric)
        )

        result = label.label_student_work(
            prompt, rubric, code, student_id,
            examples=examples(rubric),
            num_responses=num_responses,
            temperature=temperature,
            write_cached=True,
            llm_model=llm_model,
            remove_comments=False
        )

        mock_file.assert_called_with(filename, 'w+')

    def test_should_call_test_for_blank_code_before_ai_assessment(self, mocker, label, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        # Determine call order
        call_order = []

        # Get mocks
        test_for_blank_code_mock = mocker.patch.object(
            Label, 'test_for_blank_code',
            return_value=None
        ).side_effect = lambda *a, **kw: call_order.append('blank')

        ai_label_student_work_mock = mocker.patch.object(
            Label, 'ai_label_student_work',
            return_value=None
        ).side_effect = lambda *a, **kw: call_order.append('ai')

        try:
            result = label.label_student_work(
                prompt, rubric, code, student_id,
                examples=examples(rubric),
                num_responses=num_responses,
                temperature=temperature,
                use_cached = True,
                write_cached=False,
                llm_model=llm_model,
                remove_comments=False
            )
        except:
            pass

        assert call_order == ['blank', 'ai']

    def test_should_return_no_evidence_if_blank_code_detected(self, label, prompt, rubric, student_id):

        result = label.label_student_work(
            prompt, rubric, "", student_id
        )

        # It should have a metadata and data section
        assert 'metadata' in result
        assert 'data' in result

        # It should return No Evidence for all learning goals
        assert all(x["Label"] == "No Evidence" for x in result["data"])

    def test_should_call_ai_assessment_when_blank_code_check_returns_None(self, mocker, label, assessment_return_value, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        # Get mocks
        test_for_blank_code_mock = mocker.patch.object(
            Label, 'test_for_blank_code',
            return_value=None
        )

        ai_label_student_work_mock = mocker.patch.object(
            Label, 'ai_label_student_work',
            return_value=assessment_return_value(rubric)
        )

        result = label.label_student_work(
            prompt, rubric, code, student_id,
            examples=examples(rubric),
            num_responses=num_responses,
            temperature=temperature,
            write_cached=False,
            llm_model=llm_model,
            remove_comments=False
        )

        ai_label_student_work_mock.assert_called_once()

    def test_should_pass_params_through_to_ai_label_student_work(self, mocker, label, assessment_return_value, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        test_for_blank_code_mock = mocker.patch.object(
            Label, 'test_for_blank_code',
            return_value=None
        )

        ai_label_student_work_mock = mocker.patch.object(
            Label, 'ai_label_student_work',
            return_value=assessment_return_value(rubric)
        )

        response_type = 'json'
        expected_examples = examples(rubric)
        result = label.label_student_work(
            prompt, rubric, code, student_id,
            examples=expected_examples,
            num_responses=num_responses,
            temperature=temperature,
            write_cached=False,
            llm_model=llm_model,
            remove_comments=False,
            response_type=response_type
        )

        ai_label_student_work_mock.assert_called_once_with(
            prompt, rubric, code, student_id,
            examples=expected_examples,
            num_responses=num_responses,
            temperature=temperature,
            llm_model=llm_model,
            response_type=response_type
        )

    def test_should_call_ai_assessment_when_static_assessment_returns_assessed_learning_goal(self, mocker, label, assessment_return_value, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        
        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        code_feature_extractor = [parsed_rubric[-1]["Key Concept"]]

        # Get mocks
        cfe_label_student_work_mock = mocker.patch.object(
            Label, 'cfe_label_student_work',
            return_value={"metadata": {"agent": ["code feature extractor", "static analysis"]},
                          "data": [
                              {"Label": "No Evidence",
                               "Key Concept": parsed_rubric[-1]["Key Concept"],
                               "Observations": {'shapes': 0, 'sprites': 0, 'text': 0},
                               "Reason": parsed_rubric[-1]["No Evidence"],
                               }
                               ]}
        )

        ai_label_student_work_mock = mocker.patch.object(
            Label, 'ai_label_student_work',
            return_value=assessment_return_value(rubric)
        )

        result = label.label_student_work(
            prompt, rubric, code, student_id,
            examples=examples(rubric),
            num_responses=num_responses,
            temperature=temperature,
            write_cached=False,
            llm_model=llm_model,
            remove_comments=False,
            code_feature_extractor=code_feature_extractor
        )

        ai_label_student_work_mock.assert_called_once()


class TestGetConsensusResponse:
    @pytest.fixture
    def response_data_choices(self, label, openai_gpt_response):
        def gen_response_data_choices(rubric, student_id, num_responses=3, disagreements=1):
            # Disagreements always happen in the first choice... so they always
            # mean an 'outvote'
            ai_response = openai_gpt_response(rubric, num_responses=num_responses, disagreements=disagreements, output_type='tsv')
            responses = [label.get_response_data_if_valid(x['message']['content'], rubric, student_id) for x in ai_response['choices']]
            # return [list(csv.DictReader(StringIO(x), delimiter='\t')) for x in responses]
            return responses

        yield gen_response_data_choices

    def test_should_coalesce_votes(self, label, response_data_choices, rubric, student_id):
        choices = response_data_choices(rubric, student_id)
        result = label.get_consensus_response(choices, student_id)

        # It should have the same number of rows as the rubric has key concepts
        parsed_rubric = list(csv.DictReader(rubric.splitlines()))
        assert len(result) == len(parsed_rubric)

        # All of the results should be the majority label
        # (We know there are always 2 vs 1 in the vote)

        # Let's organize by concept name
        labels = {}
        for choice in choices:
            for entry in choice:
                key_concept = entry['Key Concept']
                labels[key_concept] = labels.get(key_concept, [])
                labels[key_concept].append(entry['Label'])

        # Now we have a dictionary where the key concept is mapped to the list
        # of labels. So, let's ensure that the resulting label is found at least twice
        # in the choice list.
        assert all(labels[entry['Key Concept']].count(entry['Label']) >= 2 for entry in result)

    def test_should_log_outvoting(self, caplog, label, response_data_choices, rubric, student_id):
        caplog.set_level(logging.INFO)

        choices = response_data_choices(rubric, student_id)
        result = label.get_consensus_response(choices, student_id)

        # It should have the same number of rows as the rubric has key concepts
        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        assert any(filter(lambda x: (f'outvoted {student_id}' in x.message) and x.levelno == logging.INFO, caplog.records))

    def test_reason_should_include_disagreeing_votes(self, label, response_data_choices, short_rubric, student_id):
        choices = response_data_choices(short_rubric, student_id, num_responses=3, disagreements=1)
        result = label.get_consensus_response(choices, student_id)
        assert 'Votes' in result[0]['Reason']

    def test_reason_should_exclude_agreeing_votes(self, label, response_data_choices, short_rubric, student_id):
        choices = response_data_choices(short_rubric, student_id, num_responses=3, disagreements=0)
        result = label.get_consensus_response(choices, student_id)
        assert 'Votes' not in result[0]['Reason']
