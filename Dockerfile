FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && \
    apt-get install -y curl=8.14.1-2+deb13u2 unzip=6.0-29 gosu=1.17-3+b4 --no-install-recommends && \
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    gosu root ./aws/install && \
    rm -rf /var/lib/apt/lists

COPY ./tests /app/tests
COPY ./lib /app/lib
COPY ./src /app/src

EXPOSE 80
# Modified from default 4 threads and 100 connections to better manage the long-running requests.
# https://docs.pylonsproject.org/projects/waitress/en/stable/arguments.html
CMD ["waitress-serve", "--host=0.0.0.0", "--port=80", "--threads=8", "--connection-limit=200", "--call", "src:create_app"]
