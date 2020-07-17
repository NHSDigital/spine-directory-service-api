FROM nhsdev/nia-spine-directory-service-base:1.0.0

RUN mkdir -p /usr/src/app/spine-directory-service/spine-directory-service

COPY spine-directory-service/spine-directory-service/Pipfile /usr/src/app
COPY spine-directory-service/spine-directory-service/Pipfile.lock /usr/src/app

RUN pip install pipenv

COPY spine-directory-service/common/ /usr/src/app/spine-directory-service/common/
COPY spine-directory-service/spine-directory-service/ /usr/src/app/spine-directory-service/spine-directory-service

WORKDIR /usr/src/app/spine-directory-service/spine-directory-service

RUN pipenv install --deploy --ignore-pipfile

EXPOSE 80

ENTRYPOINT pipenv run start
