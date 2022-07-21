from typing import List, Optional
from sqlalchemy.orm import Session
import ipaddress
from ..schemas.vipaddr import VIPAddrSchema, UseYN
from ..models.vipaddr import VIPAddrParams

RESERVED_PRE_HOSTS = 1
RESERVED_POST_HOSTS = 0


def find_by_addr(db: Session, addr: str) -> VIPAddrSchema:
    return db.query(VIPAddrSchema).filter_by(vip_addr=addr).first()


def find_by_hostname(db: Session, hostname: str) -> VIPAddrSchema:
    return db.query(VIPAddrSchema).filter_by(domain_name=hostname).first()


def find_by_flag(db: Session, use_yn: UseYN) -> VIPAddrSchema:
    return db.query(VIPAddrSchema).filter_by(use_yn=use_yn.value).first()


def update(db: Session, row: VIPAddrSchema, params: VIPAddrParams) -> VIPAddrSchema:
    row.vip_addr = params.vip_addr
    row.domain_name = params.domain_name
    row.use_yn = params.use_yn.value
    db.commit()
    db.refresh(row)
    return row


def reset(db: Session, row: VIPAddrSchema) -> VIPAddrSchema:
    row.domain_name = None
    row.use_yn = UseYN.N.value
    db.commit()
    db.refresh(row)
    return row


def release(db: Session, row: VIPAddrSchema) -> VIPAddrSchema:
    return reset(db=db, row=row)


def create(db: Session, params: VIPAddrParams) -> VIPAddrSchema:
    row = VIPAddrSchema(
        vip_addr=params.vip_addr,
        domain_name=params.domain_name,
        use_yn=params.use_yn.value,
    )

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def add_all(db: Session, ipaddrs: List[ipaddress.IPv4Address]):
    vipaddrs = list()
    for addr in ipaddrs:
        vipaddrs.append(
            VIPAddrSchema(vip_addr=str(addr), domain_name=None, use_yn=UseYN.N.value)
        )

    db.add_all(vipaddrs)
    db.commit()


def delete_all(db: Session, ipaddrs: List[ipaddress.IPv4Address]):
    for addr in ipaddrs:
        db.query(VIPAddrSchema).filter_by(vip_addr=str(addr)).delete()

    db.commit()


# old.domain_name 을 new.domain_name 으로 할당하고,
# old 를 release
def take_and_release(db: Session, old: VIPAddrSchema, new: VIPAddrSchema):
    params = VIPAddrParams(
        vip_addr=new.vip_addr, domain_name=old.domain_name, use_yn=UseYN.Y.value
    )
    update(db=db, row=new, params=params)
    release(db=db, row=old)
