# These routes (/assessment) issue AI driven rubric assessments.
# The /test/assessment will issue a hard-coded AI assessment of a rubric.

from flask import Blueprint, request

import os
import openai
import json
import logging
import requests

from lib.assessment.config import DEFAULT_MODEL

# Our assessment code
from lib.assessment import assess
from lib.assessment.rubric_tester import eval_dataset
from lib.assessment.assess import KeyConceptError
from lib.assessment.label import InvalidResponseError, RequestTooLargeError, OpenaiServerError

assessment_routes = Blueprint('assessment_routes', __name__)

# Submit a rubric assessment
@assessment_routes.route('/assessment', methods=['POST'])
def post_assessment():
    openai.api_key = os.getenv('OPENAI_API_KEY')

    if request.values.get("code", None) == None:
        return "`code` is required", 400

    if request.values.get("prompt", None) == None:
        return "`prompt` is required", 400

    if request.values.get("rubric", None) == None:
        return "`rubric` is required", 400

    examples = json.loads(request.values.get("examples", "[]"))

    try:
        labels = assess.label(
            code=request.values.get("code", ""),
            prompt=request.values.get("prompt", ""),
            rubric=request.values.get("rubric", ""),
            examples=examples,
            api_key=request.values.get("api-key", openai.api_key),
            llm_model=request.values.get("model", DEFAULT_MODEL),
            remove_comments=(request.values.get("remove-comments", "0") != "0"),
            num_responses=int(request.values.get("num-responses", "1")),
            temperature=float(request.values.get("temperature", "0.2")),
            response_type=request.values.get("response-type", "tsv"),
            code_feature_extractor=(request.values.get("code-feature-extractor", None)),
            lesson=(request.values.get("lesson", None))
        )
    except ValueError:
        return "One of the arguments is not parseable as a number", 400
    except RequestTooLargeError as e:
        return str(e), 413
    except InvalidResponseError as e:
        return f'InvalidResponseError: {str(e)}', 400
    except KeyConceptError as e:
        return e, 400
    except OpenaiServerError as e:
        return e, 503
    except requests.exceptions.ReadTimeout as e:
        return f"OpenAI timeout: #{e}: ", 504

    if not isinstance(labels, dict) or not isinstance(labels.get("data"), list):
        return "response from AI or service not valid", 400

    return labels

# Submit a rubric assessment
@assessment_routes.route('/assessment/report', methods=['POST'])
def post_assessment_report():
    openai.api_key = os.getenv('OPENAI_API_KEY')

    if request.values.get("prompt", None) == None:
        return "`prompt` is required", 400

    if request.values.get("rubric", None) == None:
        return "`rubric` is required", 400

    try:
        html = eval_dataset(
            request.values.get("prompt", ""),
            request.values.get("rubric", ""),
            api_key=request.values.get("api-key", openai.api_key),
            llm_model=request.values.get("model", DEFAULT_MODEL),
            num_responses=int(request.values.get("num-responses", "1")),
            temperature=float(request.values.get("temperature", "0.2")),
            remove_comments=(request.values.get("remove-comments", "0") != "0"),
            response_type=request.values.get("response-type", "json"),
            lesson=(request.values.get("lesson", None))
        )
    except ValueError:
        return "One of the arguments is not parseable as a number", 400
    except RequestTooLargeError as e:
        return str(e), 413
    except InvalidResponseError as e:
        return f'InvalidResponseError: {str(e)}', 400
    except KeyConceptError as e:
        return e, 400
    except OpenaiServerError as e:
        return e, 503
    except requests.exceptions.ReadTimeout as e:
        return f"OpenAI timeout: #{e}: ", 504

    if not isinstance(html, str):
        return "response from AI agent not valid", 400

    return html

# Submit a test rubric assessment
@assessment_routes.route('/test/assessment', methods=['GET','POST'])
def test_assessment():
    openai.api_key = os.getenv('OPENAI_API_KEY')
    
    with open('tests/data/u3l23_01.js', 'r') as f:
        code = f.read()

    with open('tests/data/u3l23.txt', 'r') as f:
        prompt = f.read()

    with open('tests/data/u3l23.csv', 'r') as f:
        rubric = f.read()

    try:
        labels = assess.label(
            code=code,
            prompt=prompt,
            rubric=rubric,
            api_key=request.values.get("api-key", openai.api_key),
            llm_model=request.values.get("model", DEFAULT_MODEL),
            remove_comments=(request.values.get("remove-comments", "0") != "0"),
            num_responses=int(request.values.get("num-responses", "1")),
            temperature=float(request.values.get("temperature", "0.2")),
        )
    except ValueError:
        return "One of the arguments is not parseable as a number", 400
    except openai.error.InvalidRequestError as e:
        return str(e), 400

    if not isinstance(labels, dict) or not isinstance(labels.get("data"), list):
        return "response from AI or service not valid", 400

    return labels

