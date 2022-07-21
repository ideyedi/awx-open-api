import logging
import requests
import json
import time
from base64 import b64decode
from requests import Session
from fastapi.templating import Jinja2Templates

from ..config import get_settings
from ..models.params import ArgocdAppParams, ArgocdProjectParams


class Argocd:
    def __init__(self):
        self.app_template = "app/templates/argocd/app.json"
        self.project_template = "app/templates/argocd/project.json"

        settings = get_settings()

        self.host, self.helm_repo, self.token = (
            settings.argocd_host,
            settings.helm_repo,
            settings.argocd_token,
        )

        self.destinations = {
            "a-wmp-dev": f"{settings.rancher_host}/c-xdbxv",
            "a-wmp-stg": f"{settings.rancher_host}/c-2j2r5",
            "b-wmp-dev": f"{settings.rancher_host}/c-ct2ql",
            "a-azure-dev": f"{settings.rancher_host}/c-v7kb9",
            "b-azure-dev": f"{settings.rancher_host}/c-8hcxx",
        }

        self.refresh_token()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def refresh_token(self):
        settings = get_settings()

        self.host, self.token = (
            settings.argocd_host,
            settings.argocd_token,
        )

        has_valid_token = True
        if not self.token:
            has_valid_token = False
        else:
            partials = self.token.split(".")
            payload = partials[1]
            payload += "=" * ((4 - len(payload) % 4) % 4)
            data = json.loads(b64decode(payload))
            seconds = int(time.time())
            if "exp" in data and data["exp"] < seconds:
                # token has expired
                has_valid_token = False

        if not has_valid_token:
            # https://argo-cd.readthedocs.io/en/stable/developer-guide/api-docs/
            username = settings.argocd_username
            password = settings.argocd_password
            try:
                res = requests.post(
                    f"https://{self.host}/api/v1/session",
                    json={"username": username, "password": password},
                )
                res.raise_for_status()
                self.token = res.json()["token"]
                logging.info("argocd token refreshed successfully")
            except (requests.exceptions.HTTPError, Exception) as error:
                print(f"Failed to create a argocd token: {error}")

    def create_app(self, params: ArgocdAppParams):

        with open(self.app_template) as f:
            data = json.load(f)

        path = f"project/{params.project}/{params.name}"
        if params.path:
            path = params.path

        for target in params.targets:
            data["metadata"]["name"] = f"{params.project}-{params.name}-{target}"
            data["spec"]["source"]["repoURL"] = self.helm_repo
            data["spec"]["source"]["path"] = path
            data["spec"]["source"]["targetRevision"] = params.branch
            data["spec"]["destination"]["server"] = self.destinations[target]
            data["spec"]["destination"]["namespace"] = params.project
            data["spec"]["project"] = params.project

            if len(params.values):
                data["spec"]["source"]["helm"]["valueFiles"] = params.values

            try:
                self.refresh_token()
                res = requests.post(
                    f"https://{self.host}/api/v1/applications",
                    headers=self.headers,
                    json=data,
                )
                res.raise_for_status()
            except (requests.exceptions.HTTPError, Exception) as error:
                print(f"Failed to create a argocd application: {error}")
                return

        return res.text

    def delete_app(self, name: str):
        try:
            self.refresh_token()
            res = requests.delete(
                f"https://{self.host}/api/v1/applications/{name}",
                headers=self.headers,
            )
            res.raise_for_status()
        except (requests.exceptions.HTTPError, Exception) as error:
            print(f"Failed to Delete a argocd application: {error}")
            return

        return res.status_code

    def exists_app(self, name: str) -> bool:
        """
        app 이 존재하는지 여부
        """
        name = name.lower()
        try:
            self.refresh_token()
            res = requests.get(
                f"https://{self.host}/api/v1/applications/{name}",
                headers=self.headers,
            )
            res.raise_for_status()
        except requests.exceptions.HTTPError as error:
            if error.response.status_code == 404:
                return False
            logging.error(f"Failed to check {name} app exists")
            raise error
        except Exception as error:
            logging.error(f"Failed to check {name} app exists")
            raise error

        return True

    def create_project(self, params: ArgocdProjectParams):
        with open(self.project_template) as f:
            data = json.load(f)

        data["project"]["metadata"]["name"] = params.name
        data["project"]["spec"]["description"] = params.description
        for key, destination in self.destinations.items():
            data["project"]["spec"]["destinations"].append(
                {"namespace": f"{params.name}", "server": f"{destination}"}
            )
        data["project"]["spec"]["sourceRepos"].append(self.helm_repo)

        try:
            self.refresh_token()
            res = requests.post(
                f"https://{self.host}/api/v1/projects",
                headers=self.headers,
                data=json.dumps(data),
            )
            res.raise_for_status()
        except (requests.exceptions.HTTPError, Exception) as error:
            print(f"Failed to create a project: {error}")
            return

        return res.text

    def delete_project(self, name: str):
        try:
            self.refresh_token()
            res = requests.delete(
                f"https://{self.host}/api/v1/projects/{name}",
                headers=self.headers,
            )
            res.raise_for_status()
        except (requests.exceptions.HTTPError, Exception) as error:
            print(f"Failed to Delete a project: {error}")
            return

        return res.status_code

    def exists_project(self, name: str) -> bool:
        """
        project 가 존재하는지 여부
        """
        try:
            self.refresh_token()
            res = requests.get(
                f"https://{self.host}/api/v1/projects/{name}",
                headers=self.headers,
            )
            res.raise_for_status()
        except requests.exceptions.HTTPError as error:
            if error.response.status_code == 404:
                return False
            logging.error(f"Failed to check {name} project exists")
            raise error
        except Exception as error:
            logging.error(f"Failed to check {name} project exists")
            raise error

        return True
