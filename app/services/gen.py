import subprocess
import tempfile
import glob
from fastapi.templating import Jinja2Templates

from ..models.params import (
    JenkinsfileParams,
    DockerfileParams,
    DockerfileDefaultParams,
    HelmValueParams,
)
from ..config import get_settings

templates = Jinja2Templates(directory="app/templates")


def gen_jenkinsfile(params: JenkinsfileParams):
    settings = get_settings()
    template = templates.get_template("generator/Jenkinsfile.j2")
    return template.render(
        dict(
            {
                "deployable_branches": ", ".join(
                    list(map(lambda x: f'"{x}"', params.branches))
                ),
            },
            **params.dict(),
        )
    )


def gen_dockerfile(params: DockerfileParams):
    template = templates.get_template("generator/Dockerfile.j2")
    default_params = DockerfileDefaultParams().dict()
    default_params[params.build.tool]["enabled"] = True
    return template.render(dict(params.dict(), **default_params))


def gen_helm_values(params: HelmValueParams):
    template = templates.get_template("generator/values.yaml.j2")
    return template.render(params.dict())


def gen_docker_entrypoint():
    template = templates.get_template("generator/docker-entrypoint.sh.j2")
    return template.render()


def gen_tomcat_config():
    template = templates.get_template("generator/server.xml.j2")
    return template.render()


def gen_wmp_spring_app_chart(params: HelmValueParams) -> str:
    """
    wmp_spring_app chart file 을 생성합니다.
    system call 로 `helm` 커맨드를 활용합니다.
    tmp directory 를 생성하고 dir path 를 return 합니다.

    Args:
        params (HelmValueParams)

    Returns:
        str: chart path
    """
    dirpath = tempfile.mkdtemp()
    subprocess.run(
        ["helm", "create", params.service, "-p", "wmp-spring-app"], cwd=dirpath
    )
    # <PROJECT> 문자열을 모두 변경
    for filepath in glob.iglob(f"{dirpath}/{params.service}/**/*.yaml", recursive=True):
        with open(filepath) as file:
            s = file.read()
        s = s.replace("<PROJECT>", params.project)
        with open(filepath, "w") as file:
            file.write(s)
    return f"{dirpath}/{params.service}"