# Submit a test rubric assessment for a blank project
@assessment_routes.route('/test/assessment/blank', methods=['GET','POST'])
def test_assessment_blank():
    openai.api_key = os.getenv('OPENAI_API_KEY')

    code = ""

    with open('tests/data/u3l23.txt', 'r') as f:
        prompt = f.read()

    with open('tests/data/u3l23.csv', 'r') as f:
        rubric = f.read()

    try:
        labels = assess.label(
            code=code,
            prompt=prompt,
            rubric=rubric,
            api_key=request.values.get("api-key", openai.api_key),
            llm_model=request.values.get("model", DEFAULT_MODEL),
            remove_comments=(request.values.get("remove-comments", "0") != "0"),
            num_responses=int(request.values.get("num-responses", "1")),
            temperature=float(request.values.get("temperature", "0.2")),
        )
    except ValueError:
        return "One of the arguments is not parseable as a number", 400
    except openai.error.InvalidRequestError as e:
        return str(e), 400

    if not isinstance(labels, dict) or not isinstance(labels.get("data"), list):
        return "response from AI or service not valid", 400

    return labels

# Submit a test rubric assessment with examples
@assessment_routes.route('/test/assessment/examples', methods=['GET', 'POST'])
def test_assessment_examples():
    openai.api_key = os.getenv('OPENAI_API_KEY')

    with open('tests/data/u3l13_01.js', 'r') as f:
        code = f.read()

    with open('tests/data/u3l13.txt', 'r') as f:
        prompt = f.read()

    with open('tests/data/u3l13.csv', 'r') as f:
        rubric = f.read()

    examples = []
    with open('tests/data/example.js', 'r') as f:
        examples.append(f.read())
    with open('tests/data/example.tsv', 'r') as f:
        examples.append(f.read())

    try:
        labels = assess.label(
            code=code,
            prompt=prompt,
            rubric=rubric,
            examples=[examples],
            api_key=request.values.get("api-key", openai.api_key),
            llm_model=request.values.get("model", DEFAULT_MODEL),
            remove_comments=(request.values.get("remove-comments", "0") != "0"),
            num_responses=int(request.values.get("num-responses", "1")),
            temperature=float(request.values.get("temperature", "0.2")),
        )
    except ValueError as e:
        return "One of the arguments is not parseable as a number: {}".format(str(e)), 400
    except openai.error.InvalidRequestError as e:
        return str(e), 400
    except KeyConceptError as e:
        return str(e), 400
    
    if not isinstance(labels, dict) or not isinstance(labels.get("data"), list):
        return "response from AI or service not valid", 400

    return labels

# Test assessment with code feature extractor
@assessment_routes.route('/test/assessment/cfe', methods=['GET', 'POST'])
def test_assessment_cfe():
    openai.api_key = os.getenv('OPENAI_API_KEY')

    with open('tests/data/cfe_params.json', 'r') as f:
        params = json.load(f)
        
    with open('tests/data/cfe_code.js', 'r') as f:
        code = f.read()

    with open('tests/data/cfe_prompt.txt', 'r') as f:
        prompt = f.read()

    with open('tests/data/cfe_rubric.csv', 'r') as f:
        rubric = f.read()

    try:
        labels = assess.label(
            code=code,
            prompt=prompt,
            rubric=rubric,
            api_key=request.values.get("api-key", openai.api_key),
            llm_model=request.values.get("model", DEFAULT_MODEL),
            remove_comments=params["remove-comments"],
            num_responses=int(params["num-responses"]),
            temperature=float(params["temperature"]),
            code_feature_extractor=params["code-feature-extractor"],
            lesson=params["lesson"],
            response_type=params["response-type"]
        )
    except ValueError as e:
        return "One of the arguments is not parseable as a number: {}".format(str(e)), 400
    except openai.error.InvalidRequestError as e:
        return str(e), 400
    except KeyConceptError as e:
        return str(e), 400
    
    if not isinstance(labels, dict) or not isinstance(labels.get("data"), list):
        return "response from AI or service not valid", 400

    return labels
