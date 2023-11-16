#!/bin/bash

set -eu

docker build -t aiproxy:local .
echo "Running: \`coverage run -m pytest $@ && coverage report -m\`"
docker run -e PYTHONPATH=/app --rm aiproxy:local /bin/bash -c "coverage run -m pytest $@ && coverage report -m"
