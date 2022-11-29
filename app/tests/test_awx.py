# python
import os
import sys
import requests

from app.worker.awx import AnsibleCrawler
from app.config import AWX_URL_TUPLE
"""
1. google stable check
2. profile 별 awx 접근 확인
3. redis 연동 테스트 - PING, PONG
4. flower 연동 테스트 - 이건 뭐로 해야할까

And so on..
"""


def inc(x):
    return x + 1


def access_awx(ix: int):
    """
    해당 서버에서 각 Ansible AWX로 접근 가능 여부 테스트 코드
    """
    stat = requests.get(AWX_URL_TUPLE[ix] + "/#/login")
    return stat.status_code


def get_chrome_path():
    return os.system("which google-chrome")


def test_get_awx():
    for ix in range(4):
        assert access_awx(ix) == 200


def test_installed_chrome():
    assert "not found" in get_chrome_path()
