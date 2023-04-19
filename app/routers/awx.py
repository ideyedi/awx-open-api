from typing import Optional

from fastapi import (APIRouter,
                     status,
                     HTTPException,
                     )

import app.services.awx as awx
router = APIRouter(prefix="/awx", tags=["awx"])


@router.post('/inventory/source', status_code=status.HTTP_201_CREATED)
def create_sourced_inventory(app_name: str, profile: str, project: str):
    """
    Create AWX Sourced inventory
    @param app_name: 생성하고자 하는 어플리케이션 이름
    @param profile: 서비스 프로파일, (e.g. dev, qa, stg, prod)
    @param project: Ansible AWX의 프로젝트
    """
    app_name = app_name.lower()
    profile = profile.lower()
    project = project.lower()
    ret = awx.create_awx_inventory_sources(app_name, profile, project)

    return {"result": ret.status_code}


@router.patch('/inventory/source', status_code=status.HTTP_200_OK)
def change_sourced_inventory_branch(profile: Optional[str] = None, app_name=""):
    """
    Application name (sourced inventory name)을 기준으로 해당 인덱스를 찾아
    머지 프로젝트로 브랜치를 변경하는 함수
    """
    idx = awx.search_source_inventory(profile=profile, app_name=app_name)
    print(f"project idx: {idx}")
    ret = awx.change_awx_sourced_inventory_branch(profile, idx)
    print(f"r: {ret.json()}")

    return {"result": ret.status_code}


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
            if ret.status_code != status.HTTP_202_ACCEPTED:
                raise HTTPException(status_code=ret.status_code, detail="")

    else:
        profile = profile.lower()
        ret = awx.update_awx_project(profile)

    # Error Handling
    if ret.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=ret.status_code, detail="Not founded AWX Project")

    return {"ret": ret.status_code}


@router.patch('/project/{project}', status_code=status.HTTP_202_ACCEPTED)
async def update_specific_project(profile: str, project):
    """
    Pre-defined project가 아닌 특정 AWX 프로젝트를 업데이트
    """
    project_idx = awx.search_project_idx(profile=profile, awx_project=project)
    ret = awx.update_awx_project(profile, project_idx)
    if ret.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=ret.status_code, detail="Not founded AWX Project")

    return {"ret": ret.status_code}

