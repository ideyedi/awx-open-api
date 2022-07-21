import re
import json
import os
import shutil
import logging
from git import Repo
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from ..config import (
    get_settings,
    ENV_BRANCH_MAP,
    ENV_TAG_MAP,
    BIGIP_ENV_BY_ENV_MAP,
    DEV_INFRACM_REGISTRY,
    DEV_INFRACM_REGISTRY_SECRET_NAME,
)
from .msteams import Teams

# model
from ..models.params import (
    DISPOSABLE_WEBHOOK_PREFIX,
    JenkinsfileParams,
    DockerfileParams,
    BitBucketPullRequestBranchParams,
    BitBucketPullRequestParams,
    BitbucketPullRequestPayload,
    BitBucketWebhookParams,
    BitbucketWebhookItem,
    PipelineBuilderParams,
    HelmValueParams,
    HelmValueIngressParams,
    HelmValueImageParams,
    HelmValueBigipParams,
    HelmValueIngressTlsParams,
    JenkinsJobParams,
    ArgocdProjectParams,
    ArgocdAppParams,
)

# services
from .vcs import Git, INFRACM_AUTHOR_INFO
from .bitbucket import PullRequest, WebHook
from .jenkins import JenkinsAgent
from .argocd import Argocd
from .gen import (
    gen_jenkinsfile,
    gen_dockerfile,
    gen_docker_entrypoint,
    gen_tomcat_config,
    gen_helm_values,
    gen_wmp_spring_app_chart,
)

# dao
from ..dao.pipeline import upsert as upsert_pipeline


settings = get_settings()
WMP_KUBERNETES_CONFIGURE_DIR = ".wmp"
WMP_INFRACM_CD_CONFIGURATION_REPO_URL = (
    "ssh://git@bitbucket.wemakeprice.com:7999/deploy/k8s.git"
)

WMP_INFRACM_CD_REPO_KEY = "DEPLOY"
WMP_INFRACM_CD_REPO_SLUG = "k8s"

WMP_INFRACM_WEBAPI_HOST_MAP_BY_ENV = {
    "dev": "https://az-dev-api-infracm.wemakeprice.kr",
    "qa": "https://az-qa-api-infracm.wemakeprice.kr",
    "stg": "https://az-stg-api-infracm.wemakeprice.kr",
    "prod": "https://api-infracm.wemakeprice.kr",
}


def checkout(git: Git, url: str, base: str, branch: str) -> Repo:
    """
    clone and checkout branch

    Args:
        git (Git)
        url (str): git ssh url
        branch (str)

    Returns:
        Repo
    """
    repo = git.clone(url=url, branch=base)
    git.checkoutBranch(repo=repo, branch=branch)
    return repo


