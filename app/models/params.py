from pydantic import BaseModel
from typing import List, Optional
from typing_extensions import Literal
from ..config import REGIONS, TARGETS, ENV_BRANCH_MAP, BIGIP_ENV

PINPOINT_VERSION = "2.0.4"
GRADLE_VERSION = "jdk8"
MAVEN_VERSION = "3-jdk-8"
TOMCAT_VERSION = "8.5-jdk8"
EXPOSE = 8080
HARBOR_ROLE_MAP = {
    "admin": 1,
    "projectAdmin": 1,
    "developer": 2,
    "guest": 3,
    "master": 4,
}


class JenkinsfileParams(BaseModel):
    project: str
    name: str
    dockerfile: Optional[str] = "Dockerfile"
    branches: List[str] = ["develop", "release/qa", "release/stg", "master"]
    targets: List[str] = ["b-azure-dev"]
    registry: str = "devinfracmconreg.azurecr.io"
    secretName: str = "devinfracmconreg"


class DockerfilePinpointParams(BaseModel):
    version: str


class DockerfileGradleParams(BaseModel):
    enabled: bool
    version: str


class DockerfileMavenParams(BaseModel):
    enabled: bool
    version: str


class DockerfileTomcatParams(BaseModel):
    version: str


class DockerfileTestParams(BaseModel):
    skip: bool


class DockerfileBuildOptions(BaseModel):
    tool: Literal["gradle", "maven"] = "gradle"
    command: str = ""
    args: str = ""
    src: str = "src"
    artifact: str = "build/libs/*.jar"


class DockerfileParams(BaseModel):
    name: str
    build: DockerfileBuildOptions
    starter: Literal["tomcat", "embedded"] = "tomcat"


class DockerfileDefaultParams(BaseModel):
    pinpoint: Optional[DockerfilePinpointParams] = {"version": PINPOINT_VERSION}
    gradle: Optional[DockerfileGradleParams] = {
        "enabled": False,
        "version": GRADLE_VERSION,
        "build": {
            "tool": "gradle",
            "command": "./gradlew clean build -x test",
            "args": "",
            "src": "src",
            "artifact": "build/libs/*.jar",
        },
    }
    maven: Optional[DockerfileMavenParams] = {
        "enabled": False,
        "version": MAVEN_VERSION,
        "build": {
            "tool": "maven",
            "command": "mvn package -s ./settings.xml",
            "args": "",
            "src": "src",
            "artifact": "build/libs/*.jar",
        },
    }
    tomcat: Optional[DockerfileTomcatParams] = {"version": TOMCAT_VERSION}
    expose: Optional[int] = 8080


class HelmValueImageParams(BaseModel):
    url: str = "devinfracmconreg.azurecr.io"
    imagePullSecrets: List[str] = ["devinfracmconreg"]
    tag: str = "latest"


class HelmValueIngressTlsParams(BaseModel):
    secretName: str
    hosts: List[str]


class HelmValueIngressParams(BaseModel):
    enabled: bool = True
    klass: Literal["nginx", "nginx-edge-nodeport"] = "nginx"
    hosts: Optional[List[str]]
    tls: Optional[List[HelmValueIngressTlsParams]]


class HelmValueSpringAppParams(BaseModel):
    opts: str = ""


class HelmValuePinpointParams(BaseModel):
    enabled: bool = True


class HelmValueResourceParams(BaseModel):
    cpu: str = "2000m"
    memory: str = "2048Mi"


class HelmValueResourcesParams(BaseModel):
    limits: HelmValueResourceParams
    requests: HelmValueResourceParams


class HelmValueHealthCheckParams(BaseModel):
    enabled: bool = True
    path: str = "/servicemanager/health"
    initialDelaySeconds: int = 100
    timeoutSeconds: int = 3
    failureThreshold: int = 5


class HelmValueBigipParams(BaseModel):
    enabled: bool = False
    environment: Literal[BIGIP_ENV] = "development"
    hostname: str = ""
    nodeNamePatterns: List[str] = ["a.wmp.dev"]


class HelmValueParams(BaseModel):
    project: str
    service: str
    namespace: str
    replicaCount: int = 1
    env: REGIONS = "dev"
    image: HelmValueImageParams
    ingress: HelmValueIngressParams
    pinpoint: HelmValuePinpointParams
    bigip: HelmValueBigipParams
    spring: HelmValueSpringAppParams
    resources: HelmValueResourcesParams
    healthcheck: HelmValueHealthCheckParams


class JenkinsJobParams(BaseModel):
    name: str
    project: str
    repo: str
    branch: str = "develop"
    script: Optional[str] = "Jenkinsfile"
    targets: Optional[List[TARGETS]] = ["b-azure-dev"]
    argocdServer: str


class ArgocdAppParams(BaseModel):
    name: str
    project: str
    branch: str = "develop"
    targets: Optional[List[TARGETS]] = ["b-azure-dev"]
    path: Optional[str] = ""
    values: Optional[List[str]] = []


class ArgocdProjectParams(BaseModel):
    name: str
    description: str


class BitBucketPullRequestBranchParams(BaseModel):
    source: str
    destination: str = "master"


