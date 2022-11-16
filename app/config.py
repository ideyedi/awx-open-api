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

tags_metadata = [
    {
        "name": "awx",
        "description": "AWX 관련 업무 크롤링을 통한 자동화"
    }
]


class Settings(BaseSettings):
    """
    project 'SRE Crawler API'
    infra-DevOps 메일링 주소..
    OpenAPI tags는 타입 명시를 뭐로 해야하지..
    """
    app_name: str = "sre-crawling-api"
    admin_email: str = "wmporg_distribution@wemakeprice.com"
    app_description: str = "WeMakePrice SRE Automation restful API"
    app_version: str
    docs_url: str
    openapi_tags = tags_metadata
