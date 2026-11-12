import hashlib, json, os
import pytest
from fastapi.testclient import TestClient
from . import TEST_APP

KEY_A='tenantA_sample_key_0123456789ABCDEFG'
KEY_B='tenantB_sample_key_0123456789ABCDEFG'
KEY_REVIEWER='tenantA_reviewer_key_0123456789ABC'
KEY_SECOND='tenantA_second_reviewer_0123456789'
KEY_VIEWER='tenantA_viewer_readonly_0123456789AB'
KEY_HASHED='tenantA_hashed_credential_0123456789AB'
KEY_DISABLED='tenantA_revoked_credential_0123456789AB'

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('H4_DATABASE_URL',f'sqlite:///{tmp_path / "db.sqlite"}')
    monkeypatch.setenv('H4_AUTO_CREATE_TABLES','1')
    monkeypatch.setenv('H4_TENANTS',json.dumps([
        {'tenant_id':'t-a','actor_id':'owner','role':'admin','key':KEY_A},
        {'tenant_id':'t-a','actor_id':'reviewer','role':'editor','key':KEY_REVIEWER},
        {'tenant_id':'t-a','actor_id':'second','role':'editor','key':KEY_SECOND},
        {'tenant_id':'t-b','actor_id':'ownerB','role':'admin','key':KEY_B},
        {'tenant_id':'t-a','actor_id':'observer','role':'viewer','key':KEY_VIEWER},
        {'tenant_id':'t-a','actor_id':'hashed','role':'viewer','key_sha256':hashlib.sha256(KEY_HASHED.encode()).hexdigest()},
        {'tenant_id':'t-a','actor_id':'revoked','role':'admin','key':KEY_DISABLED,'disabled':True},
    ]))
    with TestClient(TEST_APP) as c:
        yield c

def headers(key=KEY_A):
    return {'X-API-Key':key}

def test_security(client):
    assert client.get('/healthz').status_code==200
    assert client.get('/v1/audit').status_code==401
    assert client.get('/v1/audit', headers=headers('invalid')).status_code==401
    assert client.get('/v1/audit', headers=headers()).status_code==200
    assert client.get('/v1/audit', headers=headers()).headers['Cache-Control']=='no-store'

def test_transition_and_isolation(client):
    payload={'external_ref':'DSAR-001','subject_sha256':hashlib.sha256(b'synthetic-person').hexdigest(),
             'right':'access','deadline_at':'2030-05-01T10:00:00Z'}
    result=client.post('/v1/requests',json=payload,headers=headers())
    assert result.status_code==201,result.text
    id=result.json()['id']
    assert client.post(f'/v1/requests/{id}/transition',json={'status':'completed'},headers=headers()).status_code==409
    assert client.post(f'/v1/requests/{id}/transition',json={'status':'in_progress'},headers=headers()).status_code==200
    assert client.post(f'/v1/requests/{id}/transition',json={'status':'completed'},headers=headers()).status_code==200
    assert client.post(f'/v1/requests/{id}/transition',json={'status':'in_progress'},headers=headers()).status_code==409
    assert client.post(f'/v1/requests/{id}/transition',json={'status':'completed'},headers=headers(KEY_B)).status_code==404

def test_idempotent_reference_and_timezone_required(client):
    payload={'external_ref':'DSAR-002','subject_sha256':hashlib.sha256(b'fiction').hexdigest(),
             'right':'erasure','deadline_at':'2030-05-01T10:00:00Z'}
    assert client.post('/v1/requests',json=payload,headers=headers()).status_code==201
    assert client.post('/v1/requests',json=payload,headers=headers()).status_code==409
    assert client.post('/v1/requests',json={**payload,'external_ref':'DSAR-003','deadline_at':'2030-05-01T10:00:00'},headers=headers()).status_code==422

def test_audit_visibility_is_tenant_scoped(client):
    from sqlalchemy.orm import Session
    from . import TEST_APP
    from datarights.db import AuditEvent

    with Session(TEST_APP.state.engine) as session:
        session.add(AuditEvent(tenant_id='t-a',actor_id='owner',kind='synthetic',resource_id='a'))
        session.add(AuditEvent(tenant_id='t-b',actor_id='ownerB',kind='synthetic',resource_id='b'))
        session.commit()
    a=client.get('/v1/audit',headers=headers(KEY_A)).json()['events']
    b=client.get('/v1/audit',headers=headers(KEY_B)).json()['events']
    assert [x['resource_id'] for x in a]==['a']
    assert [x['resource_id'] for x in b]==['b']

def test_missing_auth_config_fails_closed(client, monkeypatch):
    monkeypatch.delenv('H4_TENANTS')
    response=client.get('/v1/audit',headers=headers(KEY_A))
    assert response.status_code==503

def test_viewer_and_hashed_keys(client):
    assert client.get('/v1/audit',headers=headers(KEY_VIEWER)).status_code==200
    assert client.get('/v1/audit',headers=headers(KEY_HASHED)).status_code==200
    assert client.get('/v1/audit',headers=headers(KEY_DISABLED)).status_code==401

def test_audit_pagination_bounds(client):
    assert client.get('/v1/audit?limit=1&offset=0',headers=headers()).status_code==200
    assert client.get('/v1/audit?limit=101',headers=headers()).status_code==422
    assert client.get('/v1/audit?offset=-1',headers=headers()).status_code==422

def test_viewer_readonly(client):
    assert client.post('/v1/requests',json={'external_ref':'REF','subject_sha256':hashlib.sha256(b'x').hexdigest(),'right':'access','deadline_at':'2030-05-01T10:00:00Z'},headers=headers(KEY_VIEWER)).status_code==403

def test_ambiguous_credentials_fail_closed(client,monkeypatch):
    entries=[{'tenant_id':'x','actor_id':'a','role':'admin','key':KEY_A},
             {'tenant_id':'y','actor_id':'b','role':'admin','key':KEY_A}]
    monkeypatch.setenv('H4_TENANTS',json.dumps(entries))
    assert client.get('/v1/audit',headers=headers(KEY_A)).status_code==503

def test_rights_summary_tenant_scope_and_deadlines(client):
    from datetime import datetime,timedelta,timezone
    deadline=(datetime.now(timezone.utc)+timedelta(days=3)).isoformat()
    body={'external_ref':'DSAR-SUM','subject_sha256':hashlib.sha256(b'synthetic').hexdigest(),
          'right':'access','deadline_at':deadline}
    assert client.post('/v1/requests',json=body,headers=headers()).status_code==201
    result=client.get('/v1/requests/summary?within_days=5',headers=headers(KEY_VIEWER)).json()
    assert result['total']==1 and result['due_soon']==1
    assert client.get('/v1/requests/summary',headers=headers(KEY_B)).json()['total']==0
    assert client.get('/v1/requests/summary?within_days=500',headers=headers()).status_code==422
