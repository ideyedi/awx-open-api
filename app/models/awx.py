from pydantic import BaseModel


class AwxInfo(BaseModel):
    """
    각 환경 AWX에 대한 정보를 관리한다.
    """
    profile: str
    url: str
    token: str
    project_idx: int
