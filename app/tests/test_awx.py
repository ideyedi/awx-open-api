# python
import pytest
"""
TC
- profile 별 awx 접근 확인
- 
"""


@pytest.fixture
def awx_urls():
    from app.config import AWX_URLS
    return list(AWX_URLS.values())


@pytest.fixture
def get_chrome_path():
    import os
    return os.system("which google-chrome")


def test_get_awx(awx_urls):
    import requests
    from fastapi import status
    for url in awx_urls:
        ret = requests.get(url)
        assert ret.status_code == status.HTTP_200_OK

