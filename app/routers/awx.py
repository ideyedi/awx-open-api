<<<<<<< HEAD
import logging
from typing import Optional

=======
import requests
import logger

from typing import Optional
from app.config import (AWX_URLS,
                        OAUTH2_TOKENS,
                        AWX_PROJECT_IDX,
                        )
from app.models.awx import AwxInfo

>>>>>>> 59b144e169f077cadef673161dcf97775c1f0a10
from fastapi import (APIRouter,
                     status,
                     HTTPException,
                     )
<<<<<<< HEAD

=======
from fastapi.responses import PlainTextResponse
>>>>>>> 59b144e169f077cadef673161dcf97775c1f0a10
from app.worker.tasks import make_sourced_inventory
from app.services.awx import update_awx_project

router = APIRouter(prefix="/awx", tags=["awx"])

"""
@router.post('/unittest/sync/source')
def test(app_name="nd-sre-api", profile="dev", project="develop"):
    task = make_sourced_inventory(app_name, profile, project)
    print(f' Sync api result: {task}')
    return JSONResponse(content=task)
"""

@router.post('/inventory/source')
def make_source(app_name: str, profile: str, project: str):
    """
    Async task to make source inventory
    @param app_name: service application name
    @param profile: profile name, (e.g. dev, qa, stg, prod)
    @param project: Ansible AWX project name
    """
    task_hash = make_sourced_inventory.delay(app_name, profile, project)
    logging.INFO(task_hash)
    return task_hash


<<<<<<< HEAD
@router.patch('/project', status_code=status.HTTP_202_ACCEPTED)
def update_project(profile: Optional[str] = None):
=======
#@router.post('/unittest/sync/source')
def test(app_name="nd-sre-api", profile="dev", project="develop"):
>>>>>>> 59b144e169f077cadef673161dcf97775c1f0a10
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


<<<<<<< HEAD
@router.patch('/project/{project_idx}', status_code=status.HTTP_202_ACCEPTED)
async def update_specific_project(profile: str, project_idx):
    """
    Pre-defined project가 아닌 특정 index의 프로젝트를 업데이트할 때 사용합니다.
    """
    ret = update_awx_project(profile, project_idx)
    if ret.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=ret.status_code, detail="Not founded AWX Project")

=======
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

>>>>>>> 59b144e169f077cadef673161dcf97775c1f0a10
    return {"ret": ret.status_code}
