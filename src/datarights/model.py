from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, UniqueConstraint
from .db import Base, uid
from datetime import datetime

class RightsRequest(Base):
    __tablename__='rights_requests'
    __table_args__=(UniqueConstraint('tenant_id','external_ref',name='tenant_external_reference'),)
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    tenant_id: Mapped[str]=mapped_column(String(100),index=True)
    external_ref: Mapped[str]=mapped_column(String(80))
    subject_sha256: Mapped[str]=mapped_column(String(64))
    right: Mapped[str]=mapped_column(String(30))
    deadline_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
    status: Mapped[str]=mapped_column(String(24),default='received')
