import os

import pytest

from lib.assessment.label import Label
from lib.assessment.assess import label, KeyConceptError


def test_label_should_pass_arguments_along(
        mocker, code, prompt, rubric, examples, openai_api_key,
        llm_model, num_responses, temperature, remove_comments, response_type):
    """ Tests lib.assessment.assess.label()
    """

    # import test data
    rubric = ''
    with open('tests/data/u3l13.csv', 'r') as f:
        rubric = f.read()

    examples = []
    with open('tests/data/example.js', 'r') as f:
        examples.append(f.read())
    with open('tests/data/example.tsv', 'r') as f:
        examples.append(f.read())
    examples = [examples]

    # Mock the Label() class
    label_student_work = mocker.patch.object(Label, 'label_student_work')

    # Actually call the method
    label(code, prompt, rubric,
        examples=examples,
        api_key=openai_api_key,
        llm_model=llm_model,
        num_responses=num_responses,
        temperature=temperature,
        remove_comments=remove_comments,
        response_type=response_type
    )

    # Check to see that it was called
    label_student_work.assert_called_with(prompt, rubric, code, "student",
        examples=examples,
        use_cached=False,
        write_cached=False,
        num_responses=num_responses,
        temperature=temperature,
        llm_model=llm_model,
        remove_comments=remove_comments,
        response_type=response_type
    )


def test_label_should_set_api_key_in_env_var(
        mocker, code, prompt, rubric, examples, openai_api_key,
        llm_model, num_responses, temperature, remove_comments):
    """ Tests lib.assessment.assess.label()
    """

    # Mock the Label() class
    label_student_work = mocker.patch.object(Label, 'label_student_work')

    # Actually call the method
    label(code, prompt, rubric,
        examples=examples(rubric, 0),
        api_key=openai_api_key,
        llm_model=llm_model,
        num_responses=num_responses,
        temperature=temperature,
        remove_comments=remove_comments
    )

    # Check to see that it was called
    assert os.environ['OPENAI_API_KEY'] == openai_api_key


def test_label_should_return_empty_result_when_no_api_key(
        mocker, code, prompt, rubric, examples,
        llm_model, num_responses, temperature, remove_comments):
    """ Tests lib.assessment.assess.label() (without an api-key)
    """

    # Mock the Label() class
    label_student_work = mocker.patch.object(Label, 'label_student_work')

    # Actually call the method
    result = label(code, prompt, rubric,
        examples=examples(rubric, 0),
        llm_model=llm_model,
        num_responses=num_responses,
        temperature=temperature,
        remove_comments=remove_comments
    )

    # Check to see an empty result
    assert result == {}


def test_label_should_return_empty_result_when_example_and_rubric_key_concepts_mismatch(
        mocker, code, prompt, rubric, examples, openai_api_key,
        llm_model, num_responses, temperature, remove_comments):
    """ Tests lib.assessment.assess.label() (without an api-key)
    """
    # Mock the Label() class
    label_student_work = mocker.patch.object(Label, 'label_student_work')

    example = []
    with open('tests/data/example.js', 'r') as f:
        example.append(f.read())
    with open('tests/data/example.tsv', 'r') as f:
        example.append(f.read())

    with pytest.raises(KeyConceptError):
        label(code, prompt, rubric,
            examples=example,
            api_key=openai_api_key,
            llm_model=llm_model,
            num_responses=num_responses,
            temperature=temperature,
            remove_comments=remove_comments
        )


def test_label_should_call_label_student_work_with_api_key_in_env_var(
        mocker, code, prompt, rubric, examples, openai_api_key,
        llm_model, num_responses, temperature, remove_comments):
    """ Tests lib.assessment.assess.label() (without an api-key)
    """

    # Set the environment variable
    os.environ['OPENAI_API_KEY'] = openai_api_key

    # Mock the Label() class
    label_student_work = mocker.patch.object(Label, 'label_student_work')

    # Actually call the method
    result = label(code, prompt, rubric,
        examples=examples(rubric, 0),
        llm_model=llm_model,
        num_responses=num_responses,
        temperature=temperature,
        remove_comments=remove_comments
    )

    # Actually call the method (without the api key)
    label(code, prompt, rubric,
        examples=examples(rubric, 0),
        llm_model=llm_model,
        num_responses=num_responses,
        temperature=temperature,
        remove_comments=remove_comments
    )