class BitBucketPullRequestParams(BaseModel):
    key: str
    slug: str
    branches: BitBucketPullRequestBranchParams
    reviewer: Optional[List[str]] = []
    title: Optional[str] = "컨테이너 환경에서 사용될 CI/CD 메타 파일 추가"
    description: Optional[
        str
    ] = """이 PR 은 자동으로 생성되었습니다.

WMP 의 Kubernetes 플랫폼에서 운영하기 위한 필수 CI/CD 메타파일을 추가하였습니다."""


# 일회용 webhook 임을 알리는 prefix
DISPOSABLE_WEBHOOK_PREFIX = "infracm-disposable"


class BitBucketWebhookParams(BaseModel):
    key: str
    slug: str
    secret: str
    url: str
    name: str = f"{DISPOSABLE_WEBHOOK_PREFIX}-pipeline-builder"
    events: Optional[List[Literal["pr:merged", "repo:refs_changed"]]] = ["pr:merged"]


class BitbucketWebhookItem(BaseModel):
    id: int
    name: str
    url: str
    active: bool
    events: List[str]
    createdDate: int  # epoch
    updatedDate: int  # epoch


class BitbucketMergeEventPayloadActor(BaseModel):
    id: int
    name: str
    emailAddress: str
    displayName: str
    active: bool
    slug: str  # user
    type: str  # NORMAL


class BitbucketMergeEventPayloadProject(BaseModel):
    id: int
    key: str
    name: str
    public: bool
    type: str  # NORMAL


class BitbucketMergeEventPayloadRepository(BaseModel):
    id: int
    slug: str
    name: str
    scmId: str  # git
    state: str
    statusMessage: str
    forkable: bool
    project: BitbucketMergeEventPayloadProject
    public: bool


class BitbucketMergeEventPayloadRef(BaseModel):
    id: str
    displayId: str
    latestCommit: str
    repository: BitbucketMergeEventPayloadRepository


class BitbucketPullRequestPayload(BaseModel):
    id: int
    version: int
    title: str
    state: str  # MERGED
    open: bool
    closed: bool
    createdDate: int  # epoch
    updatedDate: int  # epoch
    fromRef: BitbucketMergeEventPayloadRef
    toRef: BitbucketMergeEventPayloadRef
    locked: bool
    # 나머지 생략


class BitbucketMergeEventPayloadPullRequest(BitbucketPullRequestPayload):
    pass


# https://confluence.atlassian.com/bitbucketserver063/event-payload-972354401.html?utm_campaign=in-app-help&utm_medium=in-app-help&locale=ko_KR%2Cko&utm_source=stash#Eventpayload-repositoryevents
class BitbucketMergeEventPayload(BaseModel):
    eventKey: str  # pr:merged
    date: str
    actor: BitbucketMergeEventPayloadActor
    pullRequest: BitbucketMergeEventPayloadPullRequest


class PipelineBuilderDeployBigipParams(BaseModel):
    enabled: bool = False


class PipelineBuilderDeployParams(BaseModel):
    namespace: str
    replicaCount: int = 1
    branches: List[str] = ["develop", "release/qa", "release/stg", "master"]
    targets: Optional[List[TARGETS]] = ["b-azure-dev"]
    hosts: List[str]
    bigip: PipelineBuilderDeployBigipParams
    pinpoint: HelmValuePinpointParams
    spring: HelmValueSpringAppParams
    resources: HelmValueResourcesParams
    healthcheck: HelmValueHealthCheckParams


class PipelineBuilderParams(BaseModel):
    # environment
    env: REGIONS = "dev"
    repo: str
    base: str = "master"

    # service name
    # repo 로 부터 유추 가능함
    name: Optional[str] = ""
    project: Optional[str] = ""

    # Dockerfile
    build: DockerfileBuildOptions
    starter: Literal["tomcat", "embedded"] = "tomcat"

    # deploy
    deploy: PipelineBuilderDeployParams


class HarborProjectMetadata(BaseModel):
    enable_content_trust: bool
    auto_scan: bool
    severity: Literal["none", "low", "medium", "high", "critical"]
    reuse_sys_cve_whitelist: str
    public: str
    prevent_vul: str


class HarborCVEWhitelistItem(BaseModel):
    cve_id: str


class HarborCVEWhitelist(BaseModel):
    project_id: int
    id: int
    expires_at: int
    items: List[HarborCVEWhitelistItem]


class HarborProjectReq(BaseModel):
    project_name: str
    count_limit: int = 0
    storage_limit: int  # byte
    cve_whitelist: Optional[HarborCVEWhitelist]
    metadata: Optional[HarborProjectMetadata]


class HarborUserEntity(BaseModel):
    # 둘 다 optional 은 아니지만..
    # 둘 중 하나만 입려되면 된다.
    username: Optional[str]
    user_id: Optional[int]


class HarborUserGroup(BaseModel):
    id: int
    group_name: str
    ldap_group_dn: str
    group_type: int


class HarborProjectMember(BaseModel):
    # The role id 1 for projectAdmin, 2 for developer, 3 for guest, 4 for master
    # use HARBOR_ROLE_MAP
    role_id: int

    # 둘중 하나만 있으면 됨
    member_group: Optional[HarborUserGroup]
    member_user: Optional[HarborUserEntity]