def gen_ci_files(working_dir: str, params: PipelineBuilderParams):
    """
    - Dockerfile
    - Jenkinsfile
    - docker-entrypoint.sh
    - misc/apache-tomcat/conf/server.xml

    파일을 working_dir/ 에 `params` 에 맞추어 생성합니다.

    Args:
        working_dir (str): dirpath
        params (PipelineBuilderParams)
    """
    os.makedirs(f"{working_dir}/{WMP_KUBERNETES_CONFIGURE_DIR}", exist_ok=True)
    if not os.path.exists(
        f"{working_dir}/{WMP_KUBERNETES_CONFIGURE_DIR}/{params.env}.json"
    ):
        with open(
            f"{working_dir}/{WMP_KUBERNETES_CONFIGURE_DIR}/{params.env}.json", "w"
        ) as w:
            w.write(json.dumps(params.dict(), indent=4, sort_keys=True))

    # .wmp/Dockerfile 0644
    if not os.path.exists(f"{working_dir}/{WMP_KUBERNETES_CONFIGURE_DIR}/Dockerfile"):
        dockerfileParams = DockerfileParams(
            name=params.name,
            build=params.build,
            starter=params.starter,
        )
        dockerfile = gen_dockerfile(dockerfileParams)
        with open(f"{working_dir}/{WMP_KUBERNETES_CONFIGURE_DIR}/Dockerfile", "w") as w:
            w.write(dockerfile)

    # .wmp/Jenkinsfile 0644
    if not os.path.exists(f"{working_dir}/{WMP_KUBERNETES_CONFIGURE_DIR}/Jenkinsfile"):
        registry = DEV_INFRACM_REGISTRY
        secretName = DEV_INFRACM_REGISTRY_SECRET_NAME

        jenkinsfileParams = JenkinsfileParams(
            project=params.project,
            name=params.name,
            branches=params.deploy.branches,
            targets=params.deploy.targets,
            dockerfile=f"{WMP_KUBERNETES_CONFIGURE_DIR}/Dockerfile",
            registry=registry,
            secretName=secretName,
        )
        jenkinsfile = gen_jenkinsfile(jenkinsfileParams)
        with open(
            f"{working_dir}/{WMP_KUBERNETES_CONFIGURE_DIR}/Jenkinsfile", "w"
        ) as w:
            w.write(jenkinsfile)

    # docker-entrypoint.sh 0755
    if not os.path.exists(f"{working_dir}/docker-entrypoint.sh"):
        docker_entrypoint = gen_docker_entrypoint()
        with open(f"{working_dir}/docker-entrypoint.sh", "w") as w:
            w.write(docker_entrypoint)
        os.chmod(f"{working_dir}/docker-entrypoint.sh", 0o755)

    # misc/apache-tomcat/conf/server.xml 0644
    if not os.path.exists(f"{working_dir}/misc/apache-tomcat/conf/server.xml"):
        os.makedirs(f"{working_dir}/misc/apache-tomcat/conf", exist_ok=True)
        tomcat_configs = gen_tomcat_config()
        with open(
            f"{working_dir}/misc/apache-tomcat/conf/server.xml",
            "w",
        ) as w:
            w.write(tomcat_configs)


def gen_cd_files(working_dir: str, params: PipelineBuilderParams):
    """
    CD file 을 생성
    - working_dir/wmp-spring-app/values/`project`/`service`/values-`env`.yaml

    Args:
        working_dir (str): dirpath
        params (PipelineBuilderParams)
    """
    root = f"{working_dir}/project/{params.project}"
    os.makedirs(root, exist_ok=True)

    tls_params = []
    for host in params.deploy.hosts:
        secretName = (
            "star.wemakeprice.kr"
            if re.search(r"\.kr$", host)
            else "star.wemakeprice.com"
        )
        tls_params.append(
            HelmValueIngressTlsParams(secretName=secretName, hosts=[host])
        )

    ingress_params = HelmValueIngressParams(
        enabled=True,  # 이건 항상 enabled
        klass="nginx-edge-nodeport" if params.deploy.bigip.enabled else "nginx",
        hosts=params.deploy.hosts,
        tls=tls_params,
    )

    # hosts 에서 .com 을 우선함
    # false 면 필요없고
    bigip_hostname = ""
    if params.deploy.bigip.enabled:
        for host in params.deploy.hosts:
            if re.search(r"\.com$", host):
                bigip_hostname = host
                break

        # .com 을 발견하지 못했을때에는..? 첫번째 값을 사용한다.
        if not bigip_hostname and len(params.deploy.hosts):
            bigip_hostname = params.deploy.hosts[0]

    node_patterns = []
    for target in params.deploy.targets:
        # BIG-IP 의 node 는 hostname 기반으로 등록하기에
        # worker-005.k8s-a.wmp.dev.wemakeprice.org
        # a-wmp-dev 클러스터라면 a.wmp.dev 로 치환한다.
        node_patterns.append(target.replace("-", "."))

    bigip_params = HelmValueBigipParams(
        enabled=params.deploy.bigip.enabled,
        environment=BIGIP_ENV_BY_ENV_MAP[params.env],
        hostname=bigip_hostname,
        nodeNamePatterns=node_patterns,
    )

    registry = DEV_INFRACM_REGISTRY
    secretName = DEV_INFRACM_REGISTRY_SECRET_NAME

    helm_value_params = HelmValueParams(
        project=params.project,
        service=params.name,
        namespace=params.deploy.namespace,
        replicaCount=params.deploy.replicaCount,
        env=params.env,
        image=HelmValueImageParams(
            url=registry,
            imagePullSecrets=[secretName],
            tag=ENV_TAG_MAP[params.env],
        ),
        ingress=ingress_params,
        pinpoint=params.deploy.pinpoint,
        bigip=bigip_params,
        spring=params.deploy.spring,
        resources=params.deploy.resources,
        healthcheck=params.deploy.healthcheck,
    )
    # wmp-spring-app charts
    if not os.path.exists(f"{root}/{params.name}"):
        chart_path = gen_wmp_spring_app_chart(params=helm_value_params)
        shutil.move(chart_path, f"{root}/{params.name}")

    # values-env.yaml 0644
    helm_values = gen_helm_values(helm_value_params)
    with open(f"{root}/{params.name}/values-{params.env}.yaml", "w") as w:
        w.write(helm_values)


