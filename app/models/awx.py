from pydantic import BaseModel
from app.config import (AWX_URLS,
                        OAUTH2_TOKENS,
                        AWX_PROJECT_IDX,
                        AWX_HOST_FILTER,
                        AWX_INVENTORY_IDX)


class AwxInfo(BaseModel):
    """
    각 환경 AWX에 대한 정보를 관리한다.
    (deprecated)
    """
    profile: str
    url: str
    token: str
    project_idx: int


class AWXModel(BaseModel):
    """

    """
    profile: str
    url = AWX_URLS['dev']
    api_token = OAUTH2_TOKENS['dev']

    project_idx = AWX_PROJECT_IDX['dev']
    inventory_idx = AWX_INVENTORY_IDX['dev']
    host_filter = AWX_HOST_FILTER['dev']

