from fastapi import APIRouter
from fastapi.responses import (PlainTextResponse,
                               )
from app.worker.tasks import (make_sourced_inventory,
                              )

router = APIRouter(prefix="/awx", tags=["awx"])


@router.post('/inventory/source', response_class=PlainTextResponse)
def make_source(app_name="nd-sre-api", profile="dev", project="develop"):
    task = make_sourced_inventory.delay(app_name, profile, project)
    print(f' Async object: task {task}')

    return "OK"


@router.post('/unittest/sync/source')
def test(app_name="nd-sre-api", profile="dev", project="develop"):
    task = make_sourced_inventory(app_name, profile, project)
    print(f' Sync api result: {task}')
    return True
