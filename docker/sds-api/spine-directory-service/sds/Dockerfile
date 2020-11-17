FROM python:3.7-slim as base

RUN apt-get update && \
    apt-get install build-essential -y

RUN sed -i 's/SECLEVEL=2/SECLEVEL=1/' /etc/ssl/openssl.cnf # Temporarily lower security to workaround opentest certs with SHA1 signatures

RUN mkdir -p /usr/src/app/spine-directory-service/sds

COPY spine-directory-service/sds/Pipfile /usr/src/app
COPY spine-directory-service/sds/Pipfile.lock /usr/src/app

RUN pip install pipenv

COPY spine-directory-service/sds/ /usr/src/app/spine-directory-service/sds

WORKDIR /usr/src/app/spine-directory-service/sds

RUN pipenv install --deploy --ignore-pipfile

EXPOSE 9000

ENTRYPOINT pipenv run start
