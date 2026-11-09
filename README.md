# Northstar AI IT Help Desk (Spec-Driven Demo 2)

A local Python and Streamlit AI IT Help Desk application for the fictional company Northstar Technologies. The app demonstrates specification-driven development with local TF-IDF RAG, simulated IT tools, explicit ticket confirmation, SQLite persistence, execution traces, and reproducible evaluation.

## What is included

- Interactive Streamlit chat interface.
- Local RAG over fictional Northstar IT knowledge documents using TF-IDF; no vector database required.
- Agent orchestration that can retrieve documents, check simulated service status, draft tickets, and ask clarifying questions.
- SQLite support-ticket storage with explicit confirmation before ticket creation.
- Conversation memory in Streamlit session state.
- Execution trace showing stages, retrieval, tool calls, validation, errors, and latency without exposing private model reasoning.
- Prompt-injection detection and tool allowlist controls.
- Evaluation dashboard with reproducible cases for answer quality, citations, latency, tool success, and ticket safety.
- Mock model fallback for local development and automated tests.

## Specification documents

The `specs/` directory contains:

1. `requirements.md`
2. `architecture.md`
3. `agent-design.md`
4. `security.md`
5. `evaluation.md`
6. `implementation-plan.md`

The requirements-to-tests traceability matrix is in `specs/implementation-plan.md`.

## Project structure

```text
.
|-- app.py
|-- knowledge_base/
|   |-- email-outlook.md
|   |-- mfa-sso.md
|   |-- password-policy.md
|   |-- ticket-escalation.md
|   |-- vpn-remote-access.md
|   `-- wifi-connectivity.md
|-- northstar_helpdesk/
|   |-- agent.py
|   |-- config.py
|   |-- evaluation.py
|   |-- model_client.py
|   |-- rag.py
|   |-- security.py
|   |-- tickets.py
|   |-- tools.py
|   `-- trace.py
|-- specs/
|-- tests/
|-- .env.example
|-- .gitignore
`-- requirements.txt
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

By default, `MODEL_PROVIDER=mock` keeps everything local except no live model call is made. To use Azure-hosted Claude, set the Azure variables in `.env`:

```env
MODEL_PROVIDER=azure
AZURE_CLAUDE_ENDPOINT=https://your-endpoint.example/path
AZURE_CLAUDE_API_KEY=your-key
AZURE_CLAUDE_MODEL=your-model-or-deployment
AZURE_CLAUDE_API_VERSION=your-api-version-if-required
```

Do not commit `.env`; it is ignored by git.

## Run the application

```bash
source .venv/bin/activate
streamlit run app.py
```

Open the URL Streamlit prints in the terminal. Try:

> My VPN keeps disconnecting. I am working remotely, and I have a client presentation in 30 minutes. Can you help?

The app should retrieve VPN guidance, check simulated VPN status, prepare an urgent ticket draft, and require confirmation before creating the ticket.

## Run tests

```bash
source .venv/bin/activate
pytest
```

Tests use the mock model and do not require Azure credentials.

## Evaluation dashboard

In the Streamlit app, click **Run reproducible evaluation**. The dashboard reports:

- Case pass/fail status
- Answer quality heuristic score
- Citation coverage
- Tool calls
- Latency metrics
- Security and ticket-safety assertions

## Security notes

- Credentials are read only from environment variables.
- Retrieved documents and user input are treated as untrusted.
- Unknown tools are rejected by an allowlist.
- The agent can prepare ticket drafts, but only the UI confirmation action persists a ticket.
- Execution traces are sanitized and do not include private chain-of-thought.

## Known limitations

- This is a local single-user demo, not a production help desk.
- The Azure Claude adapter is conservative because endpoint schemas can vary by Azure gateway. Use mock mode for tests and adjust the endpoint payload if your Azure deployment requires a different schema.
- Prompt-injection protection is pattern-based and should be strengthened for production.
- Simulated service status is static local data, not live monitoring.