def add_genfiles(git: Git, repo: Repo):
    """
    $ git add .

    Args:
        git (Git)
        repo (Repo)
    """
    git.add(repo=repo)


def commit_genfiles(git: Git, repo: Repo, message: str, author: str):
    """
    $ git commit -m <message> --author <author>

    Args:
        git (Git)
        repo (Repo)
        message (str)
        author (str)
    """
    git.commit(
        repo=repo,
        message=message,
        author=author,
    )


def merge_repo(git: Git, repo: Repo, branch: str, into: str, author: str):
    """
    merge `branch` branch into `into` branch
    $ git checkout into
    $ git merge branch
    $ git checkout branch # restore

    Args:
        git (Git)
        repo (Repo)
        branch (str)
        into (str)
        author (str): commit author info
    """
    git.merge(repo=repo, branch=branch, into=into, author=author)


def push_repo(git: Git, repo: Repo, remote: str, branch: str):
    """
    $ git push <remote> <branch>

    Args:
        git (Git)
        repo (Repo)
        remote (str)
        branch (str)
    """
    git.push(repo=repo, remote=remote, branch=branch)


def rmdir(dirpath: str):
    """
    $ rm -rf `dirpath`

    Args:
        dirpath (str)
    """
    shutil.rmtree(dirpath)


def create_pullrequest(
    pr_params: BitBucketPullRequestParams,
) -> BitbucketPullRequestPayload:
    """
    create pull request

    Args:
        pr_params (BitBucketPullRequestParams)
    """
    return PullRequest().create(pr_params)


def create_webhook(webhook_params: BitBucketWebhookParams) -> BitbucketWebhookItem:
    """
    create webhook

    Args:
        webhook_params (BitBucketWebhookParams)
    """
    return WebHook().create(webhook_params)


