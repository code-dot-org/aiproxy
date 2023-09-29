FROM python:3.11-slim

RUN pip install Flask

WORKDIR /app
COPY ./src /app

EXPOSE 5000
CMD ["python", "app.py"]
