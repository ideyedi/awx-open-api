from fastapi import HTTPException


class AWXLoginFailException(Exception):
    """
    Ansible AWX 로그인 실패할 경우 예외 처리
    """
    pass


class AWXProjectNotFoundException(Exception):
    """
    Ansible AWX 프로젝트 찾을 수 없을 시 예외 처리
    """
    pass


class AWXProjectNotCreatedException(Exception):
    """"""
    pass


class PoolNotFoundException(Exception):
    pass


class VServerNotFoundException(Exception):
    pass


class VServerNothingToChangeException(Exception):
    pass


class NodeNotFoundException(Exception):
    pass


def raise_error(code: int, msg: str):
    raise HTTPException(status_code=code, detail=msg)
