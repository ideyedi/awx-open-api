from pydantic import BaseModel
from typing import Optional
from typing_extensions import Literal

from ..schemas.vipaddr import UseYN


class VIPAddrParams(BaseModel):
    vip_addr: str
    domain_name: Optional[str]
    use_yn: Optional[UseYN] = UseYN.N


class VIPAddrUpdateParams(BaseModel):
    domain_name: Optional[str] = None
    use_yn: Optional[UseYN] = UseYN.N
