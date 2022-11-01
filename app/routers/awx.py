from fastapi import APIRouter
from fastapi.responses import (PlainTextResponse,)

from ..services.awx import (AnsibleCrawler,
                            )
import logging

router = APIRouter(prefix="/awx", tags=["awx"])


@router.post('/inventory/source', response_class=PlainTextResponse)
def make_source(app_name, profile, awx_project):
    ret = "OK"
    crawler = AnsibleCrawler(app_name, profile, awx_project)
    ret = crawler.make_inven()
    return ret


@router.post("/worker/test")
def test():
    logging.info(f'Celery Worker Test')

    return 0
