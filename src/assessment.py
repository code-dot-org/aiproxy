# These routes (/assessment) issue AI driven rubric assessments.
# The /test/assessment will issue a hard-coded AI assessment of a rubric.

from flask import Blueprint, request

import os
import openai

# Our assessment code
from lib.assessment import assess

assessment_routes = Blueprint('assessment_routes', __name__)

# Get the status of a rubric assessment
@assessment_routes.route('/assessment', methods=['GET'])
def get_assessment():
    # So far, we don't persist the results in any memory store, here.
    return {}

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

    try:
        grades = assess.grade(
            code=request.values.get("code", ""),
            prompt=request.values.get("prompt", ""),
            rubric=request.values.get("rubric", ""),
            api_key=request.values.get("api-key", openai.api_key),
            llm_model=request.values.get("model", "gpt-4"),
            remove_comments=(request.values.get("remove-comments", "0") != "0"),
            num_responses=int(request.values.get("num-responses", "1")),
            temperature=float(request.values.get("temperature", "0.2")),
            num_passing_grades=int(request.values.get("num-passing-grades", "2")),
        )
    except ValueError:
        return "One of the arguments is not parseable as a number", 400
    except openai.error.InvalidRequestError as e:
        return str(e), 400

    if not isinstance(grades, list):
        return "response from AI or service not valid", 400

    return grades

# Submit a test rubric assessment
@assessment_routes.route('/test/assessment', methods=['GET','POST'])
def test_assessment():
    openai.api_key = os.getenv('OPENAI_API_KEY')
    
    with open('test/data/u3l23_01.js', 'r') as f:
        code = f.read()

    with open('test/data/u3l23.txt', 'r') as f:
        prompt = f.read()

    with open('test/data/u3l23.csv', 'r') as f:
        rubric = f.read()

    try:
        grades = assess.grade(
            code=code,
            prompt=prompt,
            rubric=rubric,
            api_key=request.values.get("api-key", openai.api_key),
            llm_model=request.values.get("model", "gpt-4"),
            remove_comments=(request.values.get("remove-comments", "0") != "0"),
            num_responses=int(request.values.get("num-responses", "1")),
            temperature=float(request.values.get("temperature", "0.2")),
            num_passing_grades=int(request.values.get("num-passing-grades", "2")),
        )
    except ValueError:
        return "One of the arguments is not parseable as a number", 400
    except openai.error.InvalidRequestError as e:
        return str(e), 400

    if not isinstance(grades, list):
        return "response from AI or service not valid", 400

    return grades
