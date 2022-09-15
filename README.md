# site-reliability-api
WMP Infrastructure RESTful WEB API

## Prerequisites

    $ install pipenv
    $ pipenv --python 3.8.12
    $ pipenv sync
    $ Start develop!!

## Run

    # http://localhost:8000/
    $ uvicorn app.main:app --reload or ./run

## Test

    $ pytest                          # default WARN log level
    $ pytest --log-cli-level DEBUG    # DEBUG|INFO|WARN|ERROR|CRITICAL

<!--
### Code review
docker-compose를 이용해서 DB 프로비저닝, harbor에 등록된 이미지를 이용해서 기본 셋업 구성
docker file

### Run as docker-compose

    # once
    $ docker volume create infracm-web-api-db-storage

    # http://localhost:8000/
    $ docker-compose up -d

    # database only; 0.0.0.0:3306
    $ docker-compose up -d db
-->