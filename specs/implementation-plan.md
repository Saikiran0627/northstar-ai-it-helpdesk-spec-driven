# Implementation Plan

## Milestone 1: Project structure and specifications
Requirement IDs: FR-003, TR-008, TR-009
- Create `specs/`, package directory, tests, sample knowledge docs, and dependency manifests.
- Add README, `.env.example`, `.gitignore`.
- Acceptance: repository contains the six specification documents and traceability matrix.

## Milestone 2: Deterministic core
Requirement IDs: FR-003, FR-004, FR-008, FR-010, TR-006, TR-007
- Implement config, security scanner, TF-IDF retriever, tool registry, and SQLite ticket store.
- Unit tests for retrieval, tools, security, and persistence.

## Milestone 3: Agent orchestration
Requirement IDs: FR-002, FR-005, FR-006, FR-007, FR-009, FR-011, TR-003, TR-004, TR-005
- Implement isolated model clients, bounded agent loop, trace, ticket draft behavior, and fallback handling.
- Unit/integration tests with mock model responses.

## Milestone 4: Streamlit application
Requirement IDs: FR-001, FR-009, FR-011, FR-012, TR-001, TR-002
- Implement chat UI, pending-ticket confirmation controls, trace view, ticket list, and evaluation dashboard.
- Startup smoke check using import/compile tests.

## Milestone 5: Evaluation and documentation
Requirement IDs: FR-012, TR-008, TR-009
- Implement reproducible evaluation cases and dashboard output.
- Update README with setup, run, test, and configuration instructions.

## Requirements-to-tests traceability matrix
| Requirement | Tests |
| --- | --- |
| FR-001 | T-START-001, T-CHAT-001 |
| FR-002 | T-MEM-001 |
| FR-003 | T-RAG-001 |
| FR-004 | T-RAG-001, T-RAG-002 |
| FR-005 | T-AGENT-001, T-EVAL-001 |
| FR-006 | T-AGENT-002 |
| FR-007 | T-AGENT-001, T-TRACE-001 |
| FR-008 | T-TOOL-001 |
| FR-009 | T-TICKET-001, T-TICKET-002 |
| FR-010 | T-DB-001 |
| FR-011 | T-TRACE-001, T-SEC-002 |
| FR-012 | T-EVAL-001, T-EVAL-002 |
| TR-001 | T-START-001 |
| TR-002 | T-CONFIG-001 |
| TR-003 | T-API-001 |
| TR-004 | T-API-001, T-EVAL-001 |
| TR-005 | T-AGENT-003 |
| TR-006 | T-SEC-001 |
| TR-007 | T-TOOL-002, T-SEC-003 |
| TR-008 | Full pytest suite |
| TR-009 | T-START-001 |

## Specification review
### Missing requirements addressed
- Added local fallback for missing Azure credentials.
- Added explicit no-persistence-before-confirmation requirement.
- Added trace redaction and no-private-reasoning requirement.
- Added reproducible evaluation requirements and metrics.

### Contradictions resolved
- The original phase flow asked to wait for approval, while the final instruction asked for one continuous workflow. This implementation treats the user's final instruction as approval to proceed after creating and reviewing specs.
- Ticket creation is described as a tool in the high-level request, but security requires confirmation. The implementation separates unprivileged ticket drafting from confirmed SQLite creation.

### Complexity review
- Vector databases, authentication, production workflow engines, and live monitoring are unnecessary for this demo and remain out of scope.
- Deterministic code handles retrieval, tools, security checks, persistence, and evaluation scoring. The model is used only for language synthesis/flexible response generation.

### RAG grounding and citations
- Retrieved chunks carry citation IDs and source paths.
- Agent prompts instruct the model to cite supplied citation IDs.
- Evaluation checks expected source filenames and citation presence.

### Unauthorized tool execution
- Tools are allowlisted by registry and validate inputs.
- Ticket persistence is not available through the agent tool loop.

### API and tool failure handling
- Azure errors are captured and replaced with mock/local fallback responses unless explicitly forced.
- Tool validation failures are trace events and do not crash the request.

## Unresolved decisions
- Exact Azure Claude REST schema can vary by provider gateway; the adapter is conservative and documented for environment-based adjustment.
- Production deployment, authentication, and real ITSM integration remain future work.
