import os

import pytest

from lib.assessment.grade import Grade
from lib.assessment.assess import grade


def test_grade_should_pass_arguments_along(
        mocker, code, prompt, rubric, examples, openai_api_key,
        llm_model, num_responses, temperature, remove_comments):
    """ Tests lib.assessment.assess.grade()
    """

    # Mock the Grade() class
    grade_student_work = mocker.patch.object(Grade, 'grade_student_work')

    # Actually call the method
    grade(code, prompt, rubric,
        examples=examples,
        api_key=openai_api_key,
        llm_model=llm_model,
        num_responses=num_responses,
        temperature=temperature,
        remove_comments=remove_comments
    )

    # Check to see that it was called
    grade_student_work.assert_called_with(prompt, rubric, code, "student",
        examples=examples,
        use_cached=False,
        write_cached=False,
        num_responses=num_responses,
        temperature=temperature,
        llm_model=llm_model,
        remove_comments=remove_comments
    )


def test_grade_should_set_api_key_in_env_var(
        mocker, code, prompt, rubric, examples, openai_api_key,
        llm_model, num_responses, temperature, remove_comments):
    """ Tests lib.assessment.assess.grade()
    """

    # Mock the Grade() class
    grade_student_work = mocker.patch.object(Grade, 'grade_student_work')

    # Actually call the method
    grade(code, prompt, rubric,
        examples=examples,
        api_key=openai_api_key,
        llm_model=llm_model,
        num_responses=num_responses,
        temperature=temperature,
        remove_comments=remove_comments
    )

    # Check to see that it was called
    assert os.environ['OPENAI_API_KEY'] == openai_api_key


def test_grade_should_return_empty_result_when_no_api_key(
        mocker, code, prompt, rubric, examples,
        llm_model, num_responses, temperature, remove_comments):
    """ Tests lib.assessment.assess.grade() (without an api-key)
    """

    # Mock the Grade() class
    grade_student_work = mocker.patch.object(Grade, 'grade_student_work')

    # Actually call the method
    result = grade(code, prompt, rubric,
        examples=examples,
        llm_model=llm_model,
        num_responses=num_responses,
        temperature=temperature,
        remove_comments=remove_comments
    )

    # Check to see an empty result
    assert result == {}


def test_grade_should_call_grade_student_work_with_api_key_in_env_var(
        mocker, code, prompt, rubric, examples, openai_api_key,
        llm_model, num_responses, temperature, remove_comments):
    """ Tests lib.assessment.assess.grade() (without an api-key)
    """

    # Set the environment variable
    os.environ['OPENAI_API_KEY'] = openai_api_key

    # Mock the Grade() class
    grade_student_work = mocker.patch.object(Grade, 'grade_student_work')

    # Actually call the method
    result = grade(code, prompt, rubric,
        examples=examples,
        llm_model=llm_model,
        num_responses=num_responses,
        temperature=temperature,
        remove_comments=remove_comments
    )

    # Actually call the method (without the api key)
    grade(code, prompt, rubric,
        examples=examples,
        llm_model=llm_model,
        num_responses=num_responses,
        temperature=temperature,
        remove_comments=remove_comments
    )
