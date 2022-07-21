import json
import logging
from typing import List
from requests import Session
from requests.exceptions import HTTPError
from pydantic import ValidationError

from ..config import get_settings
from ..models.params import (
    BitBucketPullRequestParams,
    BitbucketPullRequestPayload,
    BitBucketWebhookParams,
    BitbucketWebhookItem,
)


class Bitbucket:
    url: str = "https://bitbucket.wemakeprice.com"
    token: str = ""
    session: Session

    def __init__(self):
        settings = get_settings()
        self.token = settings.bitbucket_token
        self.session = Session()

    def set_token(self, token: str):
        self.token = token


class PullRequest(Bitbucket):
    def create(self, params: BitBucketPullRequestParams) -> BitbucketPullRequestPayload:
        """
        Bitbucket 에 PullRequest 를 생성합니다.
        """
        payload: BitbucketPullRequestPayload = None
        try:
            r = self.session.post(
                # $ http -v $JIRA_URL/rest/api/1.0/projects/INFCM/repos/web-api/pull-requests Authorization:"Bearer $JIRA_TOKEN" < pr.json
                f"{self.url}/rest/api/1.0/projects/{params.key}/repos/{params.slug}/pull-requests",
                headers={
                    "Authorization": f"Bearer {self.token}",
                },
                json=self.__build_pr_content(params),
            )
            r.raise_for_status()
            data = json.loads(r.text)
            payload = BitbucketPullRequestPayload(**data)
        except HTTPError as error:
            logging.info(f"Failed to create a new PR: {error}")
            logging.debug(error.response.text)
            return None
        except ValidationError as error:
            logging.info(
                f"ValidationError got successful response, but failed to parse pullrequest payload"
            )
            logging.debug(error.json())
            return None
        except Exception as error:
            logging.info(f"Failed to create a new PR: {error}")
            return None

        logging.info(
            f"PR {params.key}/{params.slug}/{params.title} created successfully"
        )
        return payload

    def delete(self, key: str, slug: str, id: int) -> bool:
        """
        PR 을 삭제합니다.

        https://docs.atlassian.com/bitbucket-server/rest/5.1.0/bitbucket-rest.html?utm_source=%2Fstatic%2Frest%2Fbitbucket-server%2Flatest%2Fbitbucket-rest.html&utm_medium=301#idm45588159968240

        Args:
            key (str): Bitbucket key
            slug (str): Bitbucket key
            id (int): pullrequest ID

        Returns:
            bool: True if successful
        """
        try:
            r = self.session.delete(
                # $ http -v DELETE $JIRA_URL/rest/api/1.0/projects/INFCM/repos/web-api/pull-requests/:id Authorization:"Bearer $JIRA_TOKEN"
                f"{self.url}/rest/api/1.0/projects/{key}/repos/{slug}/pull-requests/{id}",
                headers={
                    "Authorization": f"Bearer {self.token}",
                },
                # TODO: version check 를 어떻게 하지..?
                json={"version": 0},
            )
            r.raise_for_status()
        except HTTPError as error:
            logging.info(f"Failed to delete PR({id}): {error}")
            logging.debug(error.response.text)
            return False
        except ValidationError as error:
            logging.info(
                f"ValidationError got successful response, but failed to parse pullrequest payload"
            )
            logging.debug(error.json())
            return False
        except Exception as error:
            logging.info(f"Failed to delete PR({id}): {error}")
            return False

        logging.info(f"PR {key}/{slug}/{id} deleted successfully")
        return True

    def __build_pr_content(self, params: BitBucketPullRequestParams) -> dict:
        """
        PullRequest post body 를 템플릿을 사용해서 생성합니다.
        """
        reviewers = list(map(lambda r: {"user": {"name": r}}, params.reviewer))
        return {
            "closed": False,
            "description": params.description,
            "fromRef": {
                "id": f"refs/heads/{params.branches.source}",
                "repository": {
                    "name": None,
                    "project": {"key": params.key},
                    "slug": params.slug,
                },
            },
            "links": {"self": [None]},
            "locked": False,
            "open": True,
            "reviewers": reviewers,
            "state": "OPEN",
            "title": params.title,
            "toRef": {
                "id": f"refs/heads/{params.branches.destination}",
                "repository": {
                    "name": None,
                    "project": {"key": params.key},
                    "slug": params.slug,
                },
            },
        }


