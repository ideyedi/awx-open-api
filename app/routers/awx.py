import logging
from typing import Optional

from fastapi import (APIRouter,
                     status,
                     HTTPException,
                     )

from app.worker.tasks import make_sourced_inventory
import app.services.awx as awx

router = APIRouter(prefix="/awx", tags=["awx"])


@router.post('/inventory/source', status_code=status.HTTP_201_CREATED)
def create_sourced_inventory(app_name: str, profile: str, project: str):
    """
    Async task to make source inventory
    @param app_name: service application name
    @param profile: profile name, (e.g. dev, qa, stg, prod)
    @param project: Ansible AWX project name
    """
    #if profile.lower() == "dev" or profile.lower() == "prod":
    #    task_hash = make_sourced_inventory.delay(app_name, profile, project)
    #    logging.INFO(task_hash)

    #else:
    app_name = app_name.lower()
    profile = profile.lower()
    project = project.lower()
    ret = awx.create_awx_inventory_sources(app_name, profile, project)

    return ret.json()


@router.patch('/project', status_code=status.HTTP_202_ACCEPTED)
def update_project(profile: Optional[str] = None):
    """
    AWX project update 동작을 수행
    profile 값이 없을 경우, 모든 환경의 기본 프로젝트 업데이트
    """
    ret = None
    regions = ['dev', 'qa', 'stg', 'prod']

    if profile is None:
        for item in regions:
            ret = awx.update_awx_project(item)
            # Error Handling
            if ret.status_code != status.HTTP_202_ACCEPTED:
                raise HTTPException(status_code=ret.status_code, detail="")

    else:
        profile = profile.lower()
        ret = awx.update_awx_project(profile)

    if ret.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=ret.status_code, detail="Not founded AWX Project")

    return {"ret": ret.status_code}


@router.patch('/project/{project_idx}', status_code=status.HTTP_202_ACCEPTED)
async def update_specific_project(profile: str, project_idx):
    """
    Pre-defined project가 아닌 특정 index의 프로젝트를 업데이트할 때 사용합니다.
    """
    ret = awx.update_awx_project(profile, project_idx)
    if ret.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=ret.status_code, detail="Not founded AWX Project")

    return {"ret": ret.status_code}


"""
@router.post('/unittest/sync/source')
def test(app_name="nd-sre-api", profile="dev", project="develop"):
    task = make_sourced_inventory(app_name, profile, project)
    print(f' Sync api result: {task}')
    return JSONResponse(content=task)
"""