from fastapi import APIRouter
from fastapi.responses import (PlainTextResponse,
                               )

router = APIRouter(prefix='/pinpoint', tags=["pinpoint"])


@router.get('/test', response_class=PlainTextResponse)
def get_host_info():

    return "OK"