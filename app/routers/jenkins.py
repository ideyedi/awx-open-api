from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from ..models.params import JenkinsJobParams
from ..services.jenkins import JenkinsAgent
from ..errors import raise_error

router = APIRouter(prefix="/jenkins", tags=["Jenkins"])
agent = JenkinsAgent()


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
