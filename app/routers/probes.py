from fastapi import APIRouter

router = APIRouter(prefix="/probes", tags=["Probes"])


@router.get("/liveness")
def liveness():
    return "OK"
