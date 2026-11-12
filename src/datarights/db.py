"""SQLAlchemy persistence. create_all is intentionally enabled only for development/testing."""
import os
from sqlalchemy import create_engine, String, DateTime, ForeignKey, Text, Integer, Boolean, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from datetime import datetime, timezone
from uuid import uuid4

class Base(DeclarativeBase):
    pass

def uid() -> str:
    return str(uuid4())

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class AuditEvent(Base):
    __tablename__ = 'audit_events'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor_id: Mapped[str] = mapped_column(String(100), nullable=False)
    kind: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

# Tables for domain entities live in model.py.

def engine_for_env():
    url = os.environ.get('H4_DATABASE_URL', 'sqlite:///./h4-demo.db')
    kwargs = {'connect_args': {'check_same_thread': False}} if url.startswith('sqlite') else {}
    return create_engine(url, pool_pre_ping=True, **kwargs)


def audit(session, auth, kind, resource_id):
    session.add(AuditEvent(tenant_id=auth['tenant_id'], actor_id=auth['actor_id'], kind=kind,
                           resource_id=str(resource_id)))
