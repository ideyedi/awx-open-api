from fastapi import HTTPException


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
