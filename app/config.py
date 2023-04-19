from pydantic import BaseSettings
from typing_extensions import Literal

REGIONS = Literal["dev", "qa", "stg", "prod"]

AWX_URLS = {
    "dev": "http://awx-dev.wemakeprice.kr",
    "qa": "http://awx-qa.wemakeprice.kr",
    "stg": "http://awx-stg.wemakeprice.kr",
    "prod": "http://awx.wemakeprice.kr",
}

# AWX 'jenkins' Token expires time '3/31/3022'..
OAUTH2_TOKENS = {
    "dev": "lXhCWAnf9cVIw67JJlex4PZL2PmMjz",
    "qa": "zI6di0MBYg7FUnpF7W7S9GGhYKoQNL",
    "stg": "3E0QQJTVxGIKf8J4B9cBrWrOfmQIoW",
    "prod": "GAIoEoNzHbhHIuqeNNmhNkpV8AB4PF",
}

AWX_PROJECT_IDX = {
    "dev": 8,
    "qa": 6,
    "stg": 8,
    "prod": 6,
}

AWX_INVENTORY_IDX = {
    "dev": 2,
    "qa": 1,
    "stg": 2,
    "prod": 1,
}

AWX_HOST_FILTER = {
    "dev": "[A-Za-z]+\d+\w+.dev.",
    "qa": "[A-Za-z]+\d+\w+.qa.",
    "stg": "[A-Za-z]+\d+\w+.stg.",
    "prod": "[A-Za-z]+\d+\w+.(?!dev|qa|stg)[a-z].",
}

"""
'--no-sandbox'
- Linux system에서 사용하기 위함

'--window-size'
- input tag에 키워드 전달 시 창 크기 정의가 없는 경우 상호 작용이 안될수 있음
"""
CHROME_OPTION = [
    "--incognito",
    "--headless",
    "--no-sandbox",
    "--window-size=1920,1080"
]

tags_metadata = [
    {
        "name": "awx",
        "description": "AWX 관련 업무 크롤링을 통한 자동화"
    }
]


class Settings(BaseSettings):
    """
    project 'SRE Crawler API'
    infra-DevOps 메일링 주소..
    OpenAPI tags는 타입 명시를 뭐로 해야하지..
    """
    app_name: str = "sre-api"
    admin_email: str = "wmporg_distribution@wemakeprice.com"
    app_description: str = "WeMakePrice SRE Automation restful API"
    app_version: str
    docs_url: str
    openapi_tags = tags_metadata
