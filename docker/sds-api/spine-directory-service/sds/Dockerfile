FROM nhsdev/nia-spine-directory-service-base:1.0.0

RUN mkdir -p /usr/src/app/spine-directory-service/sds

COPY ./Pipfile /usr/src/app
COPY ./Pipfile.lock /usr/src/app

RUN pip install pipenv

COPY . /usr/src/app/spine-directory-service/sds

WORKDIR /usr/src/app/spine-directory-service/sds

RUN pipenv install --deploy --ignore-pipfile

EXPOSE 9000

ENTRYPOINT pipenv run start
