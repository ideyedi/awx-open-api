import logging
from .harbor import Harbor
from ..models.params import (
    HarborProjectReq,
    HarborUserEntity,
    HARBOR_ROLE_MAP,
    HarborProjectMember,
)

wregistry = Harbor()


def test_exists_project():
    """
    project 가 존재하는지 여부 체크
    """
    assert wregistry.exists_project("infracm") != 0
    assert wregistry.exists_project("neverexistsproject") == 0


def test_txn_project():
    """
    project 생성 테스트
    """
    created_project_id = 0
    created_project_member_id = 0

    mb = 1000 * 1000
    gb = mb * 1000

    params = HarborProjectReq(
        project_name="justfortest",
        storage_limit=(mb * 1),
    )

    # 프로젝트 생성
    created_project_id = wregistry.create_project(params=params)
    assert created_project_id != 0

    # project 에 member 추가
    # 자신이 만든 프로젝트에는 member 로 추가할 필요가 없다; 이미 member 임
    # 오히려 Conflict 에러 남
    member = HarborProjectMember(
        role_id=HARBOR_ROLE_MAP["projectAdmin"],
        member_user=HarborUserEntity(username="john.kang"),  # RIP john.kang..
    )
    created_project_member_id = wregistry.create_project_member(
        id=created_project_id, member=member
    )
    assert created_project_member_id != 0

    # member 삭제
    assert wregistry.remove_project_member(
        id=created_project_id, mid=created_project_member_id
    )

    # project 삭제
    assert wregistry.delete_project(id=created_project_id)
