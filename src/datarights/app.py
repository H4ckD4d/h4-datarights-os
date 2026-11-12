"""Bounded MVP API. Never deploy this demo unchanged with real customer data."""
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta, date
from typing import Literal
from fastapi import FastAPI, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .db import Base, AuditEvent, audit, engine_for_env, uid
from .security import current_actor
from .model import *

@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = engine_for_env()
    app.state.engine = engine
    if os.getenv('H4_AUTO_CREATE_TABLES') == '1':
        Base.metadata.create_all(engine)
    try:
        yield
    finally:
        engine.dispose()

def session_dep(request: Request):
    with Session(request.app.state.engine) as session:
        yield session

def require_tenant(session: Session, model, entity_id: str, tenant_id: str):
    item = session.scalar(select(model).where(model.id == entity_id, model.tenant_id == tenant_id))
    if item is None:
        raise HTTPException(404, 'Not found')
    return item

app = FastAPI(title='H4 DataRights OS', version='0.1.0', lifespan=lifespan,
              description='Tenant-scoped technical MVP; not production-ready.')

@app.middleware('http')
async def add_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Frame-Options'] = 'DENY'
    return response

@app.get('/healthz', include_in_schema=False)
def healthz():
    return {'ok': True}

@app.get('/v1/audit')
def audit_list(auth=Depends(current_actor), session: Session=Depends(session_dep)):
    rows = session.scalars(select(AuditEvent).where(AuditEvent.tenant_id == auth['tenant_id'])
                           .order_by(AuditEvent.created_at.desc()).limit(100)).all()
    return {'events': [{'kind': r.kind, 'resource_id': r.resource_id,
                        'actor_id': r.actor_id, 'at': r.created_at.isoformat()} for r in rows]}

from sqlalchemy.exc import IntegrityError

class NewRightsRequest(BaseModel):
    external_ref: str=Field(min_length=2,max_length=80)
    subject_sha256: str=Field(pattern='^[0-9a-f]{64}$')
    right: Literal['access','rectification','erasure','portability','objection']
    deadline_at: datetime

class Transition(BaseModel):
    status: Literal['in_progress','completed','rejected']

@app.post('/v1/requests',status_code=201)
def create_rights_request(payload: NewRightsRequest,auth=Depends(current_actor),session: Session=Depends(session_dep)):
    if payload.deadline_at.tzinfo is None:
        raise HTTPException(422,'A timezone-aware deadline is required')
    request=RightsRequest(tenant_id=auth['tenant_id'],external_ref=payload.external_ref,
        subject_sha256=payload.subject_sha256,right=payload.right,deadline_at=payload.deadline_at,status='received')
    session.add(request)
    try:
        session.flush()
    except IntegrityError:
        session.rollback();raise HTTPException(409,'Duplicate external reference for this tenant')
    audit(session,auth,'rights_request.received',request.id);session.commit()
    return {'id':request.id,'status':request.status,'deadline_at':request.deadline_at.isoformat()}

@app.get('/v1/requests')
def list_requests(auth=Depends(current_actor),session: Session=Depends(session_dep)):
    rows=session.scalars(select(RightsRequest).where(RightsRequest.tenant_id==auth['tenant_id']).limit(100)).all()
    return [{'id':r.id,'external_ref':r.external_ref,'right':r.right,'status':r.status,
             'deadline_at':r.deadline_at.isoformat()} for r in rows]

@app.post('/v1/requests/{request_id}/transition')
def transition(request_id: str,payload: Transition,auth=Depends(current_actor),session: Session=Depends(session_dep)):
    request=require_tenant(session,RightsRequest,request_id,auth['tenant_id'])
    allowed={'received':{'in_progress'},'in_progress':{'completed','rejected'},'completed':set(),'rejected':set()}
    if payload.status not in allowed[request.status]:
        raise HTTPException(409,'Invalid workflow transition')
    request.status=payload.status;audit(session,auth,'rights_request.'+request.status,request.id);session.commit()
    return {'id':request.id,'status':request.status,
            'note':'Workflow tracking only. No data erasure or legal verification performed.'}
