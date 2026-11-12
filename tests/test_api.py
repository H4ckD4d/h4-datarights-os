import hashlib, json, os
import pytest
from fastapi.testclient import TestClient
from . import TEST_APP

KEY_A='tenantA_sample_key_0123456789ABCDEFG'
KEY_B='tenantB_sample_key_0123456789ABCDEFG'
KEY_REVIEWER='tenantA_reviewer_key_0123456789ABC'
KEY_SECOND='tenantA_second_reviewer_0123456789'

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('H4_DATABASE_URL',f'sqlite:///{tmp_path / "db.sqlite"}')
    monkeypatch.setenv('H4_AUTO_CREATE_TABLES','1')
    monkeypatch.setenv('H4_TENANTS',json.dumps([
        {'tenant_id':'t-a','actor_id':'owner','key':KEY_A},
        {'tenant_id':'t-a','actor_id':'reviewer','key':KEY_REVIEWER},
        {'tenant_id':'t-a','actor_id':'second','key':KEY_SECOND},
        {'tenant_id':'t-b','actor_id':'ownerB','key':KEY_B},
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
