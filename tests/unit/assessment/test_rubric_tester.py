import csv
import pytest
import random

from unittest import mock
from types import SimpleNamespace

from lib.assessment.rubric_tester import (
    read_and_label_student_work,
    get_passing_labels,
    read_inputs,
    get_student_files,
    get_actual_labels,
    validate_rubrics,
    validate_students,
    compute_accuracy,
    init,
    main,
    get_examples,
)

from lib.assessment.label import Label, InvalidResponseError


class TestReadAndLabelStudentWork:
    def test_should_pass_arguments_through(self, mocker, code, prompt, rubric, examples, student_id, temperature, llm_model, remove_comments, response_type):
        label_student_work_mock = mocker.patch.object(Label, 'label_student_work')

        # Mock the file read
        mock_open = mocker.mock_open(read_data=code)
        mock_file = mocker.patch('builtins.open', mock_open)

        options = SimpleNamespace(
            use_cached=False,
            write_cached=False,
            num_responses=random.randint(1, 3),
            temperature=temperature,
            llm_model=llm_model,
            remove_comments=remove_comments,
        )

        labels = ['good data']
        label_student_work_mock.return_value = labels

        result = read_and_label_student_work(
            prompt=prompt,
            rubric=rubric,
            student_file=f"blah/{student_id}.js",
            examples=examples(rubric),
            options=options,
            params={},
            prefix="",
            response_type=response_type,
        )

        assert result[0] == student_id
        assert result[1] == labels


class TestReadInputs:
    def test_should_read_prompt_and_rubric_file(self, mocker, randomstring, prompt, rubric):
        prompt_file = randomstring(10) + '.txt'
        standard_rubric_file = randomstring(10) + '.csv'

        contents = {}
        contents[prompt_file] = prompt
        contents[standard_rubric_file] = rubric

        def file_open_mock(name, *a, **kw):
            return mocker.mock_open(read_data=contents.get(name, '')).return_value

        # Mock the file read
        m = mock.Mock()
        mock_open = mocker.mock_open(m)
        mock_file = mocker.patch('builtins.open', mock_open, create=True)
        m.side_effect = file_open_mock

        result = read_inputs(prompt_file, standard_rubric_file, "")

        assert result[0] == prompt
        assert result[1] == rubric


class TestGetStudentFiles:
    def test_should_return_student_code_paths_in_sample_code_path_when_given_ids(self):
        student_ids = [random.randint(100000, 999999) for _ in range(3, random.randint(10, 40))]

        result = get_student_files(len(student_ids), "sample_code", student_ids=student_ids)

        for student_id in student_ids:
            assert f'sample_code/{student_id}.js' in result

    def test_should_read_some_number_of_possible_files_from_sample_code_when_student_ids_is_none(self, mocker):
        student_ids = [random.randint(100000, 999999) for _ in range(3, random.randint(10, 40))]

        glob_mock = mocker.patch('glob.glob')
        glob_mock.return_value = [
        ]

        result = get_student_files(20, "", student_ids=None)

        assert len(result) <= 20

    def test_should_read_a_limited_number_of_possible_files_from_sample_code_when_max_is_larger_than_capacity(self, mocker):
        student_ids = [random.randint(100000, 999999) for _ in range(3, 50)]

        glob_mock = mocker.patch('glob.glob')
        glob_mock.return_value = [f'sample_code/{x}.js' for x in student_ids]

        result = get_student_files(20, "", student_ids=None)

        assert len(result) == 20


class TestGetActualLabels:
    def test_should_open_and_parse_the_given_file(self, mocker, rubric, random_label_generator):
        key_concepts = list(set(row['Key Concept'] for row in csv.DictReader(rubric.splitlines())))

        # Build header of key concepts starting with student id
        actual_csv_data = "student,"
        for key_concept in key_concepts:
            actual_csv_data += f'{key_concept},'

        # Chop off leading comma
        actual_csv_data = actual_csv_data[0:-1]

        # Now add random labels
        student_ids = [random.randint(100000, 999999) for _ in range(3, 50)]
        for student_id in student_ids:
            actual_csv_data += f'\n{student_id},'
            for key_concept in key_concepts:
                actual_csv_data += f'{random_label_generator()},'

            # Chop off leading comma
            actual_csv_data = actual_csv_data[0:-1]

        # Mock the file read
        mock_open = mocker.mock_open(read_data=actual_csv_data)
        mock_file = mocker.patch('builtins.open', mock_open)

        result = get_actual_labels('actual.csv', "")

        # The result it the size of the unique number of student ids
        assert len(result.keys()) == len(list(set(student_ids)))


