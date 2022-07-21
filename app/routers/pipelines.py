import re
from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models.params import PipelineBuilderParams
from ..services.pipeline_builder import build as build_pipelines

router = APIRouter(prefix="/pipelines", tags=["Pipelines"])


@router.post("/", response_class=PlainTextResponse)
async def create(
    params: PipelineBuilderParams, tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    """
    컨테이너 운영 환경의 CI/CD pipeline 을 생성 합니다.
    - app 저장소에 Dockerize PR 생성
    - Jenkins item 추가
    - Bitbucket 에 webhook 추가
    - Argocd 에 app 추가
    """

    # TODO: more powerful validation
    # bitbucket key, slug 는 repo 로 부터 유추 가능
    # repo: format ssh://git@bitbucket.wemakeprice.com:7999/infcm/web-api.git
    matched = re.search(
        r"^ssh://git@(?:bitbucket|stash)\.wemakeprice\.com:7999/([^/]+)/([^\.]+).git$",
        params.repo,
    )
    if not matched:
        raise HTTPException(status_code=418, detail="repo should be ssh url")

    params.project, params.name = matched.groups()
    tasks.add_task(build_pipelines, params, db)
    return "Pipeline enqueued in background tasks"
