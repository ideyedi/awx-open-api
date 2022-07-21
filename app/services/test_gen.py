import re
import logging
import shutil
from .gen import gen_dockerfile, gen_jenkinsfile, gen_wmp_spring_app_chart
from ..models.params import (
    DockerfileParams,
    DockerfileBuildOptions,
    JenkinsfileParams,
    HelmValueParams,
    HelmValueImageParams,
    HelmValueIngressParams,
    HelmValueIngressTlsParams,
    HelmValuePinpointParams,
    HelmValueBigipParams,
    HelmValueSpringAppParams,
    HelmValueResourcesParams,
    HelmValueHealthCheckParams,
    HelmValueResourceParams,
)


def test_gen_dockerfile():
    """
    생성된 Dockerfile 의 유효성 체크
    """
    params = DockerfileParams(
        name="test",
        build=DockerfileBuildOptions(artifact="build/libs/*.jar"),
    )
    content = gen_dockerfile(params=params)
    assert len(re.findall("ROOT.jar", content)) == 1

    params = DockerfileParams(
        name="test",
        build=DockerfileBuildOptions(artifact="build/libs/*.war"),
    )
    content = gen_dockerfile(params=params)
    assert len(re.findall("ROOT.war", content)) == 1
    assert len(re.findall("ROOT.jar", content)) == 0


def test_gen_jenkinsfile():
    """
    생성된 Jenkinsfile 의 유효성 체크
    """
    params = JenkinsfileParams(
        project="wonder",
        name="deal-api",
        branches=["develop"],
        targets=["a-wmp-dev"],
        dockerfile="Dockerfile",
    )

    content = gen_jenkinsfile(params=params)
    assert len(re.findall(r'deployable_branches = \["develop"\]', content)) == 1
    assert len(re.findall(r"wonder", content)) >= 1
    assert len(re.findall(r"deal-api", content)) >= 1
    assert len(re.findall(r"Dockerfile", content)) >= 1


def test_wmp_spring_app_chart():
    """
    spring app chart 가 올바르게 생성되는지
    """
    params = HelmValueParams(
        project="infcm",
        service="deal-api",
        namespace="infcm",
        replicaCount=1,
        env="dev",
        image=HelmValueImageParams(tag="develop"),
        ingress=HelmValueIngressParams(
            enabled=True,
            klass="nginx",
            hosts=["dev-deal-api-infcm.wemakeprice.kr"],
            tls=[
                HelmValueIngressTlsParams(
                    secretName="star.wemakeprice.kr",
                    hosts=["dev-deal-api-infcm.wemakeprice.kr"],
                )
            ],
        ),
        pinpoint=HelmValuePinpointParams(enabled=False),
        bigip=HelmValueBigipParams(
            enabled=False,
            environment="development",
            hostname="dev-deal-api-infcm.wemakeprice.kr",
            nodeNamePatterns=["a.wmp.dev"],
        ),
        spring=HelmValueSpringAppParams(opts=""),
        resources=HelmValueResourcesParams(
            requests=HelmValueResourceParams(cpu="2000m", memory="2048Mi"),
            limits=HelmValueResourceParams(cpu="2000m", memory="2048Mi"),
        ),
        healthcheck=HelmValueHealthCheckParams(
            enabled=True,
            path="/servicemanager/health",
            initialDelaySeconds=100,
            timeoutSeconds=3,
            failureThreshold=5,
        ),
    )

    path = gen_wmp_spring_app_chart(params=params)
    assert len(re.findall("deal-api", path)) == 1

    with open(f"{path}/values.yaml") as file:
        content = file.read()
        assert len(re.findall("PROJECT", content)) == 0

    shutil.rmtree("/".join(path.split("/")[:-1]))
