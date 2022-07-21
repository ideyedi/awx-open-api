import re
import logging
from fastapi.testclient import TestClient

from ..main import app
from ..services.bitbucket import WebHook
from ..services.jenkins import JenkinsAgent
from ..services.argocd import Argocd
from ..models.params import (
    DISPOSABLE_WEBHOOK_PREFIX,
    BitbucketMergeEventPayload,
    BitbucketMergeEventPayloadRef,
    BitbucketMergeEventPayloadRepository,
    BitbucketMergeEventPayloadPullRequest,
    BitbucketMergeEventPayloadProject,
    BitbucketMergeEventPayloadActor,
)

webhook = WebHook()
agent = JenkinsAgent()
argocd = Argocd()
client = TestClient(app)

# POST /webhooks/bitbucket/
# TODO: 구현에 있어서 대소문자와 관련한 일관된 rule 을 적용해야 함
def test_post_webhooks_bitbucket():
    payload = BitbucketMergeEventPayload(
        eventKey="pr:merged",
        date="2021-02-15T09:32:00+0900",
        actor=BitbucketMergeEventPayloadActor(
            id=1,
            name="hshong",
            emailAddress="hshong@wemakeprice.com",
            displayName="Hyungsuk Hong",
            active=True,
            slug="user",
            type="NORMAL",
        ),
        ## fromRef.displayId -> toRef.displayId
        ## e.g. feature-something -> master
        pullRequest=BitbucketMergeEventPayloadPullRequest(
            id=1,
            version=0,
            title="",
            state="MERGED",
            open=True,
            closed=False,
            createdDate=0,  # ignore
            updatedDate=0,  # ignore
            fromRef=BitbucketMergeEventPayloadRef(
                id="refs/heads/dockerize-by-infracm-2021-02-11T125902/file-12345",
                displayId="dockerize-by-infracm-2021-02-11T125902/file-12345",
                latestCommit="abcde",  # ignore
                repository=BitbucketMergeEventPayloadRepository(
                    id=1,
                    slug="spring-hello-world",
                    name="pr name",
                    scmId="git",
                    state="AVAILABLE",
                    statusMessage="Available",
                    forkable=True,
                    project=BitbucketMergeEventPayloadProject(
                        key="INFCM",
                        id=1,
                        name="InframCM TF",
                        public=True,
                        type="NORMAL",
                    ),
                    public=False,
                ),
            ),
            toRef=BitbucketMergeEventPayloadRef(
                id="refs/heads/k8s-350-ci-pipeline-test",
                displayId="k8s-350-ci-pipeline-test",
                latestCommit="abcde",  # ignore
                repository=BitbucketMergeEventPayloadRepository(
                    id=1,
                    slug="spring-hello-world",
                    name="pr name",
                    scmId="git",
                    state="AVAILABLE",
                    statusMessage="Available",
                    forkable=True,
                    project=BitbucketMergeEventPayloadProject(
                        key="INFCM",
                        id=1,
                        name="InframCM TF",
                        public=True,
                        type="NORMAL",
                    ),
                    public=False,
                ),
            ),
            locked=False,
        ),
    )

    res = client.post("/webhooks/bitbucket", json=payload.dict())
    assert res.status_code == 200

    hooks = webhook.list(key="INFCM", slug="spring-hello-world")

    # webhook 이 제거 되었는지 (삭제 되었어야 함)
    found_pr_trigger_hook = False
    for hook in hooks:
        if re.search(rf"^{DISPOSABLE_WEBHOOK_PREFIX}", hook.name):
            found_pr_trigger_hook = True
            break
    assert found_pr_trigger_hook == False

    # jenkins job 추가되었는지
    try:
        assert agent.exists(project="infcm", name="spring-hello-world") == True
    except Exception as error:
        logging.error(error)
        exit(-1)

    # build trigger webhook 생성되었는지
    found_push_trigger_hook = False
    for hook in hooks:
        if re.search(rf"jenkins\-k8s", hook.name):
            found_push_trigger_hook = True
            break
    assert found_push_trigger_hook == True

    # argocd 에 app 생성되었는지
    try:
        assert argocd.exists_app(f"infcm-spring-hello-world-a-wmp-dev") == True
    except Exception as error:
        logging.error(error)
        exit(-1)

    # 그리고 cleanup
    # argocd 에서 제거
    # jenkins 에서 제거
    # push trigger webhook 제거
