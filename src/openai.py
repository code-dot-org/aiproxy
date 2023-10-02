from flask import Blueprint

import os
import openai

openai_routes = Blueprint('openai_routes', __name__)

# Just report the models from OpenAI
@openai_routes.route('/openai/models')
def get_openai_models():
    openai.api_key = os.getenv('OPENAI_API_KEY')
    return openai.Model.list().data
