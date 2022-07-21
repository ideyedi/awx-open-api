import json
import logging

import requests
from requests.exceptions import HTTPError
from pydantic import ValidationError

from ..config import get_settings
from ..models.params import HarborProjectReq, HarborProjectMember


class Harbor:
    url: str = "https://wregistry.wemakeprice.com/api/v2.0"

    def __init__(self):
        settings = get_settings()
        self.username = settings.harbor_username
        self.password = settings.harbor_password

        # harbor 에서는 session 을 사용하면 안됨
        # cookie 없이 요청해야 함; Invalid CSRF token error 가 발생.
        # https://github.com/goharbor/harbor/issues/13570#issuecomment-731952904
        # session = Session()
        # session.auth = (settings.harbor_username, settings.harbor_password)
        # self.session = session

    def exists_project(self, name: str) -> int:
        """
        Check if the project already exists

        Args:
            name (str): project name

        Returns:
            bool
        """
        # HEAD https://wregistry.wemakeprice.com/api/v2.0/projects?project_name=justfortest
        # 여기서는 존재여부만 response status_code 로 알려주고 project_id 를 얻어오려면 GET /projects 를 사용해야 함
        try:
            r = requests.head(
                f"{self.url}/projects?project_name={name}",
                auth=(self.username, self.password),
            )
            r.raise_for_status()
        except (HTTPError, Exception) as error:
            logging.info(f"Failed check if the project exists: {error}")
            return 0

        items = self.search_project(q=name)
        if not len(items):
            logging.info(f"project exists({name}), but couldn't get details.")
            return 0

        return items[0]["project_id"]

    # TODO: 응답 값을 model 로 정의 해야 한다.
    # 지금은 필요가 없어서 안함
    def search_project(self, q: str) -> list:
        """
        `name` 과 matching 되는 project 목록

        Args:
            q (str): query

        Returns:
            dict: decoded json response
        """
        # GET https://wregistry.wemakeprice.com/api/v2.0/projects?name=justfortest
        #
        # [
        #   {
        #     "project_id": 67,
        #     "owner_id": 38,
        #     ...

        try:
            r = requests.get(
                f"{self.url}/projects?project_name={q}",
                auth=(self.username, self.password),
            )
            r.raise_for_status()
            return r.json()  # 응답이 list 임
        except (HTTPError, Exception) as error:
            logging.info(f"Failed to search projects({q}): {error}")
            return list()

    def create_project(self, params: HarborProjectReq) -> int:
        """
        create harbor(wregistry) project

        Args:
            params (HarborProjectReq)

        Returns:
            int: project ID
        """
        # curl -X POST "https://wregistry.wemakeprice.com/api/v2.0/projects"
        # -H  "accept: application/json" -H  "Content-Type: application/json" -H  "X-Harbor-CSRF-Token: /3UUwCNn7HQE9V8ltstrwVk87DIVWmRNwhXuKig7iFrLZBufobXfQ9nJtqj38K4S1b4ZHcxDY6bP+55CbCyBpg==" -d "{  \"project_name\": \"justfortest\",  \"storage_limit\": 1000000}"

        # POST https://wregistry.wemakeprice.com/api/v2.0/projects
        #      https://wregistry.wemakeprice.com/api/v2.0/projects
        # {
        #     "count_limit": 0,
        #     "project_name": "justfortest",
        #     "storage_limit": 1
        # }

        # 201
        # connection: keep-alive
        # content-length: 0
        # location: /api/v2.0/projects/67
        # ...
        try:
            r = requests.post(
                f"{self.url}/projects/",
                auth=(self.username, self.password),
                json=params.dict(),
            )
            r.raise_for_status()
            location = r.headers.get("location")
            return int(location.split("/")[-1])
        except (HTTPError, Exception) as error:
            logging.info(f"Failed to create project: {error}")
            return 0

    def delete_project(self, id: int) -> bool:
        """
        delete project by id

        Args:
            id (int): project ID

        Returns:
            bool
        """
        # DELETE https://wregistry.wemakeprice.com/api/v2.0/projects/67
        try:
            r = requests.delete(
                f"{self.url}/projects/{id}/", auth=(self.username, self.password)
            )
            r.raise_for_status()
            return True
        except (HTTPError, Exception) as error:
            logging.info(f"Failed to delete project({id}): {error}")
            return False

    def create_project_member(self, id: int, member: HarborProjectMember) -> int:
        """
        create project member relationship

        Args:
            id (int): project ID
            member (HarborProjectMember)

        Returns:
            int: member ID
        """
        # POST https://wregistry.wemakeprice.com/api/v2.0/projects/67/members
        # {
        #     "role_id": 1,
        #     "member_user": {
        #         "username": "system"
        #     }
        # }

        # 201
        # connection: keep-alive
        # content-length: 0
        # location: /api/v2.0/projects/67/members/97
        # ...
        try:
            r = requests.post(
                f"{self.url}/projects/{id}/members/",
                auth=(self.username, self.password),
                json=member.dict(),
            )
            r.raise_for_status()
            location = r.headers.get("location")
            return int(location.split("/")[-1])
        except (HTTPError, Exception) as error:
            logging.info(f"Failed to create project: {error}")
            return 0

    def remove_project_member(self, id: int, mid: int) -> bool:
        """
        remove project member

        Args:
            id (int): project ID
            mid (int): member ID

        Returns:
            bool
        """
        # DELETE https://wregistry.wemakeprice.com/api/v2.0/projects/67/members/97
        try:
            r = requests.delete(
                f"{self.url}/projects/{id}/members/{mid}/",
                auth=(self.username, self.password),
            )
            r.raise_for_status()
            return True
        except (HTTPError, Exception) as error:
            logging.info(f"Failed to remove member({mid}) from project({id}): {error}")
            return False
