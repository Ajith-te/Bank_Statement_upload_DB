FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app

RUN pip install -r requirements.txt

COPY . /app

EXPOSE 8011

CMD ["gunicorn","-b","0.0.0.0:8011","wsgi:app"]
