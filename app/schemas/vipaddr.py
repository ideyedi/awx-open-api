from sqlalchemy import Boolean, Column, Integer, String, func, text, DateTime
from enum import Enum

from ..database import Base
from .datetime import DateTime


class UseYN(Enum):
    Y = "Y"
    N = "N"


class VIPAddrSchema(Base):
    __tablename__ = "vipaddr_tb"
    __table_args__ = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_general_ci"}

    id = Column(Integer, primary_key=True, index=True)
    vip_addr = Column(String(20), unique=True, index=True, nullable=False)
    domain_name = Column(String(100))
    use_yn = Column(String(10), default=UseYN.N, nullable=False)
    create_dt = Column(DateTime, server_default=func.now())
    update_dt = Column(
        DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )
