# Northstar Technologies AI IT Help Desk - Requirements

## Scope
Build a local Python and Streamlit AI IT Help Desk for Northstar Technologies. The app assists employees with IT questions, grounds recommendations in local knowledge documents, can check simulated service status, and creates SQLite support tickets only after explicit confirmation.

## Assumptions
- Azure-hosted Claude credentials may be absent in development and CI; a deterministic mock model must support local use and tests.
- The application is a single-user local demo and does not implement enterprise authentication.
- RAG uses local TF-IDF retrieval over sample Markdown documents; no vector database is required.
- Execution traces may show routing stages, retrieved sources, tool names, sanitized inputs, and results, but never private chain-of-thought.

## Requirement IDs

### Functional requirements
| ID | Requirement | Expected behavior | Acceptance criteria | Error handling | Test cases |
| --- | --- | --- | --- | --- | --- |
| FR-001 | Interactive chat interface | Employee can submit IT requests and receive assistant responses in Streamlit. | Chat history is rendered; new messages append without losing prior context. | Empty input is ignored with a friendly prompt. | T-CHAT-001, T-MEM-001 |
| FR-002 | Conversation memory | Recent user and assistant messages are passed to the agent and retained in session state. | Follow-up requests can reference earlier issue context. | Corrupt/missing state is reinitialized safely. | T-MEM-001 |
| FR-003 | Local knowledge corpus | Include fictional Northstar IT support documents for VPN, MFA, Wi-Fi, password, tickets, and incident escalation. | Documents are stored locally and loaded on startup. | Missing docs produce a clear app error and empty retrieval results. | T-RAG-001 |
| FR-004 | TF-IDF RAG retrieval | Retrieve relevant document chunks without a vector database. | Query returns ranked chunks with document title and source path. | No matches returns an empty cited context and fallback guidance. | T-RAG-001, T-RAG-002 |
| FR-005 | Grounded recommendations | Assistant answers include troubleshooting steps grounded in retrieved docs with citations. | Answers for support topics cite at least one retrieved source when relevant. | If grounding is weak, ask a clarifying question or state limitation. | T-AGENT-001, T-EVAL-001 |
| FR-006 | Clarifying questions | Agent asks for missing details when required to solve safely. | For underspecified issues, response asks concise clarifying questions. | Avoids ticket creation when critical info is missing. | T-AGENT-002 |
| FR-007 | Agent routing | Agent can choose deterministic retrieval, direct answer, service-status tool, and ticket draft paths. | Routing plan is bounded, validated, and visible in trace. | Unknown route falls back to retrieval plus safe answer. | T-AGENT-001, T-TRACE-001 |
| FR-008 | Simulated service status tool | Agent can check service health for VPN, email, SSO, Wi-Fi, and ticketing. | Tool returns structured service status and incident notes. | Unknown service returns a validation error without crashing. | T-TOOL-001 |
| FR-009 | Ticket creation with confirmation | Ticket creation requires explicit user confirmation after a draft is shown. | No database row is inserted before confirmation. | Rejected or expired confirmation discards pending ticket. | T-TICKET-001, T-TICKET-002 |
| FR-010 | SQLite ticket persistence | Confirmed tickets are saved in SQLite with id, user, category, priority, description, status, and timestamps. | Ticket can be created and listed after app restart. | Database errors are surfaced in trace and response. | T-DB-001 |
| FR-011 | Execution trace | UI shows sanitized execution steps, tool calls, retrieval, validation, latency, and errors. | Trace excludes private model reasoning and secrets. | Trace capture continues even after recoverable failures. | T-TRACE-001, T-SEC-002 |
| FR-012 | Evaluation dashboard | UI shows reproducible evaluation results, latency, quality, citation, and tool success metrics. | Evaluation can run locally without API credentials. | Individual case failure is recorded while suite continues. | T-EVAL-001, T-EVAL-002 |

### Technical and security requirements
| ID | Requirement | Expected behavior | Acceptance criteria | Error handling | Test cases |
| --- | --- | --- | --- | --- | --- |
| TR-001 | Python/Streamlit app | Use Python and Streamlit with clear module boundaries. | `streamlit run app.py` starts the app. | Startup errors include remediation hints. | T-START-001 |
| TR-002 | Environment-managed model config | Azure endpoint, key, deployment/model, API version, and provider are read from environment variables. | `.env.example` documents variables; `.env` is gitignored. | Missing credentials selects mock provider unless explicitly forced. | T-CONFIG-001, T-API-001 |
| TR-003 | Isolated model client | Model client is separate from agent, RAG, database, and UI logic. | Business logic can be tested with mock client. | API failures return controlled fallback messages. | T-API-001 |
| TR-004 | Local fallback | Mock/local model supports development, tests, and demos with no external calls. | Full tests pass without Azure credentials. | Mock returns deterministic safe output. | T-API-001, T-EVAL-001 |
| TR-005 | Bounded loops | Agent has a maximum number of steps and validates each tool call. | Agent cannot run unbounded loops. | Exceeding limit produces a safe apology and trace error. | T-AGENT-003 |
| TR-006 | Prompt injection protection | Retrieved docs and user input are scanned for suspicious instructions and treated as untrusted. | Injection content is flagged and not obeyed. | Suspicious content reduces trust and prompts safe answer. | T-SEC-001 |
| TR-007 | Tool authorization | Only allowlisted tools execute and ticket-writing tools require confirmation. | Unauthorized tool names are rejected. | Rejection is logged in trace and returned as controlled error. | T-TOOL-002, T-SEC-003 |
| TR-008 | Test coverage | Include unit and integration tests using mocked model responses. | `pytest` completes locally. | Failures identify affected requirement IDs. | All tests |
| TR-009 | Dependency setup | Provide venv/dependency instructions and dependency manifest. | New environment can install with `pip install -r requirements.txt`. | Install issues are documented in README. | T-START-001 |

## Out of scope
- Enterprise SSO, multi-user authorization, production ticketing integrations, vector databases, live service monitoring, and credential provisioning.
