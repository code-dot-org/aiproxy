import os
import json
import csv
import time
import requests
import logging

from typing import List, Dict, Any
from lib.assessment.config import VALID_GRADES

from io import StringIO

class InvalidResponseError(Exception):
    pass

class Grade:
    def __init__(self):
        pass

    def grade_student_work(self, prompt, rubric, student_code, student_id, examples=[], use_cached=False, write_cached=True, num_responses=0, temperature=0.0, llm_model="", remove_comments=False):
        if use_cached and os.path.exists(f"cached_responses/{student_id}.json"):
            with open(f"cached_responses/{student_id}.json", 'r') as f:
                return json.load(f)

        api_url = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {os.getenv('OPENAI_API_KEY')}"
        }

        # Sanitize student code
        student_code = self.sanitize_code(student_code, remove_comments=remove_comments)

        messages = self.compute_messages(prompt, rubric, student_code, examples=examples)
        data = {
            'model': llm_model,
            'temperature': temperature,
            'messages': messages,
            'n': num_responses,
        }

        start_time = time.time()
        try:
            response = requests.post(api_url, headers=headers, json=data, timeout=120)
        except requests.exceptions.ReadTimeout:
            logging.error(f"{student_id} request timed out in {(time.time() - start_time):.0f} seconds.")
            return None

        if response.status_code != 200:
            logging.error(f"{student_id} Error calling the API: {response.status_code}")
            logging.info(f"{student_id} Response body: {response.text}")
            return None

        info = response.json()
        tokens = info['usage']['total_tokens']
        elapsed = time.time() - start_time
        logging.info(f"{student_id} request succeeded in {elapsed:.0f} seconds. {tokens} tokens used.")

        tsv_data = self.tsv_data_from_choices(info, rubric, student_id)

        # only write to cache if the response is valid
        if write_cached and tsv_data:
            with open(f"cached_responses/{student_id}.json", 'w') as f:
                json.dump(tsv_data, f, indent=4)

        return {
            'metadata': {
              'time': elapsed,
              'student_id': student_id,
              'usage': info['usage'],
              'request': data,
            },
            'data': tsv_data,
        }

    def tsv_data_from_choices(self, info, rubric, student_id):
        tsv_data_choices = [
            self.get_tsv_data_if_valid(choice['message']['content'], rubric, student_id, choice_index=index) for
            index, choice in enumerate(info['choices']) if choice['message']['content']]
        tsv_data_choices = [choice for choice in tsv_data_choices if choice]
        if len(tsv_data_choices) == 0:
            tsv_data = None
        elif len(tsv_data_choices) == 1:
            tsv_data = tsv_data_choices[0]
        else:
            tsv_data = self.get_consensus_response(tsv_data_choices, student_id)
        return tsv_data

    def sanitize_code(self, student_code, remove_comments=False):
        # Remove comments
        if remove_comments:
            student_code = "\n".join(
                list(
                    map(lambda x:
                        x[0:x.index("//")] if "//" in x else x,
                        student_code.split('\n')
                    )
                )
            )

        return student_code

    def compute_messages(self, prompt, rubric, student_code, examples=[]):
        messages = [
            {'role': 'system', 'content': f"{prompt}\n\nRubric:\n{rubric}"}
        ]
        for example_js, example_rubric in examples:
            messages.append({'role': 'user', 'content': example_js})
            messages.append({'role': 'assistant', 'content': example_rubric})
        messages.append({'role': 'user', 'content': student_code})
        return messages

    def get_tsv_data_if_valid(self, response_text, rubric, student_id, choice_index=None):
        choice_text = f"Choice {choice_index}: " if choice_index is not None else ''
        if not response_text:
            logging.error(f"{student_id} {choice_text} Invalid response: empty response")
            return None
        text = response_text.strip()

        # Remove anything up to the first column name
        if "\nKey Concept" in text:
            index = text.index("\nKey Concept")
            text = text[index:].strip()

        # Replace escaped tabs
        if '\\t' in text:
            text = text.replace("\\t", "\t")

        # Replace double tabs... ugh
        text = text.replace("\t\t", "\t")

        # If there is a tab, it is probably TSV
        if '\t' not in text:
            if ' | ' in text:
                # Ok, sometimes it does markdown sequence... which means it does '|'
                # as a delimiter and has lines with '---' in them
                lines = text.split('\n')
                lines = list(filter(lambda x: "---" not in x, lines))
                text = "\n".join(lines)
                logging.info("response was markdown and not tsv, delimiting by '|'")

                tsv_data = list(csv.DictReader(StringIO(text), delimiter='|'))
            else:
                # Let's assume it is CSV
                logging.info("response had no tabs so is not tsv, delimiting by ','")
                tsv_data = list(csv.DictReader(StringIO(text), delimiter=','))
        else:
            # Let's assume it is TSV
            tsv_data = list(csv.DictReader(StringIO(text), delimiter='\t'))

        try:
            self.sanitize_server_response(tsv_data)
            self.validate_server_response(tsv_data, rubric)
            return [row for row in tsv_data]
        except InvalidResponseError as e:
            logging.error(f"{student_id} {choice_text} Invalid response: {str(e)}\n{response_text}")
            return None

    def parse_tsv(self, tsv_text):
        rows = tsv_text.split("\n")
        header = rows.pop(0).split("\t")
        return [dict(zip(header, row.split("\t"))) for row in rows]

    def sanitize_server_response(self, tsv_data):
        if not isinstance(tsv_data, list):
            return

        # Strip whitespace and quotes from fields
        for row in tsv_data:
            for key in list(row.keys()):
                if isinstance(row[key], str):
                    row[key] = row[key].strip().strip('"')

                if isinstance(key, str):
                    if key.strip() != key:
                        row[key.strip()] = row[key]
                        del row[key]

        # Remove rows that don't start with reasonable things
        for row in tsv_data:
            if "Key Concept" in row:
                if not row["Key Concept"][0:1].isalnum():
                    tsv_data.remove(row)

    def validate_server_response(self, tsv_data, rubric):
        expected_columns = ["Key Concept", "Observations", "Grade", "Reason"]

        rubric_key_concepts = list(set(row['Key Concept'] for row in csv.DictReader(rubric.splitlines())))

        if not isinstance(tsv_data, list):
            raise InvalidResponseError('invalid format')

        if not all((set(row.keys()) & set(expected_columns)) == set(expected_columns) for row in tsv_data):
            unexpected_columns = set(row.keys()) - set(expected_columns)
            missing_columns = set(expected_columns) - set(row.keys())
            raise InvalidResponseError('incorrect column names. unexpected: {unexpected_columns} missing: {missing_columns}')

        key_concepts_from_response = list(set(row["Key Concept"] for row in tsv_data))
        if sorted(rubric_key_concepts) != sorted(key_concepts_from_response):
            unexpected_concepts = set(key_concepts_from_response) - set(rubric_key_concepts)
            missing_concepts = set(rubric_key_concepts) - set(key_concepts_from_response)
            raise InvalidResponseError(f'unexpected or missing key concept. unexpected: {unexpected_concepts} missing: {missing_concepts}')

        for row in tsv_data:
            if row["Grade"] not in VALID_GRADES:
                raise InvalidResponseError(f"invalid grade value: '{row['Grade']}'")

    def get_consensus_response(self, choices, student_id):
        from collections import Counter

        key_concept_to_grades = {}
        for choice in choices:
            for row in choice:
                if row['Key Concept'] not in key_concept_to_grades:
                    key_concept_to_grades[row['Key Concept']] = []
                key_concept_to_grades[row['Key Concept']].append(row['Grade'])

        key_concept_to_majority_grade = {}
        for key_concept, grades in key_concept_to_grades.items():
            majority_grade = Counter(grades).most_common(1)[0][0]
            key_concept_to_majority_grade[key_concept] = majority_grade
            if majority_grade != grades[0]:
                logging.info(f"outvoted {student_id} Key Concept: {key_concept} first grade: {grades[0]} majority grade: {majority_grade}")

        key_concept_to_observations = {}
        key_concept_to_reason = {}
        for choice in choices:
            for row in choice:
                key_concept = row['Key Concept']
                if key_concept_to_majority_grade[key_concept] == row['Grade']:
                    if key_concept not in key_concept_to_observations:
                        key_concept_to_observations[key_concept] = row['Observations']
                    key_concept_to_reason[key_concept] = row['Reason']

        return [{'Key Concept': key_concept, 'Observations': key_concept_to_observations[key_concept], 'Grade': grade, 'Reason': f"<b>Votes: [{', '.join(key_concept_to_grades[key_concept])}]</b><br>{key_concept_to_reason[key_concept]}"} for key_concept, grade in key_concept_to_majority_grade.items()]
