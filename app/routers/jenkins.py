from fastapi import APIRouter, HTTPException
from fastapi.responses import (PlainTextResponse,
                               Response,
                               ORJSONResponse,
                               )

from ..models.params import JenkinsJobParams
from ..services.jenkins import (JenkinsAgent,
                                JenkinsInfo,
                                )
from ..errors import raise_error

import requests
import logging

router = APIRouter(prefix="/jenkins", tags=["Jenkins"])
agent = JenkinsAgent()


@router.post('/account', response_class=PlainTextResponse)
def create_user(profile: str, account_id: str, account_name: str, account_email: str):
    profile_info = JenkinsInfo(profile)
    domain = profile_info.url
    api_url = domain + "/job/MAINTENANCE/job/wd_user/buildWithParameters"
    account_data = {
        'account_id': account_id,
        'account_name': account_name,
        'account_email': account_email
    }
    crumb_key = profile_info.check_csrf_crumb()
    headers = {crumb_key['crumbRequestField']: crumb_key['crumb']}

    ret = requests.post(api_url,
                        auth=(profile_info.api_id, profile_info.api_token),
                        data=account_data,
                        timeout=5,
                        headers=headers)
    print(f'{ret}')

    return str(ret.status_code)


@router.get('/account', response_class=PlainTextResponse)
def show_user(profile: str):
    return "OK"


@router.get('/test', response_class=PlainTextResponse)
def test(profile: str):
    profile_info = JenkinsInfo(profile)
    print(f' ENV : {profile_info.env}')

    ret = profile_info.check_csrf_crumb()
    print(ret['crumb'])

    return "OK"


@router.get('/job')
def check_jenkins_job(profile: str, job_url: str):

    return 0


@router.delete('/job')
def delete_jeknins_job(profile, job_url: str):

    return 0


'''
@router.post("/jobs", response_class=PlainTextResponse)
def create_job(params: JenkinsJobParams):
    job_url = agent.create(params)
    if not job_url:
        raise HTTPException(status_code=500, detail="Failed to create a jenkins job")

    return job_url


@router.delete("/jobs/{project}/{name}")
def remove_job(self, project: str, name: str):
    removed = agent.remove(project=project, name=name)
    if not removed:
        raise_error(500, f"Failed to remove jenkins job: {project}/{name}")

    return {"removed": "OK"}
'''