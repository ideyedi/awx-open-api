import logging
from fastapi import FastAPI

from app.routers import (
    pinpoint, awx,
)

from app.ver import __version__ as version

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="sre-crawler-api",
    description="WMP Infrastructure Automation restful API",
    version=f"v{version}",
    docs_url="/",
)

'''
configs = get_settings()
origins = configs.cors_allow_origins.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
'''
app.include_router(pinpoint.router)
app.include_router(awx.router)
