FROM python:3.7-slim as base

RUN apt-get update && \
    apt-get install build-essential -y

RUN mkdir -p /usr/src/app/spine-directory-service/sandbox

COPY Pipfile /usr/src/app
COPY Pipfile.lock /usr/src/app

RUN pip install pipenv

COPY / /usr/src/app/spine-directory-service/sandbox

WORKDIR /usr/src/app/spine-directory-service/sandbox

RUN pipenv install --deploy --ignore-pipfile

EXPOSE 5000

ENTRYPOINT pipenv run start