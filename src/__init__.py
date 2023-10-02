import os
import json

# Our assessment code
from lib import assess

# Flask
from flask import Flask, Response, request

# OpenAI library
import openai


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Index (a simple HTML response that will always succeed)
    @app.route('/')
    def root():
        return 'Success.'

    # A simple JSON response that always succeeds
    @app.route('/test')
    def test():
        print("/test call handled")
        return {}

    # Just report the models from OpenAI
    @app.route('/openai/models')
    def get_models():
        openai.api_key = os.getenv('OPENAI_API_KEY')
        return openai.Model.list().data

    # Submit a test prompt
    @app.route('/openai/test', methods=['GET','POST'])
    def perform_openai_test():
        print("/openai/test call started")
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
            print("/openai/test call handled with an error:", str(e))
            return str(e), 400

        print("/openai/test call handled successfully")
        return completion.choices[0].message

    # Get the status of a rubric assessment
    @app.route('/assessment', methods=['GET'])
    def poll_assessment():
        return {}

    # Submit a rubric assessment
    @app.route('/assessment', methods=['POST'])
    def perform_assessment():
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
    @app.route('/assessment/test', methods=['GET','POST'])
    def test_assessment():
        print("/assessment/test call started")
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
            print("/assessment/test call errored: one of the arguments is not parseable as a number")
            return "One of the arguments is not parseable as a number", 400
        except openai.error.InvalidRequestError as e:
            print("/assessment/test call errored: OpenAI error:", str(e))
            return str(e), 400

        if not isinstance(grades, list):
            print("/assessment/test call errored: response from AI invalid")
            return "response from AI or service not valid", 400

        print("/assessment/test call handled successfully")
        return grades

    return app