class WebHook(Bitbucket):
    def create(self, params: BitBucketWebhookParams) -> BitbucketWebhookItem:
        """
        Bitbucket 에 Webhook 을 생성합니다.
        """
        created: BitbucketWebhookItem = None
        try:
            r = self.session.post(
                # $ http -v $JIRA_URL/rest/api/1.0/projects/INFCM/repos/web-api/webhooks Authorization:"Bearer $JIRA_TOKEN" < webhook.json
                f"{self.url}/rest/api/1.0/projects/{params.key}/repos/{params.slug}/webhooks",
                headers={
                    "Authorization": f"Bearer {self.token}",
                },
                json=self.__build_webhook_content(params),
            )
            r.raise_for_status()
            data = json.loads(r.text)
            created = BitbucketWebhookItem(**data)
        except HTTPError as error:
            logging.info(f"Failed to create a new WebHook: {error}")
            logging.debug(error.response.text)
            return None
        except ValidationError as error:
            logging.info(
                f"ValidationError got successful response, but failed to parse webhook payload"
            )
            logging.debug(error.json())
            return None
        except Exception as error:
            logging.info(f"Failed to create a new WebHook: {error}")
            return None

        logging.info(
            f"WebHook {params.key}/{params.slug}/{created.id} created successfully"
        )
        return created

    def __build_webhook_content(self, params: BitBucketWebhookParams) -> dict:
        """
        webhook post body 를 템플릿을 사용해서 생성합니다.
        """
        return {
            "active": True,
            "configuration": {"secret": params.secret},
            "events": params.events,
            "name": params.name,
            "url": params.url,
        }

    def delete(self, key: str, slug: str, id: int) -> bool:
        """
        *WARN*
        Bitbucket 에 등록된 Webhook 을 삭제합니다.

        Args:
            id (int): webhook id
        """
        try:
            r = self.session.delete(
                # $ http -v DELETE $JIRA_URL/rest/api/1.0/projects/INFCM/repos/web-api/webhooks/416 Authorization:"Bearer $JIRA_TOKEN"
                f"{self.url}/rest/api/1.0/projects/{key}/repos/{slug}/webhooks/{id}",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
            )
            r.raise_for_status()
        except HTTPError as error:
            logging.info(f"Failed to delete webhook: {id}")
            logging.debug(error.response.text)
            return False
        except Exception as error:
            logging.info(f"Failed to delete webhook: {id}")
            return False

        logging.info(f"WebHook({id}) deleted successfully")
        return True

    def delete_by_name(self, key: str, slug: str, name: str) -> bool:
        """
        *WARN*
        등록된 Webhook 중에 `name` 이 일치하는 것을 삭제합니다.

        Args:
            name (str): webhook name
        """
        id = 0
        hooks = self.list(key=key, slug=slug)
        for hook in hooks:
            if hook.name == name:
                id = hook.id
                break

        if not id:
            logging.info(f"Not found webhook name: {key}/{slug}/{name}")
            return False

        return self.delete(key=key, slug=slug, id=id)

    def list(self, key: str, slug: str) -> List[BitbucketWebhookItem]:
        """
        Bitbucket 의 {key}/{slug} 저장소의 Webhook 목록
        """
        webhooks = list()
        try:
            r = self.session.get(
                # $ http -v $BITBUCKET_URL/rest/api/1.0/projects/INFCM/repos/web-api/webhooks Authorization:"Bearer $BITBUCKET_TOKEN"
                f"{self.url}/rest/api/1.0/projects/{key}/repos/{slug}/webhooks",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/json",
                },
            )
            r.raise_for_status()
            data = json.loads(r.text)
            values = data["values"]
            for value in values:
                webhooks.append(BitbucketWebhookItem(**value))
        except HTTPError as error:
            logging.info(f"HTTPError Failed to get webhook list")
            logging.debug(error.response.text)
        except ValidationError as error:
            logging.info(
                f"ValidationError got successful response, but failed to parse webhooks"
            )
            logging.debug(error.json())
        except Exception as error:
            logging.info(f"Failed to get webhook list")

        return webhooks
