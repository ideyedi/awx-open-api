from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..dao import vipaddr as VIPAddrDao
from ..schemas.vipaddr import VIPAddrSchema
from ..models.vipaddr import VIPAddrParams, VIPAddrUpdateParams
from ..errors import raise_error

router = APIRouter(prefix="/vipaddr", tags=["VIPAddr"])


@router.get("/", deprecated=True)
def get(addr: str, db: Session = Depends(get_db)):
    return find_by_addr(addr=addr, db=db)


@router.get("/{addr}")
def find_by_addr(addr: str, db: Session = Depends(get_db)):
    row = VIPAddrDao.find_by_addr(db=db, addr=addr)
    if not row:
        return raise_error(code=404, msg=f"Not found VIPAddr: {addr}")

    return row


@router.post("/")
def create(params: VIPAddrParams, db: Session = Depends(get_db)):
    found = VIPAddrDao.find_by_addr(db=db, addr=params.vip_addr)
    if found:
        raise_error(code=400, msg=f"vipaddr already exists: {params.vip_addr}")

    return VIPAddrDao.create(db=db, params=params)


@router.put("/{addr}")
def update(addr: str, params: VIPAddrUpdateParams, db: Session = Depends(get_db)):
    row = find_by_addr(addr=addr, db=db)
    update_params = VIPAddrParams(
        vip_addr=addr, domain_name=params.domain_name, use_yn=params.use_yn
    )
    VIPAddrDao.update(db=db, row=row, params=update_params)
    return row
