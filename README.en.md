# H4 DataRights OS

> **Local technical MVP: NOT production-ready.**

**Vision:** Track data-subject requests with auditable workflows.

**Creator / Concepção / Creador:** **Chris Cruz — [@H4ckD4d](https://github.com/H4ckD4d)**. Red Team & defensive engineering.

## API demo

```bash
python -m pip install -e '.[test]'
export H4_AUTO_CREATE_TABLES=1
export H4_TENANTS='[{"tenant_id":"demo","actor_id":"operator","key":"REPLACE_WITH_RANDOM_SECRET_24_CHARS_OR_MORE"}]'
uvicorn datarights.app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation. Set a **unique random key**; the value above is an illustrative placeholder and must not protect any service.

```bash
pytest -q
```

## Contribute

Contribute tests, security, documentation, accessibility and scalable architecture. See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md) and [Architecture](docs/ARCHITECTURE.md).

## Storytelling

[Português](docs/STORYTELLING.pt-BR.md) · [English](docs/STORYTELLING.en.md) · [Español](docs/STORYTELLING.es.md)

## Scaling & commercialization

See [Architecture and production blockers](docs/ARCHITECTURE.md) and [Commercialization](docs/COMMERCIAL.md).

**MIT License (source code).** Hosted SaaS, trademarks and enterprise features require separate product decisions.

## v0.2 — Security and privacy operations

Role-based access, hashed credentials, audit pagination and rights request summaries.

[Readiness checklist](docs/PRODUCTION_READINESS.md) — **Chris Cruz @h4ckd4d**.
