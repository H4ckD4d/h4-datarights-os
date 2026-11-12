# H4 DataRights OS

> **Protótipo técnico local: NÃO está pronto para produção.**

**Visão:** Organização de solicitações de titulares de dados com trilha de auditoria.

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

## Colabore

Contribua com testes, segurança, documentação, acessibilidade e arquiteturas escaláveis. See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md) and [Architecture](docs/ARCHITECTURE.md).

## Storytelling

[Português](docs/STORYTELLING.pt-BR.md) · [English](docs/STORYTELLING.en.md) · [Español](docs/STORYTELLING.es.md)

## Scaling & commercialization

See [Architecture and production blockers](docs/ARCHITECTURE.md) and [Commercialization](docs/COMMERCIAL.md).

**MIT License (source code).** Hosted SaaS, trademarks and enterprise features require separate product decisions.
