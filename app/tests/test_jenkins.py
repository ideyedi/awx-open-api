from app.services.jenkins import JenkinsAgent, JenkinsJobParams

agent = JenkinsAgent()


def test_transaction():
    """
    - Folder 를 만들고
    - Job 을 만들고
    - Job 을 삭제
    - Folder 를 삭제
    """
    folder_name = "neverexists"

    # exists
    try:
        exist = agent.exists(project=folder_name)
        assert exist == False
    except Exception as err:
        exit(-1)

    # create folder
    folder_created = agent.create_folder(name=folder_name)
    assert folder_created == True

    # create job
    job_params = JenkinsJobParams(
        name="spring-hello-world",
        project=folder_name,
        repo="ssh://git@bitbucket.wemakeprice.com:7999/infcm/spring-hello-world.git",
        branch="develop",
        script="Jenkinsfile",
        targets=["a-wmp-dev"],
        argocdServer="dev-argocd.wemakeprice.kr",
    )

    job_created = agent.create(params=job_params)
    assert job_created == True

    # cleanup
    # delete job
    job_removed = agent.remove(project=job_params.project, name=job_params.name)
    assert job_removed == True

    # delete folder
    folder_deleted = agent.delete_folder(name=folder_name)
    assert folder_deleted == True


def test_job_url():
    url = agent.job_url(project="foo", name="bar")
    # follows .env.example JENKINS_HOST
    assert (
        url
        == "https://dev-jenkins.wemakeprice.kr/generic-webhook-trigger/invoke?token=foo-bar"
    )


def test_trigger():
    """
    특정 job 의 build 를 triggering
    """
    # TODO: 어케 테스트해야 하지..하나 맨들어두고 매번 빌드 시키면 되려남..
    pass


def test_exists():
    """
    exists test
    """
    # 이거 두개는 항상 있다.
    agent.exists(project="infracm") == True
    agent.exists(project="infracm", name="dev-api-infracm.wemakeprice.kr") == True

    # 없어야 됨
    agent.exists(project="foobar") == False
    agent.exists(project="foobar", name="baz") == False


# TODO: Test 용 job 을 만들어두는 것이 좋겠다.
# test 는 성공했지만 매번 테스트 돌릴때마다 build 되는 것이 부담이다.
# 해서 comment
# def test_perform_build():
#     location = agent.perform_build(
#         project="infracm", name="dev-api-infracm.wemakeprice.kr"
#     )
#     assert location != ""

# def test_perform_build_with_param():
#     build_params = {"targetClusterList": '"a-wmp-dev"'}
#     location = agent.perform_build(
#         project="infracm", name="ws-tour-api-test", build_params=build_params
#     )
#     assert location != ""
