# sre-serving-api

WMP Infrastructure Automation RESTful WEB API
Made by FastAPI

## Prerequisites

    $ virtualenv venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt
    $ pre-commit install      # auto formatting
    $ cp .env.example .env    # customize it!

## Run

    # http://localhost:8000/
    $ uvicorn app.main:app --reload    # or ./run

### Run as docker-compose

    # once
    $ docker volume create infracm-web-api-db-storage

    # http://localhost:8000/
    $ docker-compose up -d

    # database only; 0.0.0.0:3306
    $ docker-compose up -d db

## Test

    $ pytest                          # default WARN log level
    $ pytest --log-cli-level DEBUG    # DEBUG|INFO|WARN|ERROR|CRITICAL

### Code review
docker-compose를 이용해서 DB 프로비저닝, harbor에 등록된 이미지를 이용해서 기본 셋업 구성
docker file
