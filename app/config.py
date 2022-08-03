from pydantic import BaseSettings
from typing import Optional
from typing_extensions import Literal

REGIONS = Literal["dev", "qa", "stg", "prod"]
BIGIP_ENV = Literal["development", "qa", "staging", "production"]
TARGETS = Literal[
    "a-wmp-dev", "b-wmp-dev", "a-azure-dev", "b-azure-dev", "b-gcp-dev", "a-wmp-stg"
]
ENV_BRANCH_MAP = {
    "dev": "develop",
    "qa": "release/qa",
    "stg": "release/stg",
    "prod": "master",
    # fallback
    "develop": "develop",
    "development": "develop",
    "staging": "release/stg",
    "production": "master",
}

ENV_TAG_MAP = {
    "dev": "develop",
    "qa": "qa",
    "stg": "stg",
    "prod": "prod",
}

ARGOCD_TARGET_REVISION_BY_REGION = {
    "dev": "develop",
    "qa": "release/qa",
    "stg": "release/stg",
    "prod": "master",
}

BIGIP_ENV_BY_ENV_MAP = {
    "dev": "development",
    "qa": "qa",
    "stg": "staging",
    "prod": "production",
    # fallback
    "staging": "staging",
}

WREGISTRY = "wregistry.wemakeprice.com"
WREGISTRY_SECRET_NAME = "wregistry"
DEV_INFRACM_REGISTRY = "devinfracmconreg.azurecr.io"
DEV_INFRACM_REGISTRY_SECRET_NAME = "devinfracmconreg"


class Settings(BaseSettings):
    region: Optional[REGIONS] = "dev"

    #bigip_enabled: str
    #bigip_host: str
    #bigip_username: str
    #bigip_password: str
    #bigip_snatpool: str

    #jenkins_host: str
    #jenkins_username: str
    #jenkins_token: str

    #argocd_host: str
    #argocd_grpc_host: str
    ## deprecated
    #argocd_token: str
    #argocd_username: str
    #argocd_password: str

    #rancher_host: str
    #helm_repo: str

    #db_host: str
    #db_user: str
    #db_password: str
    #db_name: str

    db_trace: Optional[int] = 0

    # http://jira.wemakeprice.com/browse/K8S-327
    # DB 의 wait_timeout 보다 작게 설정해야 함.
    # DB 의 wait_timeout 동안 request 가 없으면 connection 이 끊어짐.
    # dev 환경의 wait_timeout: 28800.
    pool_recycle: Optional[int] = 14400

    #bitbucket_token: str
    #bitbucket_username: str
    #bitbucket_password: str
    #bitbucket_default_reviewer: str  # comma seperated

    #harbor_username: str
    #harbor_password: str

    #pipeline_webhook: str

    #cors_allow_origins: str

    class Config:
        env_file = ".env"


def get_settings():
    return Settings()

