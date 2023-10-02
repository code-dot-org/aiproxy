from flask import Blueprint, request

import os
import openai
import numpy

test_routes = Blueprint('test_routes', __name__)

# A simple JSON response that always succeeds
@test_routes.route('/test')
def test():
    return {}

# Test numpy integration
@test_routes.route('/test/numpy')
def test_numpy():
    response = []

    x = numpy.asarray([[1, 2, 3], [4, 5, 6]])
    response.append(str(x))
    response.append(str(x[1, 1:2]))
    response.append(str(x.T))
    response.append(str(x.dot(x.T)))
    response.append(str(x.reshape([3, 2])))

    return "\n<br>\n".join(response)

# Submit a test prompt
@test_routes.route('/test/openai', methods=['GET','POST'])
def test_openai():
    openai.api_key = os.getenv('OPENAI_API_KEY')

    try:
        completion = openai.ChatCompletion.create(
            model=request.values.get("model", "gpt-3.5-turbo"),
            api_key=request.values.get("api-key", openai.api_key),
            messages=[
                {
                    "role": "user",
                    "content": "Hello world"
                }
            ]
        )
    except openai.error.InvalidRequestError as e:
        return str(e), 400

    return completion.choices[0].message

# Submit a test rubric assessment
@test_routes.route('/test/assessment', methods=['GET','POST'])
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
