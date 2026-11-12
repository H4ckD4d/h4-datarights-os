# Threat model — H4 DataRights OS

**Assets:** tenant-scoped application metadata, API keys, audit trails, downstream actions.

**Trust boundaries:** client -> API gateway -> backend -> database -> third-party integrations (not implemented).

**Threats:** API key theft; cross-tenant IDOR; state/race confusion; unauthorized privilege; unbounded request sizes; audit tampering; insecure outbound requests; backup loss.

**Current mitigations:** tenant-filtered database queries; explicit key validation; immutable-like audit inserts; input validation; safe defaults; no outbound integrations; versioned API.

**Residual risks:** demo key store lives in environment, SQLite does not provide scale, no distributed rate-limiter, no production authorization policy, no formal audit signing, no schema migrations, no high-availability. Do not run on public infrastructure with customer data.
