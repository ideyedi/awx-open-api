from fastapi import APIRouter
from fastapi.responses import (PlainTextResponse,)

from ..services.awx import (AnsibleCrawler,
                            )

router = APIRouter(prefix="/awx", tags=["awx"])
crawler = AnsibleCrawler()


@router.post('/inventory/source', response_class=PlainTextResponse)
def make_source():
    ret = "OK"

    return ret

