FROM python:3.8-buster

ENV PORT 8080

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install pdftohtml -y && pip install -r requirements.txt

COPY . .

EXPOSE $PORT

ENTRYPOINT flask run --port $PORT
