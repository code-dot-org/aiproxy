# Main imports
import os, sys

# Logging
import logging

# Our modules
from src.test import test_routes
from src.openai import openai_routes
from src.assessment import assessment_routes


# Flask
from flask import Flask, jsonify, request

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

    # Set up logging
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logging.basicConfig(format='%(asctime)s: %(name)s:%(message)s', level=log_level)
    logging.log(100, f"Setting up application. Logging level={log_level}")
    logging.basicConfig(format='%(asctime)s: %(levelname)s:%(name)s:%(message)s', level=log_level)

    # Index (a simple HTML response that will always succeed)
    @app.route('/')
    def root():
        return 'Success.'

    app.register_blueprint(test_routes)
    app.register_blueprint(openai_routes)
    app.register_blueprint(assessment_routes)

    @app.before_request
    def require_aiproxy_api_key():
        if request.method == "POST":
            aiproxy_api_key = request.headers.get('Authorization')
            if aiproxy_api_key != os.getenv('AIPROXY_API_KEY'):
                logging.info(aiproxy_api_key, os.getenv('AIPROXY_API_KEY'))
                return jsonify({"error": "Unauthorized"}), 401

    return app
