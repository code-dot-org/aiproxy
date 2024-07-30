import os
import json
import re
import csv
import time
import requests
import logging
import boto3
from threading import Lock

from typing import List, Dict, Any
from lib.assessment.config import VALID_LABELS, OPENAI_API_TIMEOUT
from lib.assessment.code_feature_extractor import CodeFeatures
from lib.assessment.decision_trees import DecisionTrees

boto3.set_stream_logger('botocore', level='INFO')

from io import StringIO

class InvalidResponseError(Exception):
    pass

class RequestTooLargeError(Exception):
    pass

class OpenaiServerError(Exception):
    pass

class BedrockServerError(Exception):
    pass

class Label:
    _bedrock_client = None
    _bedrock_lock = Lock()

    def __init__(self):
        pass

    # Check to ensure that student project is not blank. Assessment is statically generated for blank code.
    def test_for_blank_code(self, rubric, student_code, student_id):
        rubric_key_concepts = list(set(row['Key Concept'] for row in csv.DictReader(rubric.splitlines())))

        # Test for blank code
        if student_code.strip() == "":
            # Blank code should return No Evidence
            return {
                'metadata': {
                    'agent': 'static',
                    'student_id': student_id,
                },
                'data': list(
                    map(
                        lambda key_concept: {
                            "Label": "No Evidence",
                            "Key Concept": key_concept,
                            "Observations": "The program is empty.",
                            "Evidence": "",
                            "Reason": "The program is empty.",
                        },
                        rubric_key_concepts
                    )
                )
            }

        # Code is not blank
        return None
    
    def cfe_label_student_work(self, rubric, student_code, code_feature_extractor, lesson):

        # Filter rubric to return only learning goals listed for code feature extractor
        learning_goals = [row for row in csv.DictReader(rubric.splitlines()) if row["Key Concept"] in code_feature_extractor]

        # Prep output data
        results = {"metadata": {"agent": "code feature extractor"},"data": []}

        # Extract features from student code
        cfe = CodeFeatures()
        cfe.extract_features(student_code)

        # Send extracted features through decision tree for each learning goal with CFE enabled
        for learning_goal in learning_goals:
            dt = DecisionTrees()
            dt.assess(cfe.features, learning_goal, lesson)
            results["data"].append({"Label": dt.assessment,
                                    "Key Concept": learning_goal["Key Concept"],
                                    "Observations": cfe.features,
                                    "Reason": learning_goal[dt.assessment] if dt.assessment else '',
                                    "Evidence": dt.evidence,
                                        })

        return results

    def ai_label_student_work(self, prompt, rubric, student_code, student_id, examples=[], num_responses=0, temperature=0.0, llm_model="", response_type='tsv'):
        if llm_model.startswith("gpt"):
            return self.openai_label_student_work(prompt, rubric, student_code, student_id, examples=examples, num_responses=num_responses, temperature=temperature, llm_model=llm_model, response_type=response_type)
        elif llm_model.startswith("bedrock.meta"):
            return self.bedrock_meta_label_student_work(prompt, rubric, student_code, student_id, examples=examples, num_responses=num_responses, temperature=temperature, llm_model=llm_model)
        elif llm_model.startswith("bedrock.anthropic"):
            return self.bedrock_anthropic_label_student_work(prompt, rubric, student_code, student_id, examples=examples, num_responses=num_responses, temperature=temperature, llm_model=llm_model)
        else:
            raise Exception("Unknown model: {}".format(llm_model))

    def bedrock_anthropic_label_student_work(self, prompt, rubric, student_code, student_id, examples=[], num_responses=0, temperature=0.0, llm_model=""):
        bedrock = boto3.client(service_name='bedrock-runtime')

        # strip 'bedrock.' from the model name
        bedrock_model = llm_model[8:]
        if not bedrock_model.startswith("anthropic."):
            raise Exception(f"Error parsing llm_model: {llm_model} bedrock_model: {bedrock_model}")

        anthropic_prompt = self.compute_anthropic_prompt(prompt, rubric, student_code, examples=examples)
        if "claude-3" in bedrock_model:
            body = json.dumps({"anthropic_version": "bedrock-2023-05-31",
                               "max_tokens": 4000,
                               "messages": [{"role": "user",
                                             "content": [{"type": "text",
                                                          "text": anthropic_prompt}
                                                        ]
                                            }]
                              })
        else:
            body = json.dumps({
                "prompt": anthropic_prompt,
                "max_tokens_to_sample": 4000,
                "temperature": temperature,
                # "top_p": 0.9,
            })
        accept = 'application/json'
        content_type = 'application/json'
        response = bedrock.invoke_model(body=body, modelId=bedrock_model, accept=accept, contentType=content_type)

        if response['ResponseMetadata']['HTTPStatusCode'] == 500:
            logging.warning(f"{student_id} Error calling the API: {response['ResponseMetadata']['HTTPStatusCode']}")
            logging.warning(f"{student_id} Response body: {response['body']}")
            raise BedrockServerError(f"Error calling Bedrock Anthropic API: {response['body']}")
        elif response['ResponseMetadata']['HTTPStatusCode'] != 200:
            logging.error(f"{student_id} Error calling the API: {response['ResponseMetadata']['HTTPStatusCode']}")
            logging.error(f"{student_id} Response body: {response['body']}")
            return None

        response_body = json.loads(response.get('body').read())

        data = self.get_response_data_if_valid(response_body, rubric, student_id, response_type='json')

        return {
            'metadata': {
                'agent': 'anthropic',
                'request': body,
            },
            'data': data,
        }

    def bedrock_meta_label_student_work(self, prompt, rubric, student_code, student_id, examples=[], num_responses=0, temperature=0.0, llm_model=""):
        bedrock = self.get_bedrock_client(student_id)

        # strip 'bedrock.' from the model name
        bedrock_model = llm_model[8:]

        # raise if the model name does not start with 'meta'
        if not bedrock_model.startswith("meta."):
            raise Exception(f"Error parsing llm_model: {llm_model} bedrock_model: {bedrock_model}")

        meta_prompt = self.compute_meta_prompt(prompt, rubric, student_code, examples=examples)
        body = json.dumps({
            "prompt": meta_prompt,
            "max_gen_len": 1536,
            "temperature": temperature,
        })
        accept = 'application/json'
        content_type = 'application/json'
        response = bedrock.invoke_model(body=body, modelId=bedrock_model, accept=accept, contentType=content_type)

        response_body = json.loads(response.get('body').read())
        generation = response_body.get('generation')

        data = self.get_response_data_if_valid(generation, rubric, student_id, response_type='json')

        return {
            'metadata': {
                'agent': 'meta',
                'request': body,
            },
            'data': data,
        }

    # make sure only one client is created, otherwise we sometimes end up with a corrupt .aws/credentials file
    # when rubric tester calls this function multiple times in parallel.
    @classmethod
    def get_bedrock_client(cls, student_id):
        if cls._bedrock_client is None:
            with cls._bedrock_lock:
                if cls._bedrock_client is None:
                    # print the student_id so we can debug if we see multiple clients being created
                    logging.info(f"creating bedrock client. student_id: {student_id}")
                    cls._bedrock_client = boto3.client(service_name='bedrock-runtime')
        return cls._bedrock_client

    def openai_label_student_work(self, prompt, rubric, student_code, student_id, examples=[], num_responses=0, temperature=0.0, llm_model="", response_type='tsv'):
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
        response = requests.post(api_url, headers=headers, json=data, timeout=OPENAI_API_TIMEOUT)

        if response.status_code == 500:
            logging.warning(f"{student_id} Error calling the API: {response.status_code}")
            logging.warning(f"{student_id} Response body: {response.text}")
            raise OpenaiServerError(f"Error calling OpenAI API: {response.text}")
        elif self._openai_context_length_exceeded(response):
            message = response.json().get('error', {}).get('message')
            logging.warning(f"{student_id} Request too large: {message}")
            raise RequestTooLargeError(f"{student_id} {message}")
        elif response.status_code != 200:
            logging.error(f"{student_id} Error calling the API: {response.status_code}")
            logging.error(f"{student_id} Response body: {response.text}")
            return None

        info = response.json()

        response_data = self.response_data_from_choices(info, rubric, student_id, response_type=response_type)

        return {
            'metadata': {
                'agent': 'openai',
                'usage': info['usage'],
                'request': data,
            },
            'data': response_data,
        }

    def _openai_context_length_exceeded(self, response):
        return (
            response.status_code == 400 and
            response.headers.get('Content-Type') == 'application/json' and
            response.json().get('error', {}).get('code') == 'context_length_exceeded'
        )

    def label_student_work(self, prompt, rubric, student_code, student_id, examples=[], use_cached=False, write_cached=False, num_responses=0, temperature=0.0, llm_model="", remove_comments=False, response_type='tsv', cache_prefix="", code_feature_extractor=None, lesson=None):
        if use_cached and os.path.exists(os.path.join(cache_prefix, f"cached_responses/{student_id}.json")):
            with open(os.path.join(cache_prefix, f"cached_responses/{student_id}.json"), 'r') as f:
                return json.load(f)

        # We will record the time it takes to perform the assessment
        start_time = time.time()

        # Sanitize student code
        student_code = self.sanitize_code(student_code, remove_comments=remove_comments)

        # Test for empty student code file
        blank_code_result = self.test_for_blank_code(rubric, student_code, student_id)

        # If code is blank, return results
        if blank_code_result:
            blank_code_result["metadata"]["time"] = time.time() - start_time
            return blank_code_result

        # If student code is not blank, check for learning goals flagged for code feature extractor
        # Send student code and learning goals(s) for feature extraction and labeling.
        cfe_results = None
        if code_feature_extractor:
            cfe_results = self.cfe_label_student_work(rubric, student_code, code_feature_extractor, lesson)
        
        # Send data to LLM for assessment
        try:
            ai_result = self.ai_label_student_work(prompt, rubric, student_code, student_id, examples=examples, num_responses=num_responses, temperature=temperature, llm_model=llm_model, response_type=response_type)
        except requests.exceptions.ReadTimeout as exception:
            logging.warning(f"{student_id} request timed out in {(time.time() - start_time):.0f} seconds.")
            raise exception

        # No assessment was possible
        if ai_result is None:
            raise Exception("AI assessment failed.")

        elapsed = time.time() - start_time
        tokens = ai_result.get('metadata', {}).get('usage', {}).get('total_tokens', 0)
        logging.info(f"{student_id} request succeeded in {elapsed:.0f} seconds. {tokens} tokens used.")

        # Craft the response dictionary
        response = {
            'metadata': {
                'time': elapsed,
                'student_id': student_id,
            },
            'data': ai_result.get('data', []),
        }
        response['metadata'].update(ai_result.get('metadata', {}))

        # If any learning goals were assessed by the code feature extractor, replace the AI results with cfe results
        if cfe_results:
            response["metadata"]["agent"] += ", " + cfe_results["metadata"]["agent"]
            new_data = list(filter(lambda assessment: assessment["Key Concept"] not in code_feature_extractor, response["data"]))
            new_data.extend(cfe_results["data"])
            response["data"] = new_data

        # only write to cache if the response is valid
        if write_cached and ai_result:
            with open(os.path.join(cache_prefix, f"cached_responses/{student_id}.json"), 'w+') as f:
                json.dump(response, f, indent=4)

        return response

    def remove_js_comments(self, code):
        # This regex pattern captures three groups:
        # 1) Single or double quoted strings
        # 2) Multi-line comments
        # 3) Single-line comments
        pattern = r'(".*?[^\\]"|\'.*?[^\\]\'|/\*.*?\*/|//.*?$)'

        def replacer(match):
            # If the match is a string, return it unchanged
            if match.group(0).startswith(("'", '"')):
                return match.group(0)

            # Otherwise, it's a comment, so remove it
            return ''

        return re.sub(pattern, replacer, code, flags=re.DOTALL | re.MULTILINE)

    def sanitize_code(self, student_code, remove_comments=False):
        # Remove comments
        if remove_comments:
            student_code = self.remove_js_comments(student_code)

        return student_code

    def response_data_from_choices(self, info, rubric, student_id, response_type='tsv'):
        max_index = len(info['choices']) - 1
        response_data_choices = []
        for index, choice in enumerate(info['choices']):
            # If all choices result in an InvalidResponseError, reraise the last one.
            reraise = len(response_data_choices) == 0 and index == max_index

            if choice['message']['content']:
                response_data = self.get_response_data_if_valid(choice, rubric, student_id, choice_index=index, reraise=reraise, response_type=response_type)
                if response_data:
                    response_data_choices.append(response_data)

        if len(response_data_choices) == 0:
            raise InvalidResponseError("No valid responses. An InvalidResponseError should have been raised earlier.")
        elif len(response_data_choices) == 1:
            response_data = response_data_choices[0]
        else:
            response_data = self.get_consensus_response(response_data_choices, student_id)
        return response_data

    def compute_anthropic_prompt(self, prompt, rubric, student_code, examples=[]):
        return f"Human:\n{prompt}\n\nRubric:\n{rubric}\n\nStudent Code:\n{student_code}\n\nAssistant:\n"

    def compute_meta_prompt(self, prompt, rubric, student_code, examples=[]):
        # here is the documentation for code llama and llama 2 prompting:
        # https://huggingface.co/blog/llama2#how-to-prompt-llama-2
        # https://huggingface.co/blog/codellama#conversational-instructions
        #
        # that documentation says that the prompt should be in the following format:
        # return f"<s>[INST]<<SYS>>{prompt}<</SYS>>\n\nRubric:\n{rubric}\n\nStudent Code:\n{student_code}\n\nEvaluation (JSON):\n[/INST]"
        #
        # but that format does not consistently lead to valid JSON output. The following format works more reliably:
        return f"[INST]{prompt}[/INST]\n\nRubric:\n{rubric}\n\nStudent Code:\n{student_code}\n\nEvaluation (JSON):\n"

    def compute_messages(self, prompt, rubric, student_code, examples=[]):
        messages = [
            {'role': 'system', 'content': f"{prompt}\n\nRubric:\n{rubric}"}
        ]
        for example_js, example_rubric in examples:
            messages.append({'role': 'user', 'content': example_js})
            messages.append({'role': 'assistant', 'content': example_rubric})
        messages.append({'role': 'user', 'content': student_code})
        return messages

    def get_response_data_if_valid(self, choice, rubric, student_id, choice_index=None, reraise=False, response_type='tsv'):
        response_text = None
        finish_reason = None
        if 'message' in choice.keys(): # OpenAI response
            response_text = choice['message']['content']
            finish_reason = choice['finish_reason']
        elif 'completion' in choice.keys(): # Claude 2 response
            response_text = choice['completion']
            finish_reason = choice['stop_reason']
        elif 'content' in choice.keys(): # Claude 3 response
            response_text = choice['content'][0]['text']
            finish_reason = choice['stop_reason']

        try:
            choice_text = f"Choice {choice_index}: " if choice_index is not None else ''
            if not response_text:
                raise InvalidResponseError("empty response")
            text = response_text.strip()

            if response_type == 'json':
                response_data = self.parse_json_response(text, student_id, finish_reason=finish_reason)
            elif response_type == 'tsv':
                response_data = self.parse_non_json_response(text)
            else:
                raise ValueError(f"Invalid response type: {response_type}")

            if type(response_data) == 'list' and "Key Concept" in response_data[0]:
                for i in range(len(response_data)):
                    response_data[i]["Key Concept"] = response_data[i]["Key Concept"].replace("\"", "“", 1).replace("\"", "”", 1)

            self._sanitize_server_response(response_data)
            self._validate_server_response(response_data, rubric)
            return [row for row in response_data]
        except InvalidResponseError as e:
            logging.info(f"{student_id} {choice_text} Invalid response: {str(e)}\n{response_text}")
            if reraise:
                raise e
            return None
        except RequestTooLargeError as e:
            logging.warning(f"{student_id} {choice_text} Request too large: {str(e)}")
            if reraise:
                raise e

    # gpt-4-0613 has a context window of 8192 tokens, which is the limit for input + output tokens.
    # If the json in the response is unparseable, and the llm says the response was truncated due to length,
    # then assume the reason for the error is because the input was too large to leave enough remaining tokens
    # for a valid response.
    def parse_json_response(self, response_text, student_id, finish_reason):
        # capture all data from the first '[' to the last ']', inclusive
        match = re.search(r'(\[.*\])', response_text,re.DOTALL)
        if not match:
            if finish_reason == 'length' or finish_reason == 'max_tokens':
                raise RequestTooLargeError(f"{student_id}: no valid JSON data")
            raise InvalidResponseError(f"no valid JSON data:\n{response_text}")
        json_text = match.group(1)

        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            if finish_reason == 'length' or finish_reason == 'max_tokens':
                raise RequestTooLargeError(f"{student_id}: JSON decoding error")
            raise InvalidResponseError(f"JSON decoding error: {e}\n{json_text}")

        return data

    # parse response data in tsv, csv or markdown format.
    def parse_non_json_response(self, text):
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

                response_data = list(csv.DictReader(StringIO(text), delimiter='|'))
            else:
                # Let's assume it is CSV
                logging.info("response had no tabs so is not tsv, delimiting by ','")
                response_data = list(csv.DictReader(StringIO(text), delimiter=','))
        else:
            # Let's assume it is TSV
            response_data = list(csv.DictReader(StringIO(text), delimiter='\t'))
        return response_data

    def _sanitize_server_response(self, response_data):
        # Strip whitespace and quotes from fields
        for row in response_data:
            for key in list(row.keys()):
                if isinstance(row[key], str):
                    row[key] = row[key].strip().strip('"')

                if isinstance(key, str):
                    if key.strip() != key:
                        row[key.strip()] = row[key]
                        del row[key]

        # Remove rows that don't start with reasonable things
        for row in response_data:
            if "Key Concept" in row:
                if not row["Key Concept"][0:1].isalnum():
                    response_data.remove(row)

        for row in response_data:
            if "Grade" in row.keys():
                row['Label'] = row['Grade']
                del row['Grade']

    def _validate_server_response(self, response_data, rubric):
        expected_columns = ["Key Concept", "Observations", "Label", "Reason"]

        rubric_key_concepts = list(set(row['Key Concept'] for row in csv.DictReader(rubric.splitlines())))

        if not all((set(row.keys()) & set(expected_columns)) == set(expected_columns) for row in response_data):
            for row in response_data:
                unexpected_columns = set(row.keys()) - set(expected_columns)
                missing_columns = set(expected_columns) - set(row.keys())
                raise InvalidResponseError(f'incorrect column names. unexpected: {unexpected_columns} missing: {missing_columns}')

        key_concepts_from_response = list(set(row["Key Concept"] for row in response_data))

        if sorted(rubric_key_concepts) != sorted(key_concepts_from_response):
            unexpected_concepts = set(key_concepts_from_response) - set(rubric_key_concepts)
            unexpected_concepts = None if len(unexpected_concepts) == 0 else unexpected_concepts
            missing_concepts = set(rubric_key_concepts) - set(key_concepts_from_response)
            missing_concepts = None if len(missing_concepts) == 0 else missing_concepts
            raise InvalidResponseError(f'unexpected or missing key concept. unexpected: {unexpected_concepts} missing: {missing_concepts}')

        for row in response_data:
            if row['Label'] not in VALID_LABELS:
                raise InvalidResponseError(f"invalid label value: '{row['Label']}'")

    def get_consensus_response(self, choices, student_id):
        from collections import Counter

        key_concept_to_labels = {}
        for choice in choices:
            for row in choice:
                if row['Key Concept'] not in key_concept_to_labels:
                    key_concept_to_labels[row['Key Concept']] = []
                key_concept_to_labels[row['Key Concept']].append(row['Label'])

        key_concept_to_majority_label = {}
        for key_concept, labels in key_concept_to_labels.items():
            majority_label = Counter(labels).most_common(1)[0][0]
            key_concept_to_majority_label[key_concept] = majority_label
            if majority_label != labels[0]:
                logging.info(f"outvoted {student_id} Key Concept: {key_concept} first label: {labels[0]} majority label: {majority_label}")

        key_concept_to_observations = {}
        key_concept_to_evidence = {}
        key_concept_to_reason = {}
        for choice in choices:
            for row in choice:
                key_concept = row['Key Concept']
                if key_concept_to_majority_label[key_concept] == row['Label']:
                    if key_concept not in key_concept_to_observations:
                        key_concept_to_observations[key_concept] = row['Observations']
                        key_concept_to_evidence[key_concept] = row.get('Evidence', '')
                    key_concept_to_reason[key_concept] = row['Reason']

        return [{'Key Concept': key_concept, 'Observations': key_concept_to_observations[key_concept], 'Evidence': key_concept_to_evidence[key_concept], 'Label': label, 'Reason': f"{self.get_consensus_votes(key_concept_to_labels[key_concept])}{key_concept_to_reason[key_concept]}"} for key_concept, label in key_concept_to_majority_label.items()]

    def get_consensus_votes(self, labels):
        # only display votes if there is a disagreement
        if len(set(labels)) == 1:
            return ""
        return f"<b>Votes: [{', '.join(labels)}]</b><br>"
