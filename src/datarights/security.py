"""Tenant authentication for bounded local MVP; production needs SSO, RBAC, revocation and KMS."""
import hmac
import json
import os
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

api_key = APIKeyHeader(name="X-API-Key", auto_error=False)

def current_actor(key: str | None = Security(api_key)) -> dict:
    if not key:
        raise HTTPException(401, "Missing API key")
    try:
        entries = json.loads(os.environ["H4_TENANTS"])
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(503, "Tenant authentication not configured") from exc
    if not isinstance(entries, list):
        raise HTTPException(503, "Invalid authentication configuration")
    for item in entries:
        if not isinstance(item, dict):
            continue
        secret = item.get("key", "")
        if (isinstance(secret, str) and len(secret) >= 24
            and isinstance(item.get("tenant_id"), str) and item.get("tenant_id")
            and isinstance(item.get("actor_id"), str) and item.get("actor_id")
            and hmac.compare_digest(key, secret)):
            return {"tenant_id": item["tenant_id"], "actor_id": item["actor_id"]}
    raise HTTPException(401, "Invalid API key")
