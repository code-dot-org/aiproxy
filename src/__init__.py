# Main imports
import os

# Our modules
from src.test import test_routes
from src.openai import openai_routes
from src.assessment import assessment_routes

# Flask
from flask import Flask

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

    app.register_blueprint(test_routes)
    app.register_blueprint(openai_routes)
    app.register_blueprint(assessment_routes)

    return app
