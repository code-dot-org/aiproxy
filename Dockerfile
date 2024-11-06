FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./tests /app/tests
COPY ./lib /app/lib
COPY ./src /app/src

EXPOSE 80
# Modified from default 4 threads and 100 connections to better manage the long-running requests.
# https://docs.pylonsproject.org/projects/waitress/en/stable/arguments.html
CMD ["waitress-serve", "--host=0.0.0.0", "--port=80", "--threads=8", "--connection-limit=200", "--call", "src:create_app"]