def build(params: PipelineBuilderParams, db: Session):
    """
    1. Create CI files to service repo
      - PR
      - Webhook
    2. Create CD files to configuration repo
      - PR
    """

    """
    1. Create CI files then PR
      - PR
        - clone repo
        - create `dockerize-by-infracm-yyyy-mm-dd` branch
        - gen files
        - add files and commit
        - push branch
        - Create Pull Request to app repo
      - Create Webhook which execute after this PR merged
    """

    teams = Teams()
    teams.info(f"[{params.project}/{params.name}] ({params.env}) started")

    git = Git()

    branch = f"dockerize-{params.env}-by-infracm-{datetime.today().strftime('%Y-%m-%dT%H%M%S')}"
    pr_params = BitBucketPullRequestParams(
        key=params.project.upper(),
        slug=params.name,
        title=f"[{params.project}/{params.name}] ({params.env}) 컨테이너 환경에서 사용될 CI/CD 메타 파일 추가",
        reviewer=settings.bitbucket_default_reviewer.split(","),
        branches=BitBucketPullRequestBranchParams(
            source=branch, destination=params.base
        ),
    )

    webhook_params = BitBucketWebhookParams(
        key=params.project.upper(),
        slug=params.name,
        secret=params.name,
        url=f"{WMP_INFRACM_WEBAPI_HOST_MAP_BY_ENV[params.env]}/webhooks/bitbucket",
    )

    # CI files
    try:
        repo = checkout(git=git, url=params.repo, base=params.base, branch=branch)
        gen_ci_files(working_dir=repo.working_dir, params=params)
        add_genfiles(git=git, repo=repo)
        commit_genfiles(
            git=git,
            repo=repo,
            message=f"[{params.project}/{params.name}] ({params.env}) Add Continuous Integration metafiles for container environment",
            author=INFRACM_AUTHOR_INFO,
        )
        merge_repo(
            git=git,
            repo=repo,
            branch=branch,
            into=ENV_BRANCH_MAP[params.env],
            author=INFRACM_AUTHOR_INFO,
        )
        push_repo(git=git, repo=repo, remote="origin", branch=branch)
        push_repo(
            git=git, repo=repo, remote="origin", branch=ENV_BRANCH_MAP[params.env]
        )
        rmdir(repo.working_dir)
        create_pullrequest(pr_params)
        create_webhook(webhook_params)
        logging.info(
            f"[{params.project}/{params.name}] ({params.env}) CI pipeline PR and Webhook created successfully"
        )
    except Exception as err:
        err_msg = f"[{params.project}/{params.name}] ({params.env}) Failed to create CI files and PR: {err}"
        logging.error(err_msg)
        teams.error(err_msg)
        return

    """
    2. Create CD files then PR
      - fetch deploy repo
      - create `configure-APPNAME-by-infracm-yyyy-mm-dd` branch
      - gen files
      - add files and commit
      - merge `branch` into `develop` (environment branch)
      - push branches
      - Create Pull Request to deploy repo
        - web-api 의 배포 환경에 따라.. develop or qa or staging or master <- feature
    """
    # CD files
    # FIXME: test 용도로 `base` branch 로 `develop` 을 사용
    branch = f"configure-{params.env}-{params.project}-{params.name}-by-infracm-{datetime.today().strftime('%Y-%m-%dT%H%M%S')}"
    try:
        repo = checkout(
            git=git,
            url=WMP_INFRACM_CD_CONFIGURATION_REPO_URL,
            base="master",  # master 어떤 환경이던지 브랜치로부터 분기
            branch=branch,
        )
        gen_cd_files(working_dir=repo.working_dir, params=params)
        add_genfiles(git=git, repo=repo)
        commit_genfiles(
            git=git,
            repo=repo,
            message=f"[{params.project}/{params.name}] ({params.env}) Add Continuous Delivery metafiles",
            author=INFRACM_AUTHOR_INFO,
        )
        merge_repo(
            git=git,
            repo=repo,
            branch=branch,
            into=ENV_BRANCH_MAP[params.env],
            author=INFRACM_AUTHOR_INFO,
        )
        push_repo(git=git, repo=repo, remote="origin", branch=branch)
        push_repo(
            git=git, repo=repo, remote="origin", branch=ENV_BRANCH_MAP[params.env]
        )
        rmdir(repo.working_dir)
        pr_params = BitBucketPullRequestParams(
            key=WMP_INFRACM_CD_REPO_KEY,
            slug=WMP_INFRACM_CD_REPO_SLUG,
            title=f"[{params.project}/{params.name}] ({params.env}) Add Continuous Delivery metafiles",
            reviewer=settings.bitbucket_default_reviewer.split(","),
            branches=BitBucketPullRequestBranchParams(
                source=branch, destination="master"
            ),
        )
        create_pullrequest(pr_params)
        logging.info(
            f"[{params.project}/{params.name}] ({params.env}) CD pipeline PR created successfully"
        )
        upsert_pipeline(db=db, params=params)
    except Exception as err:
        err_msg = f"[{params.project}/{params.name}] ({params.env}) Failed to create CD files and PR: {err}"
        logging.error(err_msg)
        teams.error(err_msg)
        return

    teams.info(f"[{params.project}/{params.name}] ({params.env}) done")


