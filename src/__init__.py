# Main imports
import os, sys

# Logging
import logging

# Our modules
from src.test import test_routes
from src.openai import openai_routes
from src.assessment import assessment_routes

# AWS
import boto3

# Flask
from flask import Flask

# Honeybadger support
from honeybadger.contrib import FlaskHoneybadger
from honeybadger.contrib.logger import HoneybadgerHandler

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
  
    
    honeybadger_api_key = get_secret('honeybadger_api_key')
    if honeybadger_api_key:
        # Add Honeybadger support
        logging.info('Setting up Honeybadger configuration')

        # I need to patch Flask in order for Honeybadger to load
        # The honeybadger library uses this deprecated attribute
        # It was deprecated because it is now always 'True'.
        # See: https://github.com/pallets/flask/commit/04994df59f2f642e52ba46ca656088bcdb931262
        from flask import signals
        setattr(signals, 'signals_available', True)

        # Log exceptions to Honeybadger
        app.config['HONEYBADGER_API_KEY'] = honeybadger_api_key
        app.config['HONEYBADGER_PARAMS_FILTERS'] = 'password, secret, openai_api_key, api_key'
        app.config['HONEYBADGER_ENVIRONMENT'] = os.getenv('FLASK_ENV')
        FlaskHoneybadger(app, report_exceptions=True)

        # Also log ERROR/CRITICAL logs to Honeybadger
        class NoExceptionErrorFilter(logging.Filter):
            def filter(self, record):
                # But ignore Python logging exceptions on 'ERROR'
                return not record.getMessage().startswith('Exception on ')

        hb_handler = HoneybadgerHandler(api_key=honeybadger_api_key)
        hb_handler.setLevel(logging.ERROR)
        hb_handler.addFilter(NoExceptionErrorFilter())
        logger = logging.getLogger()
        logger.addHandler(hb_handler)

    # Index (a simple HTML response that will always succeed)
    @app.route('/')
    def root():
        return 'Success.'

    app.register_blueprint(test_routes)
    app.register_blueprint(openai_routes)
    app.register_blueprint(assessment_routes)

    return app

# Get a secret from AWS Secrets Manager or local ENV
def get_secret(secret_name):
    local_env_var_name = secret_name.upper()
    # AWS Secrets are named like `production/aiproxy.code.org/secret_name}`
    aws_secret_id = '/'.join([os.getenv('ENVIRONMENT'), os.getenv('ENVIRONMENT_TYPE'), secret_name])

    secret = ''
    if os.getenv(local_env_var_name):
        secret = os.getenv(local_env_var_name)
        logging.info(f'Retrieved secret "{secret_name}" from local ENV')
    else:
        try:
            client = boto3.client('secretsmanager')
            logging.info(f'Retrieved secret "{secret_name}" from AWS Secrets Manager')
            secret = client.get_secret_value(SecretId=aws_secret_id)
        except Exception as e:
            logging.error(f'Error getting "{secret_name}" from AWS Secrets Manager: {e}')

    return secret
