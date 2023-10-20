FROM python:3.11

# Note: We cannot use a '3.x-slim' image because we want 'gcc' installed for
# certain packages. For instance, 'honeybadger' requires gcc via a
# dependency on 'psutil'.

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./test /app/test
COPY ./lib /app/lib
COPY ./src /app/src

EXPOSE 80
CMD ["waitress-serve", "--host=0.0.0.0", "--port=80", "--call", "src:create_app"]
