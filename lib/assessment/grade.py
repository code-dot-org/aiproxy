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

    # This will take a rubric and student code and it will perform static checks on the code.
    #
    # For instance, it will determine a blank project should receive a No Evidence score for
    # all items in the rubric.
    def statically_grade_student_work(self, rubric, student_code, student_id, examples=[]):
        rubric_key_concepts = list(set(row['Key Concept'] for row in csv.DictReader(rubric.splitlines())))

        if student_code.strip() == "":
            # Blank code should return No Evidence
            return {
                'metadata': {
                    'agent': 'static',
                },
                'data': list(
                    map(
                        lambda key_concept: {
                            "Grade": "No Evidence",
                            "Key Concept": key_concept,
                            "Observations": "The program is empty.",
                            "Reason": "The program is empty.",
                        },
                        rubric_key_concepts
                    )
                )
            }

        # We can't assess this statically
        return None

    def ai_grade_student_work(self, prompt, rubric, student_code, student_id, examples=[], num_responses=0, temperature=0.0, llm_model=""):
        # Determine the OpenAI URL and headers
        api_url = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {os.getenv('OPENAI_API_KEY')}"
        }

        # Compute the input we are giving to OpenAI
        messages = self.compute_messages(prompt, rubric, student_code, examples=examples)
        data = {
            'model': llm_model,
            'temperature': temperature,
            'messages': messages,
            'n': num_responses,
        }

        # Post to the AI service
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

        tsv_data_choices = [self.get_tsv_data_if_valid(choice['message']['content'], rubric, student_id, choice_index=index) for index, choice in enumerate(info['choices']) if choice['message']['content']]
        tsv_data_choices = [choice for choice in tsv_data_choices if choice]

        if len(tsv_data_choices) == 0:
            tsv_data = None
        elif len(tsv_data_choices) == 1:
            tsv_data = tsv_data_choices[0]
        else:
            tsv_data = self.get_consensus_response(tsv_data_choices, student_id)

        return {
            'metadata': {
                'agent': 'openai',
                'usage': info['usage'],
                'request': data,
            },
            'data': tsv_data,
        }

    def grade_student_work(self, prompt, rubric, student_code, student_id, examples=[], use_cached=False, write_cached=True, num_responses=0, temperature=0.0, llm_model="", remove_comments=False):
        if use_cached and os.path.exists(f"cached_responses/{student_id}.json"):
            with open(f"cached_responses/{student_id}.json", 'r') as f:
                return json.load(f)

        # We will record the time it takes to perform the assessment
        start_time = time.time()

        # Sanitize student code
        student_code = self.sanitize_code(student_code, remove_comments=remove_comments)

        # Try static analysis options (before invoking AI)
        result = self.statically_grade_student_work(rubric, student_code, student_id, examples=examples)

        # If it gives back a response, right now assume it is complete and do not perform an AI analysis
        # We may want to, in the future, gauge how many of the concepts it has graded and let AI fill in the blanks
        # Right now, however, only if there is no result, we try the AI for assessment
        if result is None:
            result = self.ai_grade_student_work(prompt, rubric, student_code, student_id, examples=examples, num_responses=num_responses, temperature=temperature, llm_model=llm_model)

        # No assessment was possible
        if result is None:
            raise Exception("AI assessment failed.")

        elapsed = time.time() - start_time
        tokens = result.get('metadata', {}).get('usage', {}).get('total_tokens', 0)
        logging.info(f"{student_id} request succeeded in {elapsed:.0f} seconds. {tokens} tokens used.")

        # only write to cache if the response is valid
        if write_cached and tsv_data:
            with open(f"cached_responses/{student_id}.json", 'w') as f:
                json.dump(tsv_data, f, indent=4)

        # Craft the response dictionary
        response = {
            'metadata': {
                'time': elapsed,
                'student_id': student_id,
            },
            'data': result.get('data', []),
        }
        response['metadata'].update(result.get('metadata', {})),
        return response

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
            raise InvalidResponseError('incorrect column names')

        key_concepts_from_response = list(set(row["Key Concept"] for row in tsv_data))
        if sorted(rubric_key_concepts) != sorted(key_concepts_from_response):
            raise InvalidResponseError('invalid or missing key concept')

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
