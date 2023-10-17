FROM python:3.11-slim

RUN pip install Flask

WORKDIR /app
COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ./test /app/test
COPY ./lib /app/lib
COPY ./src /app/src

EXPOSE 80
CMD ["waitress-serve", "--host=0.0.0.0", "--port=80", "--call", "src:create_app"]
