from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from ..models.params import JenkinsJobParams
from ..services.jenkins import JenkinsAgent
from ..errors import raise_error

import requests

router = APIRouter(prefix="/jenkins", tags=["Jenkins"])
agent = JenkinsAgent()


@router.post('/jobs', response_class=PlainTextResponse)
def account(profile, account_id: str, account_name: str, account_email: str):
    domain = "http://jenkins.dev.wemakeprice.com"
    url = domain + "/job/MAINTENANCE/job/wd_user/buildWithParameters"
    account_data = {
        'account_id': account_id,
        'account_name': account_name,
        'account_email': account_email
    }

    ret = requests.post(url, auth=("esji", "01eff24aa80f35ba589c3901c292064c"), data=account_data, timeout=5)
    print(f'{ret}')
    return "OK"


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