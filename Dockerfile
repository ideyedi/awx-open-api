FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7
LABEL maintainer="wmporg_infra-cm@wemakeprice.com"

# wmp-spring-app chart 를 생성하는 기능
# system call 로 `helm` 명령어를 사용할 수 있어야 한다.
WORKDIR /tmp
RUN curl https://get.helm.sh/helm-v3.5.2-linux-amd64.tar.gz -o helm-v3.5.2-linux-amd64.tar.gz && \
  tar -zxvf helm-v3.5.2-linux-amd64.tar.gz && \
  mv linux-amd64/helm /usr/local/bin/helm && \
  rm -rf linux-amd64/

WORKDIR /app

# http://jira.wemakeprice.com/browse/K8S-350
# 컨테이너에서 git 저장소에 commit 하기 위함
RUN echo "[user]\n\
  name  = InfraCM TF \n\
  email = wmporg_infra-cm@wemakeprice.com" > $HOME/.gitconfig

# install deps
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# install app
# https://fastapi.tiangolo.com/deployment/docker/#bigger-applications
COPY ./app /app/app
RUN chmod go-r /app/app/keys/ci_infracm

# 또한 최신버전의 starter chart 가 default path 에 존재해야 한다.
# 새로운 배포마다 최신버전을 유지해야 해서
# COPY ./app /app/app 밑에 있어야 한다.
# application 에서 init 타이밍에 의존성을 해결할 수도 있겠다.
WORKDIR /tmp
ENV XDG_DATA_HOME=$HOME/.local/share \
  BITBUCKET_USERNAME=ci_infracm \
  BITBUCKET_TOKEN=NjU1Njk5MTI5NzAwOkdpkEOnNYwsoWaUjhXX6gdp88Lo
RUN mkdir -p $XDG_DATA_HOME/helm
RUN git clone https://$BITBUCKET_USERNAME:$BITBUCKET_TOKEN@bitbucket.wemakeprice.com/scm/infcm/helm-chart-wmp-staters.git
WORKDIR /tmp/helm-chart-wmp-staters
RUN git archive --format=tar --prefix=starters/ HEAD | (cd $XDG_DATA_HOME/helm/ && tar xf -)

WORKDIR /app
RUN rm -rf /tmp/helm-chart-wmp-staters

EXPOSE 80