def configure(params: PipelineBuilderParams):
    """
    - CI/CD item 구성
    - wregistry 에 project 추가
    - TODO: kubernetes 클러스터에 namespace, secret 생성
    - jenkins 에 최초 build 를 유발
    - bitbucket 에 pr:merged webhook 을 제거
    - bitbucket 에 repo:refs_changed webhook 을 추가

    Args:
        params (PipelineBuilderParams)
    """
    settings = get_settings()
    env, key, slug = (settings.region, params.project, params.name)

    wh = WebHook()
    hooks = wh.list(key=key, slug=slug)
    for hook in hooks:
        if re.search(rf"^{DISPOSABLE_WEBHOOK_PREFIX}", hook.name):
            wh.delete(key=key, slug=slug, id=hook.id)
            break

    # serialize 해서 저장해놨다가 deserialize 해서 사용
    jenkinsJobParams = JenkinsJobParams(
        name=params.name,
        project=params.project,
        repo=params.repo,
        branch=ENV_BRANCH_MAP[params.env],
        script=".wmp/Jenkinsfile",
        targets=params.deploy.targets,
        argocdServer=settings.argocd_grpc_host,
    )

    agent = JenkinsAgent()
    folder_exists = False
    try:
        folder_exists = agent.exists(project=params.project)
    except Exception as err:
        err_msg = f"Failed to exists check jenkins folder: {params.project}"
        logging.error(err_msg)
        return

    if not folder_exists:
        if not agent.create_folder(name=params.project):
            err_msg = f"Failed to create jenkins folder: {params.project}"
            logging.error(err_msg)
            return

    if not agent.create(params=jenkinsJobParams):
        err_msg = f"Failed to create jenkins job: {params.project}/{params.name}"
        logging.error(err_msg)
        return

    jenkins_job_url = agent.job_url(project=params.project, name=params.name)
    webhook_params = BitBucketWebhookParams(
        key=params.project,
        slug=params.name,
        secret=f"{params.project}-{params.name}",  # 이 secret 은 repo:push webhook 의 token 으로 사용됨
        url=jenkins_job_url,
        name=f"{env}-jenkins-k8s",
        events=["repo:refs_changed"],
    )
    webhook_created = wh.create(params=webhook_params)
    if not webhook_created:
        err_msg = f"Failed to create webhook: {jenkins_job_url}"
        logging.error(err_msg)
        return

    # a-wmp-dev,b-wmp-dev 가 아님. 포맷 변경이 필요함
    # "a-wmp-dev","b-wmp-dev"  <- 이렇게 전달되어야 함
    targets = map(lambda target: f'"{target}"', params.deploy.targets)
    build_params = {"targetClusterList": ",".join(targets)}
    build_url = agent.perform_build(
        project=params.project, name=params.name, build_params=build_params
    )
    if not build_url:
        logging.error(f"Failed to perform build: {params.project}/{params.name}")
    else:
        logging.info(f"Perform a build: {build_url}")

    # TODO: k8s cluster 에 namespace 추가
    #       secret 을 namespace 에 생성
    #       이건 운영자가 미리 만들어둔다.
    #       kubectl 등을 통하지 않고 kubernetes API 를 직접 호출하는데에 부담이 있음

    # 4. argocd 에 item 추가
    argocd = Argocd()
    argocd_project_exists = False
    try:
        argocd_project_exists = argocd.exists_project(name=params.project)
    except Exception as error:
        err_msg = f"failed to exists check argocd project: {params.project}"
        logging.error(err_msg)
        return

    if not argocd_project_exists:
        argocd_project_params = ArgocdProjectParams(name=params.project, description="")
        created = argocd.create_project(params=argocd_project_params)
        if not created:
            err_msg = f"failed to create argocd project: {params.project}"
            logging.error(err_msg)
            return

    for target in params.deploy.targets:
        argocd_app_exists = False
        app_name = f"{params.project}-{params.name}-{target}"
        try:
            argocd_app_exists = argocd.exists_app(name=app_name)
        except Exception as error:
            err_msg = f"failed to exists check argocd app: {app_name}"
            logging.error(err_msg)
            return

        if not argocd_app_exists:
            argocd_app_params = ArgocdAppParams(
                name=params.name,
                project=params.project,
                branch=ENV_BRANCH_MAP[params.env],
                targets=[target],
                values=[
                    "values.yaml",
                    f"values-{env}.yaml",
                ],
            )
            created = argocd.create_app(params=argocd_app_params)
            if not created:
                err_msg = f"failed to create argocd app: {params.name}"
                logging.error(err_msg)
                return

    logging.info(f"{params.project}/{params.name} configured")
