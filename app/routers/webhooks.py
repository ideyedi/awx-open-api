import logging
from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from ..config import get_settings
from ..errors import raise_error
from ..dependencies import get_db

from ..dao.pipeline import find as find_pipeline

from ..services.bitbucket import WebHook
from ..services.pipeline_builder import configure

from ..models.params import (
    BitbucketWebhookItem,
    BitbucketMergeEventPayload,
    PipelineBuilderParams,
)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/bitbucket", response_class=PlainTextResponse)
async def bitbucket(
    payload: BitbucketMergeEventPayload,
    tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    bitbucket 의 webhook `pr:merged` event 가 발생

    1. 자신을 호출한 webhook 을 제거
    2. Jenkins 에 item 추가
    3. 추가된 item 에 build trigger
    4. argocd 에 item 추가
    """
    settings = get_settings()
    env, key, slug = (
        settings.region,
        payload.pullRequest.fromRef.repository.project.key,
        payload.pullRequest.fromRef.repository.slug,
    )

    # web-api 가 자신의 환경을 알아야 함.
    pipeline = find_pipeline(db=db, env=env, key=key, slug=slug)
    if not pipeline:
        raise_error(404, f"pipeline not found: {env}/{key}/{slug}")

    params = PipelineBuilderParams(**pipeline.raw)
    tasks.add_task(configure, params)
    return "Configure task added"


@router.get("/")
def webhooks(key: str, slug: str) -> List[BitbucketWebhookItem]:
    """
    Bitbucket webhook list by `key` and `slug`
    """
    return WebHook().list(key=key.upper(), slug=slug)
