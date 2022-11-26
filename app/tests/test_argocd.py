import logging
from app.services.argocd import Argocd
from app.models.params import ArgocdAppParams, ArgocdProjectParams

argocd = Argocd()


def test_argocd_project_exists():
    """
    project 가 존재하는지 여부 체크
    """
    try:
        # infracm project 는 항상 있음
        assert argocd.exists_project(name="infracm") == True
        # infracm-web-api-a-wmp-dev app 은 항상 있음
        assert argocd.exists_app(name="infracm-web-api-a-wmp-dev") == True

        # foo-bar project 는 없음
        assert argocd.exists_project(name="foo-bar") == False
        # foo-bar-baz app 또한 없음
        assert argocd.exists_app(name="foo-bar-baz") == False
    except Exception as error:
        logging.error(error)
        exit(-1)
