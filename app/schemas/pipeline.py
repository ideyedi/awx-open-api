from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    func,
    text,
    JSON,
    UniqueConstraint,
)

from ..database import Base
from .datetime import DateTime


class PipelineSchema(Base):
    __tablename__ = "pipeline"
    __table_args__ = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_general_ci"}

    id = Column(Integer, primary_key=True, index=True)
    env = Column(String(16), nullable=False, comment="dev|qa|stg|prod")
    key = Column(String(32), nullable=False, comment="Bitbucket key")
    slug = Column(String(64), nullable=False, comment="Bitbucket slug")
    repository = Column(String(128), nullable=False, comment="repository url")

    raw = Column(JSON, nullable=False, comment="raw data serialized json format")
    create_dt = Column(DateTime, server_default=func.now())
    update_dt = Column(
        DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )

    # constraints
    UniqueConstraint("env", "key", "slug", name="unique_env_key_slug")
