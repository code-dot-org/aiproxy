FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80
CMD ["waitress-serve", "--host=0.0.0.0", "--port=80", "--call", "aiproxy.app:create_app"]
