from fastapi import APIRouter
from ..services.awx import (AnsibleCrawler,
                            )

router = APIRouter(prefix="/awx", tags=["awx"])
