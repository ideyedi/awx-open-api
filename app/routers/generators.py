from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from ..models.params import JenkinsfileParams, DockerfileParams, HelmValueParams
from ..services.gen import (
    gen_jenkinsfile,
    gen_dockerfile,
    gen_docker_entrypoint,
    gen_tomcat_config,
    gen_helm_values,
)

router = APIRouter(prefix="/generator", tags=["Generators"])


@router.post("/Jenkinsfile", response_class=PlainTextResponse)
def jenkinsfile(params: JenkinsfileParams):
    return gen_jenkinsfile(params)


@router.post("/Dockerfile", response_class=PlainTextResponse)
def dockerfile(params: DockerfileParams):
    """
    parameter 에 맞게 Spring Boot app 을 build 하고 실행하는 `Dockerfile` 을 plain/text 로 제공합니다.

    starter 를 `embbeded` 로 사용하기 위해서는 app 에서 `spring-boot-starter-web` 에 대한 의존성이 명시되어 있어야 합니다.
    https://docs.spring.io/spring-boot/docs/2.1.9.RELEASE/reference/html/howto-embedded-web-servers.html

    `tomcat` starter 는 runtime 에 pinpoint 를 지원하지만, `embedded` starter 를 사용하는 경우에는 pinpoint 설정을 embedded webserver 내부에서 직접 해야합니다.
    """
    return gen_dockerfile(params)


@router.get("/docker-entrypoint", response_class=PlainTextResponse)
def docker_entrypoint():
    return gen_docker_entrypoint()


@router.get("/tomcat-config", response_class=PlainTextResponse)
def tomcat_config():
    return gen_tomcat_config()


@router.post("/helm/wmp-spring-app/values", response_class=PlainTextResponse)
def helm_values(params: HelmValueParams):
    """
    전달된 `params` 에 맞는 wmp-spring-app helm chart values.yaml 을 생성합니다.
    """
    return gen_helm_values(params)
