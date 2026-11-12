# H4 DataRights OS — Production-readiness plan

Creator: **Chris Cruz — @h4ckd4d**.

Implemented: tenant-specific API, viewer/editor/admin roles, high-entropy SHA-256 API-key digest configuration, revoked-key checks, paginated audit, operational status and deadline summary.

The deadline summary is a scheduling aid **not** a legal determination of applicability, due dates, lawfulness or consent.

Production blockers: OIDC and verified data subject identity, detailed consent records, legal review for LGPD/GDPR, case assignment and retention rules, immutable audit controls, migrations/PostgreSQL RLS, support workflow, quotas, billing, observability and independent security/load tests. No automatic erasure is implemented.
