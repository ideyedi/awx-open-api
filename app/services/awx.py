import json
import requests

from fastapi import status
from typing import Optional

from app.models.awx import AwxInfo
from app.config import (AWX_URLS,
                        OAUTH2_TOKENS,
                        AWX_PROJECT_IDX,
                        AWX_INVENTORY_IDX,
                        AWX_HOST_FILTER,
                        )

from app.errors import (AWXProjectNotFoundException,
                        AWXProjectNotCreatedException,
                        )


def update_awx_project(profile: str, index: Optional[int] = None):
    """
    Update AWX Projects
    """
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


def search_project_idx(profile, awx_project):
    """
    Searching to project index number using name
    """
    idx = 0
    sess = requests.session()

    awx_info = AwxInfo(profile=profile,
                       url=AWX_URLS[profile],
                       token=OAUTH2_TOKENS[profile],
                       project_idx=AWX_PROJECT_IDX[profile])
    req_url = awx_info.url + "/api/v2/projects?search=" + awx_project

    headers = {
        'Authorization': 'Bearer ' + awx_info.token,
        'content-type': 'application/json'
    }

    response = sess.get(req_url, headers=headers)
    cnt = response.json().get('count')
    infos = response.json().get('results')

    if cnt == 0:
        print(f"Not founded project {awx_project}")
        raise AWXProjectNotFoundException

    idx = infos[0].get('id', 0)
    return idx


def create_awx_inventory_sources(app_name, profile, project):
    """
    Create inventory sources using AWX OpenAPI
    """
    endpoints: str = ["/api/v2/inventories/", "/inventory_sources/", "/update_inventory_sources/"]
    sess = requests.session()

    awx_info = AwxInfo(profile=profile,
                       url=AWX_URLS[profile],
                       token=OAUTH2_TOKENS[profile],
                       project_idx=AWX_PROJECT_IDX[profile])

    req_address = awx_info.url + endpoints[0] + str(AWX_INVENTORY_IDX[profile]) + endpoints[1]

    headers = {
        'Authorization': 'Bearer ' + awx_info.token,
        'content-type': 'application/json'
    }

    idx = search_project_idx(profile=profile, awx_project=project)
    datas = {
        "name": app_name,
        "overwrite_vars": True,
        "source": "scm",
        "overwrite": True,
        "overwrite_var": True,
        "host_filter": AWX_HOST_FILTER[profile],
        "source_project": idx,
        "source_path": "inventories/" + app_name + "/hosts"
    }
    r = sess.post(req_address, headers=headers, data=json.dumps(datas))
    if r.status_code != status.HTTP_201_CREATED:
        raise AWXProjectNotCreatedException

    created_idx = r.json().get('id')
    req_address = awx_info.url + endpoints[0] + str(AWX_INVENTORY_IDX[profile]) + endpoints[2]
    print(req_address)
    r = sess.post(req_address, headers=headers)
    print(r.json())
    return r

