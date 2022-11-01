import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import (
    probes,
    generators,
    jenkins,
    pinpoint,
    awx,
)
#from .database import Base, engine
from .ver import __version__ as version
from .config import get_settings

logging.basicConfig(level=logging.INFO)
#Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="sre-crawler-api",
    description="WMP Infrastructure Automation RESTful WEB API",
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
app.include_router(probes.router)
app.include_router(generators.router)
app.include_router(jenkins.router)
app.include_router(pinpoint.router)
app.include_router(awx.router)

#app.include_router(webhooks.router)
#app.include_router(pipelines.router)
#app.include_router(vipaddr.router)
#app.include_router(argocd.router)
#if configs.bigip_enabled == "true":
#    app.include_router(bigip.router)
