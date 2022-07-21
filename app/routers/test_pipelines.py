from fastapi.testclient import TestClient
from ..main import app
from ..models.params import (
    DockerfileBuildOptions,
    PipelineBuilderParams,
    PipelineBuilderDeployParams,
    PipelineBuilderDeployBigipParams,
    HelmValueImageParams,
    HelmValueIngressParams,
    HelmValueBigipParams,
    HelmValuePinpointParams,
    HelmValueSpringAppParams,
    HelmValueResourceParams,
    HelmValueResourcesParams,
    HelmValueHealthCheckParams,
    HelmValueIngressTlsParams,
)

client = TestClient(app)


# POST /pipelines
def test_post_pipelines():
    params = PipelineBuilderParams(
        env="dev",
        repo="ssh://git@bitbucket.wemakeprice.com:7999/infcm/spring-hello-world.git",
        base="master",
        build=DockerfileBuildOptions(artifact="build/libs/*.war"),
        starter="tomcat",
        deploy=PipelineBuilderDeployParams(
            namespace="infcm",
            replicaCount=1,
            branches=["develop"],
            targets=["a-wmp-dev"],
            hosts=["dev-infracm-helloworld.wemakeprice.kr"],
            bigip=PipelineBuilderDeployBigipParams(enabled=False),
            pinpoint=HelmValuePinpointParams(enabled=True),
            spring=HelmValueSpringAppParams(opts=""),
            resources=HelmValueResourcesParams(
                limits=HelmValueResourceParams(),
                requests=HelmValueResourceParams(),
            ),
            # spring-hello-world 는 healthcheck 없다.
            healthcheck=HelmValueHealthCheckParams(enabled=False),
        ),
    )
    res = client.post("/pipelines/", json=params.dict())
    assert res.status_code == 200
