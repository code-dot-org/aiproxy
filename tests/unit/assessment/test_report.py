import re
import io
import csv
import pytest
import random

from lib.assessment.report import Report


@pytest.fixture
def report():
    """ Creates a Report() instance for any test that has a 'report' parameter.
    """
    yield Report()


class TestAccurate:
    def test_should_just_match_actual_to_predicted_if_no_passing_labels(self):
        assert Report.accurate('No Evidence', 'No Evidence', None)

    def test_should_return_false_when_actual_is_not_predicted_if_no_passing_labels(self):
        assert Report.accurate('No Evidence', 'Limited Evidence', None) == False

    def test_should_count_equal_number_of_matching_labels_in_given_passing_labels(self):
        assert Report.accurate('Convincing Evidence', 'Convincing Evidence', ['Convincing Evidence', 'Extensive Evidence'])

    def test_should_be_true_when_actual_not_matching_predicted_but_both_in_given_passing_labels(self):
        assert Report.accurate('Convincing Evidence', 'Extensive Evidence', ['Convincing Evidence', 'Extensive Evidence'])

    def test_should_return_true_when_neither_are_in_set_of_passing_labels(self):
        assert Report.accurate('No Evidence', 'Limited Evidence', ['Convincing Evidence', 'Extensive Evidence'])

    def test_should_return_false_when_actual_is_not_in_set_of_passing_labels(self):
        assert Report.accurate('No Evidence', 'Convincing Evidence', ['Convincing Evidence', 'Extensive Evidence']) == False

    def test_should_return_false_when_predicted_is_not_in_set_of_passing_labels(self):
        assert Report.accurate('Convincing Evidence', 'No Evidence', ['Convincing Evidence', 'Extensive Evidence']) == False


