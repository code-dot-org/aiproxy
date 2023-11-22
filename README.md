# AI Proxy

Python-based API layer for LLM API's, implemented as an HTTP API in ECS Fargate.

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

To enable Honeybadger reporting for events in the application, provide the
`HONEYBADGER_API_KEY` within the configuration or as an environment variable. When
enabled, the application will notify on Exceptions raised and any `error` or `critical`
logs.

## Local Development

All of our server code is written using [Flask](https://flask.palletsprojects.com/en/2.3.x/).

The Flask web service exists within `/src`. The `__init__.py` is the
entry point for the app. The other files provide the routes.

Other related Python code that implement features are within `/lib`.

To build the app, use `docker compose build`.
You will need to rebuild when you change the source.

To run the app locally, use `docker compose up` from the repo root.

This will run a webserver accessible at <http://localhost:5000>.

**Note**: You need to provide the API keys in the `config.txt` file
before the service runs. See the above "Configuration" section.

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

## Secrets

Secrets for this project follow the naming convention `${EnvironmentType}/${DNSRecord}/honeybadger_api_key`. Our security model controls access to secrets based on the prefix, and will deny read access to any secret not prefixed with `development/`, so we tell our application's Cloudformation template whether we are in a development, test, or production environment type via [config files](cicd/3-app/aiproxy/config).

* In production: `production/aiproxy.code.org/honeybadger_api_key`
* In test: `test/aiproxy-test.code.org/honeybadger_api_key`
* In an "adhoc" development environment: `development/aiproxy-dev-mybranch.code.org/honeybadger_api_key`
* A prod-like environment, not based on `main`: `production/aiproxy-otherbranch.code.org/honeybadger_api_key`

Read more about environments and environment types in [cicd/README.md](cicd/README.md).

### Creating new secrets

To create a new secret, define it in "[cicd/3-app/aiproxy/template.yml](cicd/3-app/aiproxy/template.yml) in the "Secrets" section. This will create an empty secret once deployed.

Once created, you can set the value of this secret (via the AWS Console, as an Admin). Finally, deploy your code that uses the new secret, loading it via the `GetSecretValue` function from the AWS SDK.

## CICD

See [CICD Readme](./cicd/README.md)

## Links to deployed resources

- [CICD Dependency Stack](https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/outputs?filteringText=&filteringStatus=active&viewNested=true&stackId=arn%3Aaws%3Acloudformation%3Aus-east-1%3A475661607190%3Astack%2Faiproxy-cicd-deps%2Fdc0cc2a0-5d98-11ee-92d1-0e2fac17ec9f)
- [CICD Stack](https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?filteringText=&filteringStatus=active&viewNested=true&stackId=arn%3Aaws%3Acloudformation%3Aus-east-1%3A475661607190%3Astack%2Faiproxy-cicd%2F580cf6b0-5d9c-11ee-b86a-0a8053e30da7)
- [CICD Pipeline](https://us-east-1.console.aws.amazon.com/codesuite/codepipeline/pipelines/aiproxy-cicd/view?region=us-east-1)
