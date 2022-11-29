import requests
import logger

from typing import Optional
from app.config import (AWX_URLS,
                        OAUTH2_TOKENS,
                        AWX_PROJECT_IDX,
                        )
from app.models.awx import AwxInfo

from fastapi import (APIRouter,
                     status,
                     HTTPException,
                     )
from fastapi.responses import PlainTextResponse
from app.worker.tasks import make_sourced_inventory
from app.services.awx import update_awx_project

router = APIRouter(prefix="/awx", tags=["awx"])


@router.post('/inventory/source', response_class=PlainTextResponse)
def make_source(app_name: str, profile: str, project: str):
    """
    Async task to make source inventory
    @param app_name: service application name
    @param profile: profile name, (e.g. dev, qa, stg, prod)
    @param project: Ansible AWX project name
    """
    task = make_sourced_inventory.delay(app_name, profile, project)
    print(f' Async object: task {task}')

    return "OK"


#@router.post('/unittest/sync/source')
def test(app_name="nd-sre-api", profile="dev", project="develop"):
    """
    Syncronize 동작을 확인하기 위한 테스트 함수
    """
    task = make_sourced_inventory(app_name, profile, project)
    print(f' Sync api result: {task}')
    return True


@router.patch('/project')
def update_project(profile: Optional[str] = None):
    """
    AWX project update 동작을 수행
    profile 값이 없을 경우, 모든 환경의 기본 프로젝트 업데이트
    """
    ret = None
    regions = ['dev', 'qa', 'stg', 'prod']

    if profile is None:
        for item in regions:
            ret = update_awx_project(item)
            # Error Handling
            if ret.status_code != status.HTTP_202_ACCEPTED:
                raise HTTPException(status_code=ret.status_code, detail="")

    else:
        profile = profile.lower()
        ret = update_awx_project(profile)

    if ret.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=ret.status_code, detail="Not founded AWX Project")

    return {"ret": ret.status_code}


@router.patch('/project/{project_idx}', status_code=status.HTTP_202_ACCEPTED)
async def update_specific_project(profile: str, project_idx):
    """
    Pre-defined project가 아닌 특정 index의 프로젝트를 업데이트할 때 사용합니다.
    """
    ret = update_awx_project(profile, project_idx)
    if ret.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=ret.status_code, detail="Not founded AWX Project")

    return {"ret": ret.status_code}
