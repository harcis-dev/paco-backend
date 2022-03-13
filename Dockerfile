# syntax=docker/dockerfile:1
FROM python:3.10-slim-buster

WORKDIR /paco

# Copy wheel file to workdir
COPY dist/paco-1.0.0-py3-none-any.whl ./

# server-python requirements
COPY requirements.txt ./

RUN apt-get update -y

RUN apt install -y build-essential

RUN apt-get install -y libmariadbclient-dev

RUN pip install -r requirements.txt

RUN pip install paco-1.0.0-py3-none-any.whl --force-reinstall
RUN pip install waitress

# waitress-serve --port=5000 --call paco:create_app
CMD ["waitress-serve", "--port=5000", "--call", "paco:create_app"]