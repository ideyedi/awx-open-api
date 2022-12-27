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
    Search by project index number using name
    """
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


def search_source_inventory(profile, app_name):
    """
    Search by source inventory index number using application name
    """
    endpoint = "/api/v2/inventory_sources?search=" + app_name
    awx_info = AwxInfo(profile=profile,
                       url=AWX_URLS[profile],
                       token=OAUTH2_TOKENS[profile],
                       project_idx=AWX_PROJECT_IDX[profile])
    headers = {
        'Authorization': 'Bearer ' + awx_info.token,
        'content-type': 'application/json'
    }

    with requests.session() as sess:
        response = sess.get(awx_info.url + endpoint, headers=headers)
        cnt = response.json().get('count')
        infos = response.json().get('results')

        if cnt == 0:
            print(f"Not founded sourced inventory {app_name}")
            raise AWXProjectNotFoundException

        idx = infos[0].get("id", 0)

    return idx


def create_awx_inventory_sources(app_name, profile, project):
    """
    Create inventory sources using AWX OpenAPI
    """
    endpoints: str = ["/api/v2/inventories/", "/inventory_sources/", "/update/"]
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
        "source": "scm",
        "overwrite": True,
        "overwrite_var": True,
        "host_filter": AWX_HOST_FILTER[profile],
        "source_project": idx,
        "source_path": "inventories/" + app_name + "/hosts"
    }
    r = sess.post(req_address, headers=headers, data=json.dumps(datas))
    if r.status_code != status.HTTP_201_CREATED:
        print(r.json())
        raise AWXProjectNotCreatedException

    created_idx = r.json().get('id')
    req_address = awx_info.url + "/api/v2" + endpoints[1] + str(created_idx) + endpoints[2]
    print(req_address)
    r = sess.get(req_address, headers=headers)
    print(r.json())
    r = sess.post(req_address, headers=headers)
    print(r.reason)

    return r


def change_awx_sourced_inventory_branch(profile, idx):
    """
    Sourced inventory branch parameter 변경
    """
    endpoints = "/api/v2/inventory_sources/"
    awx_info = AwxInfo(profile=profile,
                       url=AWX_URLS[profile],
                       token=OAUTH2_TOKENS[profile],
                       project_idx=AWX_PROJECT_IDX[profile])
    headers = {
        'Authorization': 'Bearer ' + awx_info.token,
        'content-type': 'application/json'
    }

    datas = {
        "source_project": awx_info.project_idx
    }

    with requests.Session() as sess:
        # Change branch value to profile default branch
        r = sess.patch(awx_info.url + endpoints + str(idx) + '/', headers=headers, data=json.dumps(datas))
        print(r.status_code)
        # Synchronizing sourced project
        address = awx_info.url + "/api/v2/inventory_sources/" + str(idx) + "/update/"
        r = sess.post(address, headers=headers)
        print(r.status_code)

    return r
