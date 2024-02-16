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

* To validate if the local environment is running successfully, run `bin/assessment-test.rb` It should print the response for a test assessment.

## Rubric Tester

### background

Rubric Tester is a tool used to measure the accuracy of our ai evaluation system against labels provided by human annotators.

Config for rubric tester is stored in S3:
```
s3://cdo-ai/teaching_assistant/datasets/
s3://cdo-ai/teaching_assistant/experiments/
s3://cdo-ai/teaching_assistant/releases/
```

Within each of these directories, there are named config directories each containing one subdirectory for each lesson:
```
datasets/contractor-grades-batch-1-fall-2023/csd3-2023-L11/
datasets/contractor-grades-batch-1-fall-2023/csd3-2023-L14/
datasets/contractor-grades-batch-1-fall-2023/...
...
experiments/ai-rubrics-pilot-baseline/csd3-2023-L11/
...
releases/2024-02-01-ai-rubrics-pilot-baseline/csd3-2023-L11/
...
```

The mental model for each of these directories is:
* `datasets/`: student code samples (`*.js`) with labels provided by human graders (`actual_labels.csv`)
* `experiments/`: configuration for ai evaluation in development 
  * `params.json`: model parameters including model name, num_responses, temperature
  * `system_prompt.txt`
  * `standard_rubric.csv`
  * `examples/` (optional)
* `releases/`: configuration for ai evaluation in production. similar to `experiments/`, but each directory will also contain `confidence.json` which indicates low/medium/high confidence for each learning goal in each lesson.

When you run rubric tester, the datasets and experiments you use will be copied locally, after which you can easily take a closer look at the contents of these files by running `find datasets experiments` from the repo root.

### setup

To set up rubric tester to run locally:

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
  
### run

Activate the virtual environment:
* `source .venv/bin/activate`

Install requirements to the virtual environment with pip:
* `pip install -r requirements.txt`

Export the following environment variables (or add them once to your shell profile)
* `export OPENAI_API_KEY=<your API key>`
* `export PYTHONPATH=<path to aiproxy root>`

See rubric tester options with:
* `python lib/assessment/rubric_tester.py --help`

### example usage

When running rubric tester locally, you will pick a dataset to measure accuracy against, an experiment to define the ai config, and other optional config parameters. with no params, an experiment using gpt-3.5-turbo is used to evaluate all 6 ai-enabled lessons in CSD Unit 3, measuring accuracy against the default dataset which contains about 20 labeled student projects per lesson. 

GPT 3.5 Turbo is the default because a complete test run with that model costs only $0.20 whereas a complete test run with GPT 4 (classic) costs about $12.00.

A recommended first run is to use default experiment and dataset, limited to 1 lesson:
```
(.venv) Dave-MBP:~/src/aiproxy (rt-recover-from-bad-llm-responses)$ python ./lib/assessment/rubric_tester.py --lesson-names csd3-2023-L11 
2024-02-13 20:15:30,127: INFO: Evaluating lesson csd3-2023-L11 for dataset contractor-grades-batch-1-fall-2023 and experiment ai-rubrics-pilot-gpt-3.5-turbo...
```

When you do this, you'll likely notice a mix of successes and errors on the command line:

```
2024-02-13 20:15:32,384: ERROR: student_12 Choice 0:  Invalid response: invalid label value: 'The program has no sequencing errors.'
2024-02-13 20:17:24,313: INFO: student_15 request succeeded in 2 seconds. 1305 tokens used.
```

The report that gets generated will contain a count of how many errors there were:

![Screenshot 2024-02-13 at 8 20 47 PM](https://github.com/code-dot-org/aiproxy/assets/8001765/4613414c-3bff-4209-ac0c-fdda5ec0b370)

In order to rerun only the failed student projects, you can pass the `-c` (`--use-cached`) option:

```commandline
(.venv) Dave-MBP:~/src/aiproxy (rt-recover-from-bad-llm-responses)$ python ./lib/assessment/rubric_tester.py --lesson-names csd3-2023-L11 -c
```

![Screenshot 2024-02-13 at 8 24 31 PM](https://github.com/code-dot-org/aiproxy/assets/8001765/ff560302-94b9-4966-a5d6-7d9a9fa54892)

After enough reruns, you'll have a complete accuracy measurement for the lesson. NOTE: the very high number of errors in this example is because we are using a weak model (GPT 3.5 Turbo) by default. Stronger models often complete an entire lesson without errors, but in case of errors the same principle applies to getting complete test results.

### using cached responses

experiments run against GPT 4, GPT 4 Turbo and other pricey models should include report html and cached response data. this allows you to quickly view reports for these datasets either by looking directly at the `output/report*html` files or by regenerating the report against cached data via a command like:
```commandline
python ./lib/assessment/rubric_tester.py --experiment-name ai-rubrics-pilot-baseline-gpt-4-turbo --use-cached
```

### creating a new experiment

generally speaking, new experiments will be created as follows:
* download an existing experiment from S3
* create a local copy
* make local changes and measure accuracy
* once satisfied, upload the experiment dir back to S3, including output/ and cached_responses/ directories

a similar process can be followed for new releases.

### regenerating example LLM responses

rubric tester supports sending example user requests (js) and LLM responses (json) so that the LLM can use few-shot learning to give better results. Once you have identified js that you want to use as examples, here is how you can leverage the rubric tester to have the LLM do most of the work of generating these responses for you on your local machine:

1. create a new experiment you want to add examples to
2. craft example js and desired labels into a temporary new dataset
    * copy your example `*.js` files into the dataset
    * create an `actual_labels.csv` containing desired labels for each student and each learning goal
3. use LLM to generate new json responses as a starting point
    * temporarily modify `label.py` to log each `response_data` it receives
    * use rubric tester to run the new experiment against the temp dataset using GPT 4 classic (e.g. `gpt-4-0613`), and record the report html and log output
4. in your experiment, create the example responses
    * copy your example js from the temp dataset into `examples/*.js`
    * clean the log output and paste it into `examples/*.json`
    * use the report html to identify any errors the LLM made, and correct any issues in the Observations, Reason, or Grade fields in the new `examples/*.json`

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