class TestGenerateHtmlOutput:
    def _get_output(self, mock_file):
        # I get an array of strings of all the mocked out calls the file object
        # saw. Every one of the calls to `write()` is taken out and stripped to
        # the string argument. (We eliminate the last two charcters: the final
        # quote and the right parentheses.)
        return ''.join(
            map(
                lambda x: x[x.index('write(') + 7:-2],
                filter(
                    lambda x: 'write(' in x,
                    list(str(x) for x in mock_file.mock_calls)
                )
            )
        )

    def test_should_open_given_file(self, mocker, report, prompt, rubric, randomstring):
        # Generate a random output filename
        output_file = f'{randomstring(10)}.html'

        # Mock the file open / write
        mock_open = mocker.mock_open()
        mock_file = mocker.patch('builtins.open', mock_open)

        report.generate_html_output(
            output_file,
            prompt,
            rubric,
            accuracy="42",
            command_line="./assess.py",
        )

        mock_file.assert_called_with(output_file, 'w+')

    def test_should_write_html(self, mocker, report, prompt, rubric, randomstring):
        # Generate a random output filename
        output_file = f'{randomstring(10)}.html'

        # Mock the file open / write
        mock_open = mocker.mock_open()
        mock_file = mocker.patch('builtins.open', mock_open)

        report.generate_html_output(
            output_file,
            prompt,
            rubric,
            accuracy="42",
            command_line="./assess.py",
        )

        output = self._get_output(mock_file)

        assert "<!DOCTYPE html>" in output
        assert "<html" in output
        assert "</html>" in output

    def test_should_write_html_for_given_rubric(self, mocker, report, prompt, rubric, randomstring):
        # Generate a random output filename
        output_file = f'{randomstring(10)}.html'

        # Mock the file open / write
        mock_open = mocker.mock_open()
        mock_file = mocker.patch('builtins.open', mock_open)

        report.generate_html_output(
            output_file,
            prompt,
            rubric,
            accuracy="42",
            command_line="./assess.py",
        )

        output = self._get_output(mock_file)

        parsed_rubric = list(csv.DictReader(rubric.splitlines()))
        for v in parsed_rubric:
            for _, v in v.items():
                assert f"<td>{v}</td>" in output

    def test_should_report_not_available_when_accuracy_is_not_given(self, mocker, report, prompt, rubric, randomstring):
        # Generate a random output filename
        output_file = f'{randomstring(10)}.html'

        # Mock the file open / write
        mock_open = mocker.mock_open()
        mock_file = mocker.patch('builtins.open', mock_open)

        report.generate_html_output(
            output_file,
            prompt,
            rubric,
            command_line="./assess.py",
        )

        output = self._get_output(mock_file)

        assert "Accuracy: N/A" in output

    def test_should_report_accuracy_table(self, mocker, report, prompt, rubric, randomstring):
        # Generate a random output filename
        output_file = f'{randomstring(10)}.html'

        # Mock the file open / write
        mock_open = mocker.mock_open()
        mock_file = mocker.patch('builtins.open', mock_open)

        includes_one_green = False
        includes_one_red = False

        accuracy_by_criteria = {}
        parsed_rubric = list(csv.DictReader(rubric.splitlines()))
        key_concepts = [x['Key Concept'] for x in parsed_rubric]
        for key_concept in key_concepts:
            if not includes_one_green:
                accuracy_by_criteria[key_concept] = random.randint(51, 100)
                includes_one_green = True
            if not includes_one_red:
                accuracy_by_criteria[key_concept] = random.randint(0, 50)
                includes_one_red = True
            else:
                accuracy_by_criteria[key_concept] = random.randint(0, 100)

        report.generate_html_output(
            output_file,
            prompt,
            rubric,
            accuracy_by_criteria=accuracy_by_criteria,
            command_line="./assess.py",
        )

        output = self._get_output(mock_file)

        for key_concept in key_concepts:
            assert re.search(fr'<td>{key_concept}</td>.*>{accuracy_by_criteria[key_concept]}%<', output)

    def test_should_report_confusion_table(self, mocker, report, prompt, rubric, randomstring):
        # Generate a random output filename
        output_file = f'{randomstring(10)}.html'

        # Mock the file open / write
        mock_open = mocker.mock_open()
        mock_file = mocker.patch('builtins.open', mock_open)

        labels = ['a', 'b', 'c', 'd']
        confusion_by_criteria = {}
        parsed_rubric = list(csv.DictReader(rubric.splitlines()))
        key_concepts = [x['Key Concept'] for x in parsed_rubric]
        overall_confusion = []
        for l in labels:
            overall_confusion.append(random.sample(range(0, 100), len(labels)))
        for key_concept in key_concepts:
            confusion_by_criteria[key_concept] = []
            for l in labels:
                confusion_by_criteria[key_concept].append(random.sample(range(0, 100), len(labels)))

        report.generate_html_output(
            output_file,
            prompt,
            rubric,
            command_line="./assess.py",
            overall_confusion=overall_confusion,
            confusion_by_criteria=confusion_by_criteria,
            label_names=labels,
        )

        output = self._get_output(mock_file)

        assert re.search(fr'<h2>Overall Confusion:</h2>.*style="text-align: center">{overall_confusion[0][0]}<', output)
        for key_concept in key_concepts:
            assert re.search(fr'<h3>Confusion for {key_concept}:</h3>.*style="text-align: center">{confusion_by_criteria[key_concept][0][0]}<', output)

    def test_should_report_generated_label_report(self, mocker, report, prompt, rubric, random_label_generator, randomstring):
        # Generate a random output filename
        output_file = f'{randomstring(10)}.html'

        # Mock the file open / write
        mock_open = mocker.mock_open()
        mock_file = mocker.patch('builtins.open', mock_open)

        predicted_labels = {}
        actual_labels = {}
        parsed_rubric = list(csv.DictReader(rubric.splitlines()))
        key_concepts = [x['Key Concept'] for x in parsed_rubric]
        for _ in range(1, random.randint(3, 10)):
            student_id = str(random.randint(100000, 999999))

            predicted_labels[student_id] = list(map(lambda key_concept:
                {
                    'Key Concept': key_concept,
                    'Observations': 'What I see',
                    'Label': random_label_generator(),
                    'Reason': 'Why I think so'
                },
                key_concepts
            ))

            for key_concept in key_concepts:
                actual_labels[student_id] = actual_labels.get(student_id, {})
                actual_labels[student_id][key_concept] = random_label_generator()

        report.generate_html_output(
            output_file,
            prompt,
            rubric,
            predicted_labels=predicted_labels,
            actual_labels=actual_labels,
            command_line="./assess.py",
        )

        output = self._get_output(mock_file)

        for student_id, labels in predicted_labels.items():
            for label in labels:
                key_concept = label['Key Concept']

                assert re.search(fr'<td>{key_concept}</td>.*>{actual_labels[student_id][key_concept]}<', output)
                assert re.search(fr'<td>{key_concept}</td>.*>{label["Label"]}<', output)

    def test_should_report_generated_label_report_with_pass_fail(self, mocker, report, prompt, rubric, random_label_generator, randomstring):
        # Generate a random output filename
        output_file = f'{randomstring(10)}.html'

        # Mock the file open / write
        mock_open = mocker.mock_open()
        mock_file = mocker.patch('builtins.open', mock_open)

        predicted_labels = {}
        actual_labels = {}
        parsed_rubric = list(csv.DictReader(rubric.splitlines()))
        key_concepts = [x['Key Concept'] for x in parsed_rubric]
        for _ in range(1, random.randint(3, 10)):
            student_id = str(random.randint(100000, 999999))

            predicted_labels[student_id] = list(map(lambda key_concept:
                {
                    'Key Concept': key_concept,
                    'Observations': 'What I see',
                    'Label': random_label_generator(),
                    'Reason': 'Why I think so'
                },
                key_concepts
            ))

            for key_concept in key_concepts:
                actual_labels[student_id] = actual_labels.get(student_id, {})
                actual_labels[student_id][key_concept] = random_label_generator()

        passing_labels = ['Extensive Evidence', 'Convincing Evidence']
        report.generate_html_output(
            output_file,
            prompt,
            rubric,
            predicted_labels=predicted_labels,
            actual_labels=actual_labels,
            passing_labels=passing_labels,
            command_line="./assess.py",
        )

        output = self._get_output(mock_file)

        for student_id, labels in predicted_labels.items():
            for label in labels:
                key_concept = label['Key Concept']

                assert re.search(fr'<td>{key_concept}</td>.*>{actual_labels[student_id][key_concept]}<', output)
                assert re.search(fr'<td>{key_concept}</td>.*>{label["Label"]}<', output)

    def test_should_report_errors(self, mocker, report, prompt, rubric, random_label_generator, randomstring):
        # Generate a random output filename
        output_file = f'{randomstring(10)}.html'

        # Mock the file open / write
        mock_open = mocker.mock_open()
        mock_file = mocker.patch('builtins.open', mock_open)

        errors = []
        for _ in range(0, random.randint(1, 5)):
            errors.append(randomstring(12))

        report.generate_html_output(
            output_file,
            prompt,
            rubric,
            errors=errors,
            command_line="./assess.py",
        )

        output = self._get_output(mock_file)

        # Find the error count listed
        assert f"Errors: {len(errors)}" in output

        # Find all of the random strings we used as errored student ids
        for error in errors:
            assert error in output
            
