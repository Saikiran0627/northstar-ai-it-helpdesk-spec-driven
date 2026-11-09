# Security Specification

## Security goals
- Keep credentials out of source code and logs.
- Treat user input and retrieved documents as untrusted.
- Prevent prompt injection from overriding system instructions or tool authorization.
- Require explicit user confirmation for ticket creation or modification.
- Avoid exposing private model reasoning.

## Controls
| ID | Control | Implementation | Acceptance criteria | Tests |
| --- | --- | --- | --- | --- |
| SEC-001 | Secret management | Environment variables and `.env.example`; `.env` ignored. | No real credentials in repo. | T-CONFIG-001 |
| SEC-002 | Prompt injection detection | Pattern scanner for instruction override, secret extraction, tool bypass, and exfiltration language. | Suspicious input/doc is flagged in trace. | T-SEC-001 |
| SEC-003 | Untrusted RAG context | Prompt labels retrieved docs as reference-only and strips unsafe snippets from control flow. | Retrieved instructions cannot trigger tools directly. | T-SEC-001 |
| SEC-004 | Tool allowlist | Tool registry validates name and input schema. | Unknown tools cannot execute. | T-SEC-003 |
| SEC-005 | Confirmation gate | Agent may draft tickets; persistence requires explicit confirmation action. | No ticket row appears before confirmation. | T-TICKET-001 |
| SEC-006 | Trace safety | Trace logs sanitized metadata only. | No API key, Authorization header, or private reasoning appears. | T-SEC-002 |
| SEC-007 | SQL safety | Parameterized SQLite statements. | User content cannot alter schema or query structure. | T-DB-001 |

## Error handling
- Security scanner failures default to conservative flagged state.
- Unauthorized tool attempts return controlled errors and trace events.
- Confirmation state expires when user cancels or submits an unrelated new ticket draft.

## Unresolved decisions
- Production authentication and role-based ticket access are out of scope for this local demo.
- A future production version should replace pattern-based injection detection with layered policy checks and content classification.
