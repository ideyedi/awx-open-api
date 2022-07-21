from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from ..models.params import ArgocdAppParams, ArgocdProjectParams
from ..services.argocd import Argocd

router = APIRouter(prefix="/argocd", tags=["Argocd"])
argocd = Argocd()


@router.post("/applications", response_class=PlainTextResponse)
def create_app(params: ArgocdAppParams):
    """
    argocd의 application을 생성 합니다.
    """
    argocd_url = argocd.create_app(params)
    if not argocd_url:
        raise HTTPException(
            status_code=500, detail="Failed to create a argcod application"
        )

    return argocd_url


@router.delete("/applications/{name}")
def delete_app(name: str):
    """
    argocd의 application을 삭제 합니다.
    """
    argocd_url = argocd.delete_app(name)
    if not argocd_url:
        raise HTTPException(
            status_code=500, detail="Failed to delete a argcod application"
        )

    return argocd_url


@router.post("/projects", response_class=PlainTextResponse)
def create_project(params: ArgocdProjectParams):
    """
    argocd의 project를 생성 합니다.
    """
    argocd_url = argocd.create_project(params)
    if not argocd_url:
        raise HTTPException(status_code=500, detail="Failed to create a argcod project")

    return argocd_url


@router.delete("/projects/{name}")
def delete_project(name: str):
    """
    argocd의 project를 삭제 합니다.
    """
    argocd_url = argocd.delete_project(name)
    if not argocd_url:
        raise HTTPException(status_code=500, detail="Failed to delete a argcod project")

    return argocd_url
