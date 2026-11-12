"""Demo API keys and role controls. Replace with enterprise IAM before production."""
import hashlib
import hmac
import json
import os
import re
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

api_key = APIKeyHeader(name='X-API-Key', auto_error=False)
ROLES = {'admin', 'editor', 'viewer'}

def current_actor(key: str | None = Security(api_key)) -> dict:
    if not key:
        raise HTTPException(401, 'Missing API key')
    if len(key) < 24:
        raise HTTPException(401, 'Invalid API key')
    try:
        entries = json.loads(os.environ['H4_TENANTS'])
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(503, 'Tenant authentication not configured') from exc
    if not isinstance(entries, list) or len(entries) > 10000:
        raise HTTPException(503, 'Invalid authentication configuration')
    digest = hashlib.sha256(key.encode('utf-8')).hexdigest()
    matches = []
    for item in entries:
        if not isinstance(item, dict) or item.get('disabled') is True:
            continue
        tenant = item.get('tenant_id')
        actor = item.get('actor_id')
        role = item.get('role', 'admin')  # Backward compatibility with demo fixtures only.
        if not (isinstance(tenant, str) and tenant and isinstance(actor, str) and actor and role in ROLES):
            continue
        sha = item.get('key_sha256')
        if isinstance(sha, str):
            equal = bool(re.fullmatch(r'[0-9a-f]{64}', sha)) and hmac.compare_digest(sha, digest)
        else:
            plain = item.get('key', '')
            equal = isinstance(plain, str) and len(plain) >= 24 and hmac.compare_digest(plain, key)
        if equal:
            matches.append({'tenant_id': tenant, 'actor_id': actor, 'role': role})
    if len(matches) > 1:
        raise HTTPException(503, 'Ambiguous authentication configuration')
    if not matches:
        raise HTTPException(401, 'Invalid API key')
    return matches[0]

def require_write(actor: dict = Depends(current_actor)) -> dict:
    if actor['role'] not in ('admin', 'editor'):
        raise HTTPException(403, 'Write access required')
    return actor

def require_admin(actor: dict = Depends(current_actor)) -> dict:
    if actor['role'] != 'admin':
        raise HTTPException(403, 'Admin access required')
    return actor
