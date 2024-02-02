# AI Proxy

Python-based API layer for LLM API's, implemented as an HTTP API in ECS Fargate.

All of our server code is written using [Flask](https://flask.palletsprojects.com/en/2.3.x/).

The Flask web service exists within `/src`. The `__init__.py` is the
entry point for the app. The other files provide the routes.

Other related Python code that implement features are within `/lib`.

To Do:
* [x] validate cicd infra (using placeholder app template)
* [x] validate pr validation
* [x] create python flask app
* [ ] add test steps for cicd
* [x] add build & push-to-ecr steps for cicd
* [x] create [application cloudformation template](cicd/3-app/aiproxy/template.yml)
* [ ] authentication

## Configuration

The configuration is done via environment variables stored in the `config.txt` file.

For local development, copy the `config.txt.sample` file to `config.txt` to have a
starting point. Then set the `OPENAI_API_KEY` variable to a valid OpenAI API key to
enable that service. Or, otherwise set that variable the appropriate way when
deploying the service.

To control the logging information, use the `LOG_LEVEL` configuration parameter. Set
to `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. The `DEBUG` setting is the
most permissive and shows all logging text. The `CRITICAL` prevents most logging
from happening. Most logging happens at `INFO`, which is the default setting.

## Local Development

* Install docker 
  * If you are on WSL, installing docker on the linux system wouldn't work as linux itself is running in a container. Install docker desktop instead following these instructions: https://learn.microsoft.com/en-us/windows/wsl/tutorials/wsl-containers

* To build the app, use `docker compose build`.
You will need to rebuild when you change the source.

* To run the app locally, use `docker compose up` from the repo root.

**Note**: You need to provide the API keys in the `config.txt` file
before the service runs. See the above "Configuration" section.

This will run a webserver accessible at <http://localhost>.

* To validate if the local environment is running successfully, run `bin\assessment-test.rb` It should print the response for a test assessment.

### Rubric Tester
To run the rubric tester locally:

#### setup

install pyenv: https://github.com/pyenv/pyenv?tab=readme-ov-file#installation
* Mac: `brew install pyenv`
* Ubuntu: `curl https://pyenv.run | bash`

install python 3.11:
* `pyenv install 3.11.7`

set python 3.11 for the aiproxy repo:
* `cd aiproxy`
* `pyenv local 3.11.7`

create a python virtual environment at the top of the directory:
* `python -m venv .venv`

ensure aws access for accessing aws bedrock models:
* from the code-dot-org repo root, run:
  * `bin/aws_access`
* from this repo's root, run: 
  * `gem install aws-google`
  
#### run

Activate the virtual environment:
* `source .venv/bin/activate`

Install requirements to the virtual environment with pip:
* `pip install -r requirements.txt`

Export the following environment variables (or add them once to your shell profile)
* `export OPENAI_API_KEY=<your API key>`
* `export PYTHONPATH=<path to aiproxy root>`

See rubric tester options with:
* `python lib/assessment/rubric_tester.py --help`

## Logging

Logging is done via the normal Python `logging` library.
Use the [official Python documentation](https://docs.python.org/3/howto/logging.html) for good information about using this library.

Essentially, logging happens at a variety of levels.
You can control the level you wish logs to appear using the `LOG_LEVEL` environment variable.
The logs will be written out if they match this log level or they are of a greater level.
For instance, `INFO` means everything written out using `logging.info` will be seen and also
everything at the `WARNING`, `ERROR`, or `CRITICAL` levels. Logging at the `DEBUG` level will
not be reported. See the table in the
[When to use logging](https://docs.python.org/3/howto/logging.html#when-to-use-logging)
section of the docs for the full list.

To write to the log, import the `logging` library into the Python file.
Then, simply call `logging.info("my string")` which, in this instance, will log the string at the `INFO` level.
You can find examples that already exist within the project.

### Deployed ECS Logs

When the container is deployed to Amazon ECS, the logs will likely be visible when viewing
the particular running service. When logged into AWS, navigate to ECS (Elastic Container Service)
and find the `aiproxy` cluster. Then, find the particular service. On the service page,
go to the "Logs" tab and you can find the recent logs and a link to the full log in CloudWatch.

## API

For information about the API, see the [API documentation](API.md).

## Testing

To run the test suite against the container, invoke the `./bin/test.sh` script. This will
build and run the container against the Python tests.

For information about testing the service, see the [Testing documentation](TESTING.md).

## CICD

See [CICD Readme](./cicd/README.md)

## Links to deployed resources

- [CICD Dependency Stack](https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/outputs?filteringText=&filteringStatus=active&viewNested=true&stackId=arn%3Aaws%3Acloudformation%3Aus-east-1%3A475661607190%3Astack%2Faiproxy-cicd-deps%2Fdc0cc2a0-5d98-11ee-92d1-0e2fac17ec9f)
- [CICD Stack](https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?filteringText=&filteringStatus=active&viewNested=true&stackId=arn%3Aaws%3Acloudformation%3Aus-east-1%3A475661607190%3Astack%2Faiproxy-cicd%2F580cf6b0-5d9c-11ee-b86a-0a8053e30da7)
- [CICD Pipeline](https://us-east-1.console.aws.amazon.com/codesuite/codepipeline/pipelines/aiproxy-cicd/view?region=us-east-1)
