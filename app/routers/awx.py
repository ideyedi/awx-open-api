import requests
import logger
from app.config import (AWX_URL_TUPLE,
                        )

from fastapi import APIRouter, status
from fastapi.responses import (PlainTextResponse,
                               )
from app.worker.tasks import (make_sourced_inventory,
                              )
from app.errors import (raise_error,
                        )

router = APIRouter(prefix="/awx", tags=["awx"])


@router.post('/inventory/source', response_class=PlainTextResponse)
def make_source(app_name: str, profile: str, project: str):
    """
    Async task to make source inventory
    @param app_name: service application name
    @param profile: profile name, (e.g. dev, qa, stg, prod)
    @param project: Ansible AWX project name
    """
    task = make_sourced_inventory.delay(app_name, profile, project)
    print(f' Async object: task {task}')

    return "OK"


@router.post('/unittest/sync/source')
def test(app_name="nd-sre-api", profile="dev", project="develop"):
    """
    Syncronize 동작을 확인하기 위한 테스트 함수
    """
    task = make_sourced_inventory(app_name, profile, project)
    print(f' Sync api result: {task}')
    return True


@router.post('/project/update')
def update_project():
    """
    AWX project update 동작 한번에 처리
    Retuen response_class HTTP status code로 지정하는 방법 고민 좀
    """
    endpoints: str = ["/api/v2/projects/", "/update/"]
    oauth2_token = "lXhCWAnf9cVIw67JJlex4PZL2PmMjz"

    # awx project index
    index = str(8)

    awx_url = AWX_URL_TUPLE[0] + endpoints[0] + index + endpoints[1]
    sess = requests.session()

    print(f'{awx_url}')
    ret = sess.get(AWX_URL_TUPLE[0] + "/api/login")

    headers = {
        'Authorization': 'Bearer ' + oauth2_token,
        'content-type': 'application/json'
    }
    r = sess.post(awx_url, headers=headers)
    print(r)
    print(f"{r.status_code}\n {r.headers}\n {r.cookies}")
    return ret
