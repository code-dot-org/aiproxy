import os
import csv
import json
import logging
import random

from io import StringIO

import requests
import pytest

from lib.assessment.grade import Grade, InvalidResponseError


@pytest.fixture
def grade():
    """ Creates a Grade() instance for any test that has a 'grade' parameter.
    """
    yield Grade()


class TestRemoveJsComments:
    def test_remove_js_comments(self, grade):
        # We combine a lot here... quotes escaped... comments in strings are ok, etc
        result = grade.remove_js_comments("""
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
    def test_should_call_remove_js_comments_if_wanted(self, mocker, grade, code):
        remove_js_comments_mock = mocker.patch.object(Grade, 'remove_js_comments')

        grade.sanitize_code(code, remove_comments=True)

        remove_js_comments_mock.assert_called_with(code)

    def test_should_not_call_remove_js_comments_if_not_wanted(self, mocker, grade, code):
        remove_js_comments_mock = mocker.patch.object(Grade, 'remove_js_comments')

        grade.sanitize_code(code, remove_comments=False)

        remove_js_comments_mock.assert_not_called()


class TestStaticallyGradeStudentWork:
    def test_should_return_no_evidence_on_blank_project(self, grade, rubric, student_id, examples):
        result = grade.statically_grade_student_work(
            rubric, "", student_id, examples(rubric)
        )

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        # It should have a metadata and data section
        assert 'metadata' in result
        assert 'data' in result

        # It should return just as many graded rows as there are in the rubric
        assert len(result['data']) == len(parsed_rubric)

        # It should return 'No Evidence' in every row
        assert all(x['Grade'] == 'No Evidence' for x in result['data'])

        # It should match the concepts given in the rubric
        assert set(x['Key Concept'] for x in parsed_rubric) == set(x['Key Concept'] for x in result['data'])

    def test_should_return_none_when_given_code(self, grade, code, rubric, student_id, examples):
        result = grade.statically_grade_student_work(
            rubric, code, student_id, examples(rubric)
        )

        assert result is None


class TestComputeMessages:
    def test_should_structure_messages_based_on_input(self, grade, prompt, rubric, code):
        result = grade.compute_messages(prompt, rubric, code, examples=[])

        assert len(result) == 2
        assert 'role' in result[0]
        assert result[0]['role'] == 'system'
        assert 'content' in result[0]
        assert prompt in result[0]['content']
        assert rubric in result[0]['content']
        assert 'role' in result[1]
        assert result[1]['role'] == 'user'
        assert code in result[1]['content']

    def test_should_add_examples(self, grade, prompt, rubric, code, examples):
        example_set = examples(rubric)
        result = grade.compute_messages(prompt, rubric, code, examples=example_set)

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


class TestGetTsvDataIfValid:
    def test_should_return_none_if_the_response_is_blank(self, grade, rubric, student_id):
        result = grade.get_tsv_data_if_valid("", rubric, student_id)

        assert result is None

    def test_should_log_the_choice_index_if_the_response_is_blank(self, caplog, grade, rubric, student_id):
        index = random.randint(0, 5)
        grade.get_tsv_data_if_valid("", rubric, student_id, choice_index=index)

        assert any(filter(lambda x: (f'Choice {index}' in x.message) and x.levelno == logging.ERROR, caplog.records))

    @pytest.mark.parametrize("output_type", ['tsv', 'csv', 'markdown'])
    def test_should_work_for_different_output_types(self, grade, rubric, student_id, openai_gpt_response, output_type):
        # We will generate fake openai gpt responses where it gave us the graded
        # rubrics in CSV or markdown (even though we told it NOT TO grr)
        ai_response = openai_gpt_response(rubric, num_responses=1, output_type=output_type)
        response = ai_response['choices'][0]['message']['content']

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        # It should parse them out to get the same number of rows as the rubric
        result = grade.get_tsv_data_if_valid(response, rubric, student_id)
        assert result is not None
        assert len(result) == len(parsed_rubric)

    @pytest.mark.parametrize("output_type", ['tsv', 'csv', 'markdown'])
    def test_should_work_for_different_output_types_with_leading_text(self, grade, rubric, student_id, openai_gpt_response, output_type):
        # We will generate fake openai gpt responses where it gave us the graded
        # rubrics in CSV or markdown (even though we told it NOT TO grr)
        ai_response = openai_gpt_response(rubric, num_responses=1, output_type=output_type)
        response = "Bogus Weasel lines\n" + ai_response['choices'][0]['message']['content']

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        # It should parse them out to get the same number of rows as the rubric
        result = grade.get_tsv_data_if_valid(response, rubric, student_id)
        assert result is not None
        assert len(result) == len(parsed_rubric)

    def test_should_work_for_tsv_output_where_it_escapes_tabs(self, grade, rubric, student_id, openai_gpt_response):
        # ChatGPT will sometimes give you tsv (yay!) but escape the tabs for some reason (boo!)
        ai_response = openai_gpt_response(rubric, num_responses=1, output_type='tsv')
        response = ai_response['choices'][0]['message']['content'].replace('\t', '\\t')

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        # It should parse them out to get the same number of rows as the rubric
        result = grade.get_tsv_data_if_valid(response, rubric, student_id)
        assert result is not None
        assert len(result) == len(parsed_rubric)

    def test_should_work_when_there_are_weird_entries(self, mocker, grade, rubric, student_id, openai_gpt_response):
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
        result = grade.get_tsv_data_if_valid(response, rubric, student_id)
        assert result is not None
        assert len(result) == len(parsed_rubric)

    def test_should_return_none_when_there_is_no_key_concept(self, mocker, grade, rubric, student_id, openai_gpt_response):
        # We will generate fake openai gpt responses where it gave us the graded
        # rubrics in CSV or markdown (even though we told it NOT TO grr)
        ai_response = openai_gpt_response(rubric, num_responses=1, output_type='tsv')
        response = ai_response['choices'][0]['message']['content']

        # We can invalidate the response
        response = response.replace("Key Concept", "Bogus Weasel")

        result = grade.get_tsv_data_if_valid(response, rubric, student_id)
        assert result is None

    def test_should_return_none_when_the_columns_are_invalid(self, mocker, grade, rubric, student_id, openai_gpt_response):
        # We will generate fake openai gpt responses where it gave us the graded
        # rubrics in CSV or markdown (even though we told it NOT TO grr)
        ai_response = openai_gpt_response(rubric, num_responses=1, output_type='tsv')
        response = ai_response['choices'][0]['message']['content']

        # We can invalidate the response
        response = response.replace("Observations", "Things I notice")

        result = grade.get_tsv_data_if_valid(response, rubric, student_id)
        assert result is None

    def test_should_return_none_when_a_key_concept_is_missing(self, mocker, grade, rubric, student_id, openai_gpt_response):
        # We will generate fake openai gpt responses where it gave us the graded
        # rubrics in CSV or markdown (even though we told it NOT TO grr)
        ai_response = openai_gpt_response(rubric, num_responses=1, output_type='tsv')
        response = ai_response['choices'][0]['message']['content']

        # Remove a random row from the response (ignoring the first row: the header)
        lines = response.splitlines()
        lines.remove(random.choice(lines[1:]))
        response = '\n'.join(lines)

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        result = grade.get_tsv_data_if_valid(response, rubric, student_id)
        assert result is None

    def test_should_return_none_when_a_different_key_concept_is_found(self, mocker, grade, rubric, student_id, openai_gpt_response):
        # We will generate fake openai gpt responses where it gave us the graded
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

        result = grade.get_tsv_data_if_valid(response, rubric, student_id)
        assert result is None

    def test_should_return_none_when_there_is_an_invalid_grade(self, mocker, grade, rubric, student_id, openai_gpt_response):
        # We will generate fake openai gpt responses where it gave us the graded
        # rubrics in CSV or markdown (even though we told it NOT TO grr)
        ai_response = openai_gpt_response(rubric, num_responses=1, output_type='tsv')
        response = ai_response['choices'][0]['message']['content']

        # Remove a random row from the response (ignoring the first row: the header)
        lines = response.splitlines()
        index = random.randint(1, len(lines) - 1)
        # In this case, we can corrupt the third entry (the grade)
        entries = lines[index].split('\t')
        entries[2] = 'x' + entries[2]
        lines[index] = '\t'.join(entries)
        response = '\n'.join(lines)

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        result = grade.get_tsv_data_if_valid(response, rubric, student_id)
        assert result is None


class TestAiGradeStudentWork:
    def test_should_access_openai(self, requests_mock, openai_gpt_response, grade, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        mock_gpt_response = openai_gpt_response(
            rubric=rubric,
            num_responses=num_responses
        )

        requests_mock.post(
            'https://api.openai.com/v1/chat/completions',
            json=mock_gpt_response
        )

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        result = grade.ai_grade_student_work(
            prompt, rubric, code, student_id, examples(rubric), num_responses, temperature, llm_model
        )

        # It should have a metadata and data section
        assert 'metadata' in result
        assert 'data' in result

        # It should return just as many graded rows as there are in the rubric
        assert len(result['data']) == len(parsed_rubric)

        # It should contain the concepts given in the rubric
        assert set(x['Key Concept'] for x in parsed_rubric) == set(x['Key Concept'] for x in result['data'])
        
    def test_should_return_data_as_none_when_ai_result_is_empty(self, requests_mock, mocker, openai_gpt_response, grade, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        mock_gpt_response = openai_gpt_response(
            rubric=rubric,
            num_responses=num_responses
        )

        requests_mock.post(
            'https://api.openai.com/v1/chat/completions',
            json=mock_gpt_response
        )

        # Mock the validator to invalidate everything
        mocker.patch.object(Grade, 'get_tsv_data_if_valid').return_value = None

        with pytest.raises(InvalidResponseError):
            grade.ai_grade_student_work(
                prompt, rubric, code, student_id, examples(rubric), num_responses, temperature, llm_model
            )
        
    def test_should_return_the_choice_when_only_requesting_one_response(self, requests_mock, mocker, openai_gpt_response, grade, prompt, rubric, code, student_id, examples, temperature, llm_model):
        num_responses = 1

        mock_gpt_response = openai_gpt_response(
            rubric=rubric,
            num_responses=num_responses
        )

        requests_mock.post(
            'https://api.openai.com/v1/chat/completions',
            json=mock_gpt_response
        )

        result = grade.ai_grade_student_work(
            prompt, rubric, code, student_id, examples(rubric), num_responses, temperature, llm_model
        )

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        # The data has an entry for every key concept
        assert len(result['data']) == len(parsed_rubric)

        # And none of the reasons state a vote
        assert all("Votes:" not in x['Reason'] for x in result['data'])

    def test_should_pass_api_key_from_env_var_to_header(self, requests_mock, openai_gpt_response, openai_api_key, grade, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        # Set the key into the environment
        os.environ['OPENAI_API_KEY'] = openai_api_key

        requests_mock.post(
            'https://api.openai.com/v1/chat/completions',
            json=openai_gpt_response(rubric)
        )

        result = grade.ai_grade_student_work(
            prompt, rubric, code, student_id, examples(rubric), num_responses, temperature, llm_model
        )

        # Assert the the Bearer token header contains the API key
        assert requests_mock.last_request.headers['Authorization'].startswith("Bearer ")
        assert requests_mock.last_request.headers['Authorization'].index(openai_api_key) > 0

    def test_should_pass_arguments_to_openai(self, requests_mock, mocker, openai_gpt_response, grade, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
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
        compute_messages = mocker.patch.object(Grade, 'compute_messages')
        messages = ['messages']
        compute_messages.return_value = messages

        result = grade.ai_grade_student_work(
            prompt, rubric, code, student_id, examples(rubric), num_responses, temperature, llm_model
        )

        # It should have passed the model
        assert requests_mock.last_request.json()['model'] == llm_model
        assert requests_mock.last_request.json()['temperature'] == temperature
        assert requests_mock.last_request.json()['n'] == num_responses
        assert requests_mock.last_request.json()['messages'] == messages

    def test_should_raise_timeout(self, mocker, grade, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        mocker.patch('lib.assessment.grade.requests.post', side_effect = requests.exceptions.ReadTimeout())

        # Mock out compute_messages
        compute_messages = mocker.patch.object(Grade, 'compute_messages')
        messages = ['messages']
        compute_messages.return_value = messages

        with pytest.raises(requests.exceptions.ReadTimeout):
            grade.ai_grade_student_work(
                prompt, rubric, code, student_id, examples(rubric), num_responses, temperature, llm_model
            )

    def test_should_log_status_error(self, requests_mock, caplog, grade, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        requests_mock.post(
            'https://api.openai.com/v1/chat/completions',
            status_code=400
        )

        result = grade.ai_grade_student_work(
            prompt, rubric, code, student_id, examples(rubric), num_responses, temperature, llm_model
        )

        assert any(filter(lambda x: ('Error calling the API' in x.message) and x.levelno == logging.ERROR, caplog.records))
        assert result is None


class TestGradeStudentWork:
    @pytest.fixture
    def assessment_return_value(self, randomstring):
        """ Creates the return value for the *_grade_student_work calls.
        """

        def gen_assessment(rubric, metadata={}):
            result_metadata = {}

            # Merge any metadata given to us
            result_metadata.update(metadata)

            # Form grade sheet
            key_concepts = list(set(row['Key Concept'] for row in csv.DictReader(rubric.splitlines())))
            result_grades = list(
                map(lambda key_concept:
                    {
                        'Key Concept': key_concept,
                        'Observations': randomstring(10),
                        'Grade': random.choice([
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
                'data': result_grades,
            }

        return gen_assessment

    def test_should_log_timeout(self, mocker, caplog, grade, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        # Mock out static assessment
        mocker.patch.object(Grade, 'statically_grade_student_work').return_value = None

        # Mock out ai assessment to raise a timeout
        mocker.patch.object(Grade, 'ai_grade_student_work').side_effect = requests.exceptions.ReadTimeout()

        with pytest.raises(Exception):
            grade.grade_student_work(
                prompt, rubric, code, student_id,
                examples=examples(rubric),
                num_responses=num_responses,
                temperature=temperature,
                llm_model=llm_model,
                remove_comments=False
            )

        assert any(filter(lambda x: ('request timed out' in x.message) and x.levelno == logging.ERROR, caplog.records))

    def test_should_open_cached_responses_when_asked_and_they_exist(self, mocker, grade, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        filename = f'cached_responses/{student_id}.json'

        # Mock the file read
        mock_open = mocker.mock_open(read_data='{"result": 42}')
        mock_file = mocker.patch('builtins.open', mock_open)

        # Mock the file exists
        exists_mock = mocker.patch('lib.assessment.grade.os.path.exists', return_value=True)

        result = grade.grade_student_work(
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

    def test_should_write_cached_responses_when_asked(self, mocker, grade, assessment_return_value, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        filename = f'cached_responses/{student_id}.json'

        # Mock the file open / write
        mock_open = mocker.mock_open()
        mock_file = mocker.patch('builtins.open', mock_open)

        # Mock the file so it does not exist
        exists_mock = mocker.patch('lib.assessment.grade.os.path.exists', return_value=False)

        # Get mocks
        statically_grade_student_work_mock = mocker.patch.object(
            Grade, 'statically_grade_student_work',
            return_value=None
        )

        ai_grade_student_work_mock = mocker.patch.object(
            Grade, 'ai_grade_student_work',
            return_value=assessment_return_value(rubric)
        )

        result = grade.grade_student_work(
            prompt, rubric, code, student_id,
            examples=examples(rubric),
            num_responses=num_responses,
            temperature=temperature,
            write_cached=True,
            llm_model=llm_model,
            remove_comments=False
        )

        mock_file.assert_called_with(filename, 'w+')

    def test_should_call_statically_grade_student_work_before_ai_assessment(self, mocker, grade, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        # Determine call order
        call_order = []

        # Get mocks
        statically_grade_student_work_mock = mocker.patch.object(
            Grade, 'statically_grade_student_work',
            return_value=None
        ).side_effect = lambda *a, **kw: call_order.append('static')

        ai_grade_student_work_mock = mocker.patch.object(
            Grade, 'ai_grade_student_work',
            return_value=None
        ).side_effect = lambda *a, **kw: call_order.append('ai')

        try:
            result = grade.grade_student_work(
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

        assert call_order == ['static', 'ai']

    def test_should_call_ai_assessment_when_static_assessment_returns_none(self, mocker, grade, assessment_return_value, prompt, rubric, code, student_id, examples, num_responses, temperature, llm_model):
        # Get mocks
        statically_grade_student_work_mock = mocker.patch.object(
            Grade, 'statically_grade_student_work',
            return_value=None
        )

        ai_grade_student_work_mock = mocker.patch.object(
            Grade, 'ai_grade_student_work',
            return_value=assessment_return_value(rubric)
        )

        result = grade.grade_student_work(
            prompt, rubric, code, student_id,
            examples=examples(rubric),
            num_responses=num_responses,
            temperature=temperature,
            write_cached=False,
            llm_model=llm_model,
            remove_comments=False
        )

        ai_grade_student_work_mock.assert_called_once()


class TestGetConsensusResponse:
    @pytest.fixture
    def tsv_data_choices(self, openai_gpt_response):
        def gen_tsv_data_choices(rubric):
            # Disagreements always happen in the first choice... so they always
            # mean an 'outvote'
            ai_response = openai_gpt_response(rubric, num_responses=3, disagreements=1, output_type='tsv')
            responses = [x['message']['content'] for x in ai_response['choices']]
            return [list(csv.DictReader(StringIO(x), delimiter='\t')) for x in responses]

        yield gen_tsv_data_choices

    def test_should_coalesce_votes(self, grade, tsv_data_choices, rubric, student_id):
        choices = tsv_data_choices(rubric)
        result = grade.get_consensus_response(choices, student_id)

        # It should have the same number of rows as the rubric has key concepts
        parsed_rubric = list(csv.DictReader(rubric.splitlines()))
        assert len(result) == len(parsed_rubric)

        # All of the results should be the majority grade
        # (We know there are always 2 vs 1 in the vote)

        # Let's organize by concept name
        grades = {}
        for choice in choices:
            for entry in choice:
                key_concept = entry['Key Concept']
                grades[key_concept] = grades.get(key_concept, [])
                grades[key_concept].append(entry['Grade'])

        # Now we have a dictionary where the key concept is mapped to the list
        # of grades. So, let's ensure that the resulting grade is found at least twice
        # in the choice list.
        assert all(grades[entry['Key Concept']].count(entry['Grade']) >= 2 for entry in result)

    def test_should_log_outvoting(self, caplog, grade, tsv_data_choices, rubric, student_id):
        caplog.set_level(logging.INFO)

        choices = tsv_data_choices(rubric)
        result = grade.get_consensus_response(choices, student_id)

        # It should have the same number of rows as the rubric has key concepts
        parsed_rubric = list(csv.DictReader(rubric.splitlines()))

        assert any(filter(lambda x: (f'outvoted {student_id}' in x.message) and x.levelno == logging.INFO, caplog.records))
