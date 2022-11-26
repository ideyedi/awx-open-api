from app.services.bitbucket import PullRequest, WebHook
from app.models.params import (
    BitBucketPullRequestParams,
    BitBucketPullRequestBranchParams,
    BitbucketPullRequestPayload,
    BitBucketWebhookParams,
)

pullrequest = PullRequest()
webhook = WebHook()


def test_pr_transaction():
    """
    pr 을 생성/삭제합니다.
    """
    params = BitBucketPullRequestParams(
        key="INFCM",
        slug="spring-hello-world",
        branches=BitBucketPullRequestBranchParams(
            source="develop", destination="master"
        ),
        title="test pr",
        description="created by test file",
    )
    payload = pullrequest.create(params)
    assert payload != None
    assert payload.open == True
    assert (
        pullrequest.delete(key="INFCM", slug="spring-hello-world", id=payload.id)
        == True
    )


def test_webhook_transaction():
    """
    webhook 을 생성/조회/삭제합니다.
    """
    params = BitBucketWebhookParams(
        key="INFCM",
        slug="spring-hello-world",
        secret="s3cr3t",
        url="https://example.com",
        name="test-webhook",
        events=["pr:merged"],
    )
    hook = webhook.create(params)
    assert hook != None

    hooks = webhook.list(key="INFCM", slug="spring-hello-world")
    assert len(hooks) != 0

    found = False
    for h in hooks:
        if h.name == "test-webhook":
            found = True
            break
    assert found == True

    assert webhook.delete(key="INFCM", slug="spring-hello-world", id=hook.id) == True


def test_webhook_delete_by_name():
    """
    webhook 을 생성하고 이름으로 찾아서 삭제합니다.
    """
    params = BitBucketWebhookParams(
        key="INFCM",
        slug="spring-hello-world",
        secret="s3cr3t",
        url="https://example.com",
        name="test-webhook",
        events=["pr:merged"],
    )
    hook = webhook.create(params)
    assert hook != None
    assert (
        webhook.delete_by_name(
            key="INFCM", slug="spring-hello-world", name="thisisneverexists"
        )
        == False
    )
    assert (
        webhook.delete_by_name(
            key="INFCM", slug="spring-hello-world", name="test-webhook"
        )
        == True
    )
