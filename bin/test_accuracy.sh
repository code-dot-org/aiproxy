#!/bin/bash

set -eu

echo "Running: \`coverage run -m pytest --accuracy $@ && coverage report -m\`"
coverage run -m pytest --accuracy $@ && coverage report -m