import requests

from typing import Optional

from app.models.awx import AwxInfo
from app.config import (AWX_URLS,
                        OAUTH2_TOKENS,
                        AWX_PROJECT_IDX,
                        )


def update_awx_project(profile: str, index: Optional[int] = None):
    endpoints: str = ["/api/v2/projects/", "/update/"]

    sess = requests.session()

    profile = profile.lower()
    awx_info = AwxInfo(profile=profile,
                        url=AWX_URLS[profile],
                        token=OAUTH2_TOKENS[profile],
                        project_idx=AWX_PROJECT_IDX[profile])

    print(f'parameter index: {index}')
    if index is not None:
        awx_info.project_idx = index

    req_address = awx_info.url + endpoints[0] + str(awx_info.project_idx) + endpoints[1]

    headers = {
        'Authorization': 'Bearer ' + awx_info.token,
        'content-type': 'application/json'
    }

    ret = sess.post(req_address, headers=headers)
    print(f'ret: {ret.status_code, ret.reason}')

    return ret
