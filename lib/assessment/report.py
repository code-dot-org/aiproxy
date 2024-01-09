import os
import csv
import io
import json
from typing import List, Dict, Any
from lib.assessment.config import VALID_LABELS

class Report:
    def _compute_pass_fail_cell_color(self, actual, predicted, passing_labels):
        if Report.accurate(actual, predicted, passing_labels):
            return 'green'
        else:
            return 'red'

    def _compute_predicted_cell_color(self, predicted, actual, passing_labels):
        if passing_labels:
            return self._compute_pass_fail_cell_color(actual, predicted, passing_labels)

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

    def generate_html_output(self, output_file, prompt, rubric, accuracy=None, predicted_labels=None, actual_labels=None, passing_labels=None, accuracy_by_criteria=None, errors=[], command_line=None, confusion_by_criteria=None, overall_confusion=None, label_names=None, prefix='sample_code'):
        link_base_url = f'file://{os.getcwd()}/{prefix}'

        with open(output_file, 'w+') as file:
            file.write('<!DOCTYPE html>\n')
            file.write('<html lang="en">\n')
            file.write('<head>\n')
            file.write('  <meta charset="UTF-8">\n')
            file.write('  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
            file.write('  <title>Rubric Test Results</title>\n')
            file.write('</head>\n')
            file.write('<body style="-webkit-print-color-adjust: exact;">\n')
            file.write('  <h2>Prompt:</h2>\n')
            file.write(f'  <pre>{prompt}</pre>\n')
            file.write('  <h2>Rubric:</h2>\n')
            file.write(self._rubric_to_html_table(rubric) + '\n')
            if len(errors) > 0:
                file.write(f'  <h2 style="color: red">Errors: {len(errors)}</h2>\n')
                file.write(f'  <p style="color: red">{", ".join(errors)} failed to load</p>\n')

            if command_line:
                file.write('  <h2>Command Line:</h2>\n')
                file.write(f'  <pre>{command_line}</pre>\n')

            accuracy = 'N/A' if accuracy is None else f'{int(accuracy)}%'
            file.write(f'  <h2>Overall Accuracy: {accuracy}</h2>\n')
            
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
                    file.write('    <tr><th>Criteria</th><th>Observations</th><th>Actual Label (human)</th><th>Predicted Label (AI)</th><th>Reason</th></tr>\n')
                    for label in labels:
                        criteria = label['Key Concept']
                        observations = label['Observations']
                        actual = actual_labels[student_id][criteria]
                        predicted = label['Label']
                        reason = label['Reason']
                        cell_color = self._compute_predicted_cell_color(predicted, actual, passing_labels)
                        file.write(f'    <tr><td>{criteria}</td><td>{observations}</td><td>{actual}</td><td style="background-color: {cell_color};">{predicted}</td><td>{reason}</td></tr>\n')
                    file.write('  </table>\n')

            file.write('</body>\n')
            file.write('</html>\n')

    @staticmethod
    def accurate(actual_label, predicted_label, passing_labels):
        if passing_labels:
            return passing_labels.count(actual_label) == passing_labels.count(predicted_label)
        else:
            return actual_label == predicted_label
