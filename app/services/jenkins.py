import logging
from requests import Session
from requests.exceptions import HTTPError
from fastapi.templating import Jinja2Templates
from ..config import get_settings
from ..models.params import JenkinsJobParams

templates = Jinja2Templates(directory="app/templates")


class JenkinsAgent:
    def create(self, params: JenkinsJobParams) -> bool:
        """
        Job 을 생성
        """
        s = Session()
        crumbs = ""
        try:
            crumbs = self.__issue_crumbs(session=s)
        except (HTTPError, Exception) as error:
            logging.error(f"Failed to issue a crumbs: {error}")
            return False

        settings = get_settings()
        host, username, token = (
            settings.jenkins_host,
            settings.jenkins_username,
            settings.jenkins_token,
        )

        template = templates.get_template("jenkins/config.xml.j2")
        config = template.render(params)
        try:
            r = s.post(
                f"{host}/job/{params.project}/createItem?name={params.name}",
                auth=(username, token),
                headers={"Content-Type": "text/xml", "Jenkins-Crumb": crumbs},
                data=config,
            )
            r.raise_for_status()
        except (HTTPError, Exception) as error:
            logging.error(f"Failed to create a new job: {error}")
            return False

        logging.info(f"{host}/job/{params.project}/job/{params.name}/")
        return True

    def trigger(self, project: str, name: str) -> bool:
        """
        Trigger job
        """
        # POST https://dev-jenkins.wemakeprice.kr/job/:project/job/:name/buildWithParameters
        # the successful queueing will result in 201 status code with Location HTTP header pointing the URL of the item in the queue.
        # TODO: impl
        pass

    def remove(self, project: str, name: str) -> bool:
        """
        Job item 삭제
        """
        # DELETE https://dev-jenkins.wemakeprice.kr/job/:project/job/:name/
        s = Session()
        crumbs = ""
        try:
            crumbs = self.__issue_crumbs(session=s)
        except (HTTPError, Exception) as error:
            logging.error(f"Failed to issue a crumbs: {error}")
            return False

        settings = get_settings()
        host, username, token = (
            settings.jenkins_host,
            settings.jenkins_username,
            settings.jenkins_token,
        )

        try:
            r = s.delete(
                f"{host}/job/{project}/job/{name}",
                auth=(username, token),
                headers={"Jenkins-Crumb": crumbs},
            )
            r.raise_for_status()
        except (HTTPError, Exception) as error:
            logging.error(f"Failed to remove job({project}/{name}): {error}")
            return False

        logging.info(f"{host}/job/{project}/job/{name}/ removed successfully")
        return True

    def exists(self, project: str, name: str = "") -> bool:
        """
        Folder or Job 이 존재하는지 여부
        """
        # GET https://dev-jenkins.wemakeprice.kr/job/:project/
        # GET https://dev-jenkins.wemakeprice.kr/job/:project/job/:name/
        s = Session()
        crumbs = ""
        try:
            crumbs = self.__issue_crumbs(session=s)
        except (HTTPError, Exception) as error:
            logging.error(f"Failed to issue a crumbs: {error}")
            return False

        settings = get_settings()
        host, username, token = (
            settings.jenkins_host,
            settings.jenkins_username,
            settings.jenkins_token,
        )

        try:
            url = (
                f"{host}/job/{project}/job/{name}" if name else f"{host}/job/{project}"
            )
            r = s.get(
                url,
                auth=(username, token),
                headers={"Jenkins-Crumb": crumbs},
            )
            r.raise_for_status()
        except HTTPError as error:
            if error.response.status_code == 404:
                return False
            logging.error(f"Failed to check {name} exists: {error}")
            raise error
        except Exception as error:
            logging.error(f"Failed to check {name} exists: {error}")
            raise error

        return True

    def create_folder(self, name: str) -> bool:
        """
        Folder 를 생성
        """
        # curl -XPOST 'http://jenkins/createItem?name=FolderName&mode=com.cloudbees.hudson.plugins.folder.Folder&from=&json={"name":"FolderName","mode":"com.cloudbees.hudson.plugins.folder.Folder","from":"","Submit":"OK"}&Submit=OK' --user user.name:YourAPIToken -H "Content-Type:application/x-www-form-urlencoded"
        s = Session()
        crumbs = ""
        try:
            crumbs = self.__issue_crumbs(session=s)
        except (HTTPError, Exception) as error:
            logging.error(f"Failed to issue a crumbs: {error}")
            return False

        settings = get_settings()
        host, username, token = (
            settings.jenkins_host,
            settings.jenkins_username,
            settings.jenkins_token,
        )

        try:
            r = s.post(
                f"{host}/createItem",
                auth=(username, token),
                headers={"Jenkins-Crumb": crumbs},
                data={
                    "name": name,
                    "mode": "com.cloudbees.hudson.plugins.folder.Folder",
                    "from": "",
                    "Submit": "OK",
                },
            )
            r.raise_for_status()
        except (HTTPError, Exception) as error:
            logging.error(f"Failed to create a new folder: {error}")
            return False

        logging.info(f"{host}/job/{name}/ created successfully")
        return True

    def delete_folder(self, name: str) -> bool:
        """
        Folder 를 삭제
        """
        # DELETE https://dev-jenkins.wemakeprice.kr/job/:name/
        s = Session()
        crumbs = ""
        try:
            crumbs = self.__issue_crumbs(session=s)
        except (HTTPError, Exception) as error:
            logging.error(f"Failed to issue a crumbs: {error}")
            return False

        settings = get_settings()
        host, username, token = (
            settings.jenkins_host,
            settings.jenkins_username,
            settings.jenkins_token,
        )

        try:
            r = s.delete(
                f"{host}/job/{name}/",
                auth=(username, token),
                headers={"Jenkins-Crumb": crumbs},
            )
            r.raise_for_status()
        except (HTTPError, Exception) as error:
            logging.error(f"Failed to remove folder({name}): {error}")
            return False

        logging.info(f"{host}/job/{name}/ deleted successfully")
        return True

    def __issue_crumbs(self, session: Session):
        settings = get_settings()
        host, username, token = (
            settings.jenkins_host,
            settings.jenkins_username,
            settings.jenkins_token,
        )
        r = session.get(f"{host}/crumbIssuer/api/json/", auth=(username, token))
        r.raise_for_status()

        return r.json()["crumb"]

    def job_url(self, project: str, name: str) -> str:
        """
        배포환경에 맞는 jenkins job url 을 return
        """
        # https://dev-jenkins.wemakeprice.kr/generic-webhook-trigger/invoke?token=spring-hello-world
        settings = get_settings()
        host = settings.jenkins_host
        return f"{host}/generic-webhook-trigger/invoke?token={project}-{name}"

    def perform_build(
        self, project: str, name: str, build_params: dict = dict()
    ) -> str:
        """
        build 를 triggering

        post to this URL and provide the parameters as form data.
        https://dev-jenkins.wemakeprice.kr/job/infracm/job/dev-api-infracm.wemakeprice.kr/build

        Args:
            project (str)
            name (str)
            build_parameters (dict): Build With Parameters; 없으면 구성된 default 값이 사용
                                     e.g.
                                     targetClusterList: "a-wmp-dev","a-azure-dev"
                                     targetClusterList: "a-wmp-dev"

        Returns:
            str: build location url
        """
        s = Session()
        crumbs = ""
        try:
            crumbs = self.__issue_crumbs(session=s)
        except (HTTPError, Exception) as error:
            logging.error(f"Failed to issue a crumbs: {error}")
            return ""

        settings = get_settings()
        host, username, token = (
            settings.jenkins_host,
            settings.jenkins_username,
            settings.jenkins_token,
        )

        try:
            r = None
            if len(build_params):
                r = s.post(
                    # buildWithParameters
                    f"{host}/job/{project}/job/{name}/buildWithParameters",
                    auth=(username, token),
                    headers={"Jenkins-Crumb": crumbs},
                    data=build_params,
                )
            else:
                r = s.post(
                    f"{host}/job/{project}/job/{name}/build",
                    auth=(username, token),
                    headers={"Jenkins-Crumb": crumbs},
                )

            r.raise_for_status()
            location = r.headers.get("location")
            logging.info(f"perform build {location} successfully")
            return r.headers.get("location")
        except (HTTPError, Exception) as error:
            logging.error(f"Failed to perform build: {error}")
            return ""
