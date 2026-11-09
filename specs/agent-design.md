# Agent Design

## Agent responsibilities
The Help Desk agent receives a user message and conversation context, then returns a structured `AgentResult` containing the user-facing answer, citations, trace events, optional ticket draft, and metrics.

## Routing policy
The agent uses deterministic heuristics first:
- Always scan user input for prompt-injection risk.
- Retrieve documents for support requests, policy questions, troubleshooting, access issues, or ticket requests.
- Check simulated service status when message mentions VPN, email, SSO, Wi-Fi, ticketing, outage, down, disconnecting, or service health.
- Draft a ticket only when the user explicitly asks to open/create/file a ticket or when severity indicates urgent human help may be needed.
- Ask clarifying questions when category, impact, urgency, or device/network context is missing.

## Bounded execution
- Maximum agent steps: 5.
- Allowed tools: `check_service_status`, `prepare_ticket`.
- `create_ticket` is not an agent-executable tool. It is a post-agent confirmed UI action.
- Each tool input is validated before execution.

## Model prompt contract
The model receives:
- System instructions to be helpful, concise, grounded, and safety-aware.
- Sanitized recent conversation context.
- Retrieved document excerpts marked as untrusted reference material.
- Tool results.
- Instructions to cite sources using supplied citation IDs.

The model must not receive secrets or raw environment values.

## Execution trace schema
Each trace event contains:
- `stage`: e.g. input_validation, retrieval, tool_call, model, ticket_draft, final.
- `action`: concise action label.
- `details`: sanitized structured metadata.
- `success`: boolean.
- `latency_ms`: optional.
- `error`: optional user-safe error text.

Private chain-of-thought is never recorded. The trace shows what happened, not hidden reasoning.

## Tool design
### `check_service_status(service_name)`
Returns service, status, message, updated_at, and recommended action. Supported services are vpn, email, sso, wifi, ticketing.

### `prepare_ticket(...)`
Validates and normalizes a pending ticket draft but does not persist it.

### Confirmed ticket creation
`TicketStore.create_ticket(ticket)` is called only when the user presses/enters explicit confirmation in the UI/test harness.

## Acceptance criteria
- Unauthorized tool names fail validation.
- Ticket drafts do not change SQLite state.
- Confirmation creates exactly one ticket.
- The agent returns a response even if the model provider fails.

## Test cases
- T-AGENT-001: VPN request retrieves VPN docs, checks VPN status, returns citations.
- T-AGENT-002: Vague request asks clarifying questions.
- T-AGENT-003: Step limit returns safe failure when exceeded.
- T-TOOL-001: Known and unknown service status behavior.
- T-TICKET-001: Ticket draft is generated but not persisted before confirmation.
