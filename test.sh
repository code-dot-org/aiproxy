#!/bin/bash

docker build -t aiproxy:local .
docker run --rm aiproxy:local python -m unittest test_app.py
