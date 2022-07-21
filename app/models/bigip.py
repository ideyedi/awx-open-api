from typing import Optional
from pydantic import BaseModel


class NodeModel(BaseModel):
    name: str
    partition: str = "Common"
    address: str
    description: Optional[str] = None


class MemberModel(BaseModel):
    name: str


class PoolModel(BaseModel):
    name: str
    partition: str = "Common"


class VirtualServerModel(BaseModel):
    name: str
    partition: str = "Common"
    pool: str
    sourceAddressTranslation = {"type": "snat"}
    # snatpool: str = 'snat_dev_10.107.31.0_24'
    snatpool: str
    source: str = "0.0.0.0/0"
    mask: str = "255.255.255.255"
    profiles = [{"name": "fasthttp"}]
    destination: str


class VirtualServiceModel(BaseModel):
    hostname: str
    vip: Optional[str] = None


class VirtualServerUpdateParams(BaseModel):
    vip: str
    partition: Optional[str] = "Common"


class IpPoolModel(BaseModel):
    ip_cidr: str
    ip_cidr_exclude: Optional[list] = None

    class Config:
        schema_extra = {
            "example": {
                "ip_cidr": "192.168.30.0/24",
                "ip_cidr_exclude": {
                    "192.168.30.0/28",
                    "192.168.30.16/32",
                    "192.168.30.192/26",
                },
            }
        }


class IpPoolModelDel(BaseModel):
    ip_cidr: str

    class Config:
        schema_extra = {"example": {"ip_cidr": "192.168.30.0/24"}}