class TestGetExamples:
    def test_should_open_example_js_and_tsv_files(self, mocker, code_generator, rubric, examples):
        examples_set = examples(rubric)

        contents = {}
        for i, example in enumerate(examples_set):
            contents[f'examples/{i}.js'] = example[0]
            contents[f'examples/{i}.tsv'] = example[1]

        def file_open_mock(name, *a, **kw):
            return mocker.mock_open(read_data=contents.get(name, '')).return_value

        # Mock the file read
        m = mock.Mock()
        mock_open = mocker.mock_open(m)
        mock_file = mocker.patch('builtins.open', mock_open, create=True)
        m.side_effect = file_open_mock

        glob_mock = mocker.patch('glob.glob')
        glob_mock.return_value = [f'examples/{x}.js' for x in range(0, len(examples_set))]

        result = get_examples("", response_type='tsv')

        assert len(result) == len(examples_set)

        for i, example in enumerate(result):
            assert example[0] == examples_set[i][0]
            assert example[1] == examples_set[i][1]

    def test_should_open_example_js_and_json_files(self, mocker, code_generator, rubric, examples):
        examples_set = examples(rubric)

        contents = {}
        for i, example in enumerate(examples_set):
            contents[f'examples/{i}.js'] = example[0]
            contents[f'examples/{i}.json'] = example[1]

        def file_open_mock(name, *a, **kw):
            return mocker.mock_open(read_data=contents.get(name, '')).return_value

        # Mock the file read
        m = mock.Mock()
        mock_open = mocker.mock_open(m)
        mock_file = mocker.patch('builtins.open', mock_open, create=True)
        m.side_effect = file_open_mock

        glob_mock = mocker.patch('glob.glob')
        glob_mock.return_value = [f'examples/{x}.js' for x in range(0, len(examples_set))]

        result = get_examples("", response_type='json')

        assert len(result) == len(examples_set)

        for i, example in enumerate(result):
            assert example[0] == examples_set[i][0]
            assert example[1] == examples_set[i][1]

class TestValidateRubrics:
    def test_should_raise_when_actual_labels_contains_a_concept_unknown_to_the_rubric(self, rubric, random_label_generator, randomstring):
        student_ids = [random.randint(100000, 999999) for _ in range(3, random.randint(10, 40))]
        key_concepts = list(set(row['Key Concept'] for row in csv.DictReader(rubric.splitlines())))

        actual_labels = {}

        unexpected_concept = randomstring(12)

        for student_id in student_ids:
            actual_labels[student_id] = {
                'student': student_id
            }

            for key_concept in key_concepts:
                actual_labels[student_id][key_concept] = random_label_generator()
            actual_labels[student_id][unexpected_concept] = random_label_generator()

        with pytest.raises(Exception):
            validate_rubrics(actual_labels, rubric)


class TestValidateStudents:
    def test_should_raise_when_student_work_exists_without_being_in_actual_labels(self, rubric, random_label_generator):
        student_ids = [str(random.randint(100000, 999999)) for _ in range(3, random.randint(10, 40))]
        key_concepts = list(set(row['Key Concept'] for row in csv.DictReader(rubric.splitlines())))

        actual_labels = {}
        unexpected_student = '199999x'

        for student_id in student_ids:
            actual_labels[student_id] = {
                'student': student_id
            }

            for key_concept in key_concepts:
                actual_labels[student_id][key_concept] = random_label_generator()

        student_files = [f'sample_code/{id}.js' for id in student_ids]
        student_files.append(f'sample_code/{unexpected_student}.js')

        with pytest.raises(Exception):
            validate_students(student_files, actual_labels)

    def test_should_not_raise_when_student_work_entirely_exists_in_actual_labels(self, rubric, random_label_generator):
        student_ids = [str(random.randint(100000, 999999)) for _ in range(3, random.randint(10, 40))]
        key_concepts = list(set(row['Key Concept'] for row in csv.DictReader(rubric.splitlines())))

        actual_labels = {}
        unexpected_student = '199999x'

        for student_id in student_ids:
            actual_labels[student_id] = {
                'student': student_id
            }

            for key_concept in key_concepts:
                actual_labels[student_id][key_concept] = random_label_generator()

        student_files = [f'sample_code/{id}.js' for id in student_ids]

        validate_students(student_files, actual_labels)

    def test_should_not_raise_when_there_is_an_unknown_student_in_actual_labels(self, rubric, random_label_generator):
        student_ids = [str(random.randint(100000, 999999)) for _ in range(3, random.randint(10, 40))]
        key_concepts = list(set(row['Key Concept'] for row in csv.DictReader(rubric.splitlines())))

        actual_labels = {}
        unexpected_student = '199999x'

        for student_id in student_ids:
            actual_labels[student_id] = {
                'student': student_id
            }

            for key_concept in key_concepts:
                actual_labels[student_id][key_concept] = random_label_generator()

        actual_labels[unexpected_student] = {
            'student': unexpected_student
        }

        for key_concept in key_concepts:
            actual_labels[unexpected_student][key_concept] = random_label_generator()

        student_files = [f'sample_code/{id}.js' for id in student_ids]

        validate_students(student_files, actual_labels)


class TestComputeAccuracy:
    # TODO: write these tests
    pass


class TestCommandLineOptions:
    # TODO: write these tests
    pass


class TestMain:
    # TODO: write these tests
    pass


class TestInit:
    def test_should_call_main_when_running_by_itself(self, mocker):
        main_mock = mocker.patch('lib.assessment.rubric_tester.main')
        mocker.patch('lib.assessment.rubric_tester.__name__', '__main__')

        init()

        main_mock.assert_called_once()
