import csv
import hashlib
import io
import json
import math
import os
import re
from datetime import datetime
from itertools import product, chain
from typing import List, Dict, Any
from lib.assessment.config import VALID_LABELS, PASSING_LABELS

class Report:
    def _compute_pass_fail_cell_color(self, actual, predicted):
        if Report.accurate_pass_fail(actual, predicted):
            return 'green'
        else:
            return 'red'

    def _compute_predicted_cell_color(self, predicted, actual, is_pass_fail):
        if is_pass_fail:
            return self._compute_pass_fail_cell_color(actual, predicted)

        actual_index = VALID_LABELS.index(actual) if actual in VALID_LABELS else None
        predicted_index = VALID_LABELS.index(predicted) if predicted in VALID_LABELS else None
        label_difference = abs(actual_index - predicted_index) if actual_index is not None and predicted_index is not None else None
        if label_difference == 0:
            return 'green'
        elif label_difference == 1:
            return 'yellow'
        else:
            return 'red'

    def _rubric_to_html_table(self, rubric):
        parsed_rubric = list(csv.reader(io.StringIO(rubric)))

        header_row = parsed_rubric.pop(0)
        header_html = ''.join([f'<th>{header}</th>' for header in header_row])

        rows_html = ''
        for row in parsed_rubric:
            rows_html += '<tr>'
            for cell in row:
                rows_html += f'<td>{cell}</td>'
            rows_html += '</tr>'

        return f'''
        <table border="1">
          <thead>
            <tr>{header_html}</tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>
        '''

    def _calculate_accuracy_color(self, percentage):
        intensity = int((percentage - 50) * 5.1)
        if percentage >= 50:
            return f'rgb({255 - intensity}, 255, {255 - intensity})'
        else:
            return f'rgb(255, {intensity + 200}, {intensity + 200})'

    def _generate_accuracy_table(self, accuracy_by_criteria):
        accuracy_table = '<table border="1">'
        accuracy_table += '<tr><th>Key Concept</th><th>Accuracy</th></tr>'
        for criteria, accuracy in accuracy_by_criteria.items():
            color = self._calculate_accuracy_color(accuracy)
            accuracy_table += f'<tr><td>{criteria}</td><td style="background-color: {color};">{int(accuracy)}%</td></tr>'
        accuracy_table += '</table>'
        return accuracy_table

    def _generate_confusion_table(self, confusion_matrix, labels):
        confusion_table = '<table border="1">'
        confusion_table += f'<tr><td colspan="2" rowspan="2"></td><th colspan="{len(labels)}" scope="colgroup" style="text-align: center">Predicted (AI)</th></tr>' #blank corner
        confusion_table += '<tr>'
        for label in labels:
            confusion_table += f'<td>{label}</td>'
        confusion_table += '</tr>'
        confusion_table += f'<tr><th rowspan="{len(labels)+1}" scope="rowgroup">Actual<br>(human)</th>'
        for label, row in zip(labels, confusion_matrix):
            confusion_table += f'<tr><td>{label}</td>'
            for cell in row:
                confusion_table += f'<td style="text-align: center">{int(cell)}</td>'
            confusion_table += '</tr>'
        confusion_table += '</table>'
        return confusion_table

    def _label_to_number(self, label):
        if 'Extensive' in label:
            return 3
        elif 'Convincing' in label:
            return 2
        elif 'Limited' in label:
            return 1

        return 0

    def _key_concept_to_filename(self, key_concept):
        ret = re.sub(r'[^\w\s]', '', key_concept)
        ret = re.sub(r'\s+', '-', ret)
        ret = re.sub(r'^-+|-+$', '', ret)
        return ret.lower()

    def generate_csv_output(self, output_path, prompt, rubric, accuracy=None, predicted_labels=None, actual_labels=None, is_pass_fail=False, accuracy_by_criteria=None, errors=[], input_params={}, confusion_by_criteria=None, overall_confusion=None, label_names=None):
        # Note: We open the CSV file with the newlines turned off as required by CSV writing

        # Keeps track of the rubric changes
        rubric_hash = hashlib.sha1(rubric.encode('utf-8')).hexdigest()

        # Keeps track of prompt changes
        prompt_hash = hashlib.sha1(prompt.encode('utf-8')).hexdigest()

        # String to append based on pass/fail vs. exact match
        matching_type = "partial" if is_pass_fail else "exact"

        # Get the list of key concepts
        key_concepts = list(map(lambda label: label['Key Concept'], list(predicted_labels.values())[0]))

        # Reform accuracy to something writable
        accuracy = 'NaN' if accuracy is None or math.isnan(accuracy) else str(accuracy)

        output_file = os.path.join(output_path, f"{input_params['lesson_name']}-{matching_type}-metadata.csv")
        with open(output_file, 'w+', newline='') as file:
            csv_writer = csv.writer(file)

            # Write Header
            csv_writer.writerow(["RUBRIC_HASH", "PROMPT_HASH", "DATE", "IS_PASS_FAIL", "ERRORS", "ACCURACY"])

            # Write data
            is_pass_fail_value = "TRUE" if is_pass_fail else "FALSE"
            csv_writer.writerow([rubric_hash, prompt_hash, datetime.now().isoformat(), is_pass_fail_value, ';'.join(errors), accuracy])

        # Write sample report and aggregate
        output_file = os.path.join(output_path, f"{input_params['lesson_name']}-sample-accuracy.csv")
        with open(output_file, 'w+', newline='') as file:
            csv_writer = csv.writer(file)

            # Write Header
            csv_writer.writerow(["STUDENT_ID", "LEARNING_GOAL", "ACTUAL", "PREDICTED", "PASS_FAIL_DIFF", "DIFF"])

            # Go through each student and each label
            for student_id, labels in predicted_labels.items():
                for label in labels:
                    criteria = label['Key Concept']
                    actual = actual_labels[student_id][criteria]
                    predicted = label['Label']
                    diff = self._label_to_number(predicted) - self._label_to_number(actual)
                    pass_fail_diff = (self._label_to_number(predicted) // 2) - (self._label_to_number(actual) // 2)
                    csv_writer.writerow([student_id, criteria, actual, predicted, pass_fail_diff, diff])

        output_file = os.path.join(output_path, f"{input_params['lesson_name']}-{matching_type}-accuracy.csv")
        with open(output_file, 'w+', newline='') as file:
            csv_writer = csv.writer(file)

            # Write Header
            csv_writer.writerow(["LEARNING_GOAL", "ACCURACY"])

            # Write the overall accuracy (repeated from the metadata report)
            csv_writer.writerow(["OVERALL", accuracy])

            # For each learning goal, print the accuracy
            for key_concept in key_concepts:
                cur_accuracy = accuracy_by_criteria.get(key_concept)
                cur_accuracy = 'NaN' if cur_accuracy is None or math.isnan(cur_accuracy) else str(cur_accuracy)
                csv_writer.writerow([key_concept, cur_accuracy])

        labels = ["EXTENSIVE", "CONVINCING", "LIMITED", "NO"]

        # First write confusion matrix for all goals
        output_file = os.path.join(output_path, f"{input_params['lesson_name']}-{matching_type}-confusion.csv")
        with open(output_file, 'w+', newline='') as file:
            csv_writer = csv.writer(file)

            # Write Header
            if is_pass_fail:
                csv_writer.writerow(["KEY_CONCEPT", "TRUE_POSITIVE", "FALSE_NEGATIVE", "FALSE_POSITIVE", "TRUE_NEGATIVE"])
            else:
                # Yield a permutation of all labels to form the header
                items = list(map(lambda lst: '/'.join(lst), product(labels, labels)))
                csv_writer.writerow(["KEY_CONCEPT", *items])

            # A 'chain' just flattens the 2d matrix into the row-ordered list
            # Write all the values in the overall matrix into the CSV
            csv_writer.writerow(["OVERALL", *list(chain(*overall_confusion))])

            # Write a row for each concept as well
            for key_concept, confusion_matrix in confusion_by_criteria.items():
                csv_writer.writerow([key_concept, *list(chain(*confusion_matrix))])

        # Write learning goal accuracy reports
        for key_concept in key_concepts:
            slug = self._key_concept_to_filename(key_concept)
            output_file = os.path.join(output_path, f"{input_params['lesson_name']}-sample-accuracy-{slug}.csv")

            with open(output_file, 'w+', newline='') as file:
                csv_writer = csv.writer(file)

                # Write Header
                csv_writer.writerow(["STUDENT_ID", "ACTUAL", "PREDICTED", "PASS_FAIL_DIFF", "DIFF"])

                # Search the report data for just info relevant to this key concept
                for student_id, labels in predicted_labels.items():
                    for label in labels:
                        criteria = label['Key Concept']
                        if criteria != key_concept:
                            continue

                        actual = actual_labels[student_id][criteria]
                        predicted = label['Label']
                        diff = self._label_to_number(predicted) - self._label_to_number(actual)
                        pass_fail_diff = (self._label_to_number(predicted) // 2) - (self._label_to_number(actual) // 2)
                        csv_writer.writerow([student_id, actual, predicted, pass_fail_diff, diff])

    def generate_html_output(self, output_file, prompt, rubric, accuracy=None, predicted_labels=None, actual_labels=None, is_pass_fail=False, accuracy_by_criteria=None, errors=[], input_params={}, confusion_by_criteria=None, overall_confusion=None, label_names=None, prefix='sample_code'):
        link_base_url = f'file://{os.getcwd()}/{prefix}'
        title_suffix = 'pass-fail' if is_pass_fail else 'exact-match'
        doc_title = f"{input_params['lesson_name']}-{title_suffix}"

        with open(output_file, 'w+') as file:
            file.write('<!DOCTYPE html>\n')
            file.write('<html lang="en">\n')
            file.write('<head>\n')
            file.write('  <meta charset="UTF-8">\n')
            file.write('  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
            file.write(f'  <title>{doc_title}</title>\n')
            file.write('</head>\n')
            file.write('<body style="-webkit-print-color-adjust: exact;">\n')
            file.write('  <h2>Prompt:</h2>\n')
            file.write(f'  <pre>{prompt}</pre>\n')
            file.write('  <h2>Rubric:</h2>\n')
            file.write(self._rubric_to_html_table(rubric) + '\n')

            file.write('  <h2>Input Params:</h2>\n')
            file.write(f'  <pre>{json.dumps(input_params, indent=2)}</pre>\n')

            if len(errors) > 0:
                file.write(f'  <h2 style="color: red">Errors: {len(errors)}</h2>\n')
                file.write(f'  <p style="color: red">{", ".join(errors)} failed to load</p>\n')

            accuracy = 'N/A' if accuracy is None or math.isnan(accuracy) else f'{int(accuracy)}%'
            report_type = 'Pass/Fail' if is_pass_fail else 'Exact Match'
            file.write(f'  <h2>Overall Accuracy ({report_type}): {accuracy}</h2>\n')
            
            if accuracy_by_criteria is not None:
                file.write('  <h2>Accuracy by Key Concept:</h2>\n')
                file.write(self._generate_accuracy_table(accuracy_by_criteria) + '\n')

            if overall_confusion is not None and label_names is not None:
                file.write('  <h2>Overall Confusion:</h2>\n')
                file.write(self._generate_confusion_table(overall_confusion, label_names) + '\n')

            if confusion_by_criteria is not None and label_names is not None:
                file.write('  <h2>Confusion by Key Concept:</h2>\n')
                for criteria in confusion_by_criteria:
                    file.write(f'  <h3>Confusion for {criteria}:</h3>\n')
                    file.write(self._generate_confusion_table(confusion_by_criteria[criteria], label_names) + '\n\n')

            if predicted_labels is not None:
                file.write('  <h2>Labels by student:</h2>\n')
                for student_id, labels in predicted_labels.items():
                    file.write(f'  <h3>Student: {student_id}</h3>\n')
                    file.write(f'  <a href="{link_base_url}/{student_id}.js">{student_id}.js</a>\n')
                    file.write('  <table border="1">\n')
                    file.write('    <tr><th>Criteria</th><th>Observations</th><th>Evidence</th><th>Actual Label (human)</th><th>Predicted Label (AI)</th><th>Reason</th></tr>\n')
                    for label in labels:
                        criteria = label['Key Concept']
                        observations = label['Observations']
                        evidence = label.get('Evidence', '')
                        actual = actual_labels[student_id][criteria]
                        predicted = label['Label']
                        reason = label['Reason']
                        cell_color = self._compute_predicted_cell_color(predicted, actual, is_pass_fail)
                        file.write(f'    <tr><td>{criteria}</td><td>{observations}</td><td>{evidence}</td><td>{actual}</td><td style="background-color: {cell_color};">{predicted}</td><td>{reason}</td></tr>\n')
                    file.write('  </table>\n')

            file.write('</body>\n')
            file.write('</html>\n')

    @staticmethod
    def accurate_pass_fail(actual_label, predicted_label):
        return PASSING_LABELS.count(actual_label) == PASSING_LABELS.count(predicted_label)
