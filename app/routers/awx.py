from fastapi import APIRouter
from fastapi.responses import (PlainTextResponse,)
from app.worker.tasks import (add,
                              make_sourced_inventory
                              )

router = APIRouter(prefix="/awx", tags=["awx"])


@router.post('/inventory/source', response_class=PlainTextResponse)
def make_source(app_name="nd-sre-api", profile="dev", project="develop"):
    task = make_sourced_inventory.delay(app_name, profile, project)
    print(f' Async object: task {task}')

    return "OK"


@router.get('/test')
def test(app_name="nd-sre-api", profile="dev", project="develop"):
    task = make_sourced_inventory(app_name, profile, project)
    return True
