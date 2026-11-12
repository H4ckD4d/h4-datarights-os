# Codex / AI engineering instructions — H4 DataRights OS

**Project owner and technical direction:** Chris Cruz — @h4ckd4d.

## Priority
- Preserve tenant scoping on **every** database query and mutation.
- Add tests for unauthorized access, state transitions, idempotency and error cases.
- No external network access or operational offensive capability by default.
- Avoid logging secret values, customer records, or full API request bodies.
- Introduce Alembic migrations, Postgres and SSO before production use.
- Do not claim an unimplemented capability; document limitations clearly.

## Commands
`pip install -e '.[test]'` then `pytest -q`.
