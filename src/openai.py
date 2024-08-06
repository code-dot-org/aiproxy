# These routes (/openai) will query the OpenAI API with the configured API key.
# This is useful for using the OpenAI API to determine metrics and usage data.
# Right now, we can query the list of models available. (/openai/models)
# The '/test/openai' route will query the given chat model with a small prompt.

from flask import Blueprint, request, jsonify

import os
import openai

openai_routes = Blueprint('openai_routes', __name__)

# Just report the models from OpenAI
@openai_routes.route('/openai/models')
def get_openai_models():
    openai.api_key = os.getenv('OPENAI_API_KEY')
    return openai.Model.list().data

# Submit a test prompt
@openai_routes.route('/test/openai', methods=['GET','POST'])
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
