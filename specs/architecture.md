# Architecture

## Overview
The app is a modular local Streamlit application. Streamlit owns presentation and session state, while reusable Python modules implement configuration, model integration, RAG, agent orchestration, tools, ticket persistence, evaluation, and security validation.

## Components
| Component | Module | Responsibilities | Deterministic or agentic |
| --- | --- | --- | --- |
| Streamlit UI | `app.py` | Chat, confirmation controls, tickets, traces, evaluation dashboard | Deterministic UI orchestration |
| Configuration | `northstar_helpdesk/config.py` | Load `.env`, environment variables, paths, model provider settings | Deterministic |
| Model client | `northstar_helpdesk/model_client.py` | Azure Claude request wrapper and mock provider | Agentic text generation, isolated |
| RAG retriever | `northstar_helpdesk/rag.py` | Load documents, chunk, TF-IDF rank, citation metadata | Deterministic |
| Agent | `northstar_helpdesk/agent.py` | Route requests, compose prompts, call tools safely, return response package | Hybrid: deterministic guardrails around LLM |
| Tools | `northstar_helpdesk/tools.py` | Simulated service status, ticket draft validation | Deterministic |
| Database | `northstar_helpdesk/tickets.py` | SQLite schema, create/list tickets | Deterministic |
| Security | `northstar_helpdesk/security.py` | Prompt-injection detection, sanitization, tool allowlist checks | Deterministic |
| Evaluation | `northstar_helpdesk/evaluation.py` | Run reproducible cases and aggregate metrics | Deterministic harness with mock model |
| Knowledge docs | `knowledge_base/*.md` | Fictional Northstar support policies | Static data |

## Data flow
1. User submits a chat message in Streamlit.
2. UI passes message, conversation memory, and optional pending ticket state to `HelpDeskAgent`.
3. Security scanner flags prompt-injection patterns in user input.
4. Agent retrieves TF-IDF context for IT topics.
5. Agent checks deterministic service status when the issue references supported services or outages.
6. Agent asks the model client for a grounded response or uses mock fallback.
7. Agent returns response, citations, trace, and optional pending ticket draft.
8. UI displays response and confirmation controls. Confirmed ticket creation calls `TicketStore.create_ticket` only from UI confirmation flow.
9. Evaluation dashboard runs fixed cases and records latency, citation coverage, safety, and tool success.

## Acceptance criteria summary
- `streamlit run app.py` starts with no Azure credentials by using mock provider.
- Tests can instantiate each component independently.
- No ticket-writing side effect occurs inside the model client or unconfirmed agent path.
- Retrieval and service status are deterministic and inspectable.

## Error handling architecture
- Component exceptions are caught at boundaries, represented as trace errors, and surfaced as user-safe messages.
- Missing or failed Azure configuration falls back to mock unless `MODEL_PROVIDER=azure` is explicitly set; explicit Azure failure returns a controlled model error.
- SQLite database initializes schema automatically and uses parameterized SQL only.

## Final architecture review
- Agentic AI is reserved for natural-language synthesis and flexible routing hints. Retrieval, service-status lookup, ticket persistence, security checks, and evaluation scoring are deterministic.
- RAG grounding is verified through citations and evaluation checks that expected source files appear in answers.
- Ticket confirmation is implemented in UI and persistence layers, not entrusted to model output.
