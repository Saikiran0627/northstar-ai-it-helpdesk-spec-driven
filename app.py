from __future__ import annotations

import streamlit as st

from northstar_helpdesk.agent import HelpDeskAgent
from northstar_helpdesk.config import load_settings
from northstar_helpdesk.evaluation import results_as_dicts, run_evaluation
from northstar_helpdesk.model_client import get_model_client
from northstar_helpdesk.rag import KnowledgeBase
from northstar_helpdesk.tickets import TicketDraft, TicketStore


st.set_page_config(page_title="Northstar AI IT Help Desk", page_icon="IT", layout="wide")


@st.cache_resource
def load_resources():
    settings = load_settings()
    kb = KnowledgeBase(settings.kb_path)
    model_client = get_model_client(settings)
    ticket_store = TicketStore(settings.db_path)
    agent = HelpDeskAgent(kb, model_client)
    return settings, kb, ticket_store, agent


def ensure_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("last_trace", [])
    st.session_state.setdefault("last_citations", [])
    st.session_state.setdefault("pending_ticket", None)
    st.session_state.setdefault("last_metrics", {})


def draft_from_state(data: dict) -> TicketDraft:
    return TicketDraft(
        summary=data["summary"],
        description=data["description"],
        category=data.get("category", "general"),
        priority=data.get("priority", "medium"),
        requester=data.get("requester", "employee"),
    )


def main() -> None:
    ensure_state()
    settings, kb, ticket_store, agent = load_resources()

    st.title("Northstar Technologies AI IT Help Desk")
    st.caption("Local Streamlit demo with TF-IDF RAG, simulated IT tools, ticket confirmation, execution traces, and evaluation.")

    with st.sidebar:
        st.subheader("Configuration")
        st.write({
            "model_provider": settings.model_provider,
            "azure_configured": settings.azure_configured,
            "knowledge_chunks": len(kb.chunks),
            "database": str(settings.db_path),
        })
        if settings.model_provider == "mock":
            st.info("Using local mock model. Set Azure variables in .env to use Azure Claude.")

    chat_col, trace_col = st.columns([2, 1])

    with chat_col:
        st.subheader("Chat")
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        prompt = st.chat_input("Ask Northstar IT for help...")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            result = agent.run(prompt, st.session_state.messages[:-1])
            st.session_state.messages.append({"role": "assistant", "content": result.answer})
            st.session_state.last_trace = result.trace
            st.session_state.last_citations = result.citations
            st.session_state.last_metrics = {"latency_ms": round(result.latency_ms, 2), "model_provider": result.model_provider}
            st.session_state.pending_ticket = result.pending_ticket.to_dict() if result.pending_ticket else None
            with st.chat_message("assistant"):
                st.markdown(result.answer)

        if st.session_state.pending_ticket:
            st.warning("A support ticket draft is pending confirmation. No ticket has been created yet.")
            st.json(st.session_state.pending_ticket)
            confirm_col, cancel_col = st.columns(2)
            with confirm_col:
                if st.button("Confirm and create ticket", type="primary"):
                    record = ticket_store.create_ticket(draft_from_state(st.session_state.pending_ticket))
                    st.session_state.pending_ticket = None
                    st.success(f"Created ticket #{record.id}: {record.summary}")
            with cancel_col:
                if st.button("Cancel ticket draft"):
                    st.session_state.pending_ticket = None
                    st.info("Ticket draft cancelled.")

        st.subheader("Recent tickets")
        tickets = ticket_store.list_tickets()
        if tickets:
            st.dataframe([ticket.__dict__ for ticket in tickets], use_container_width=True)
        else:
            st.caption("No confirmed tickets yet.")

    with trace_col:
        st.subheader("Execution trace")
        st.caption("Shows stages and tool calls without private model reasoning.")
        if st.session_state.last_metrics:
            st.metric("Last response latency", f"{st.session_state.last_metrics.get('latency_ms', 0)} ms")
            st.write("Model provider:", st.session_state.last_metrics.get("model_provider"))
        st.json(st.session_state.last_trace)
        st.subheader("Citations")
        st.json(st.session_state.last_citations)

    st.divider()
    st.subheader("Evaluation dashboard")
    if st.button("Run reproducible evaluation"):
        results, metrics = run_evaluation(str(settings.kb_path))
        st.session_state.eval_results = results_as_dicts(results)
        st.session_state.eval_metrics = metrics
    if "eval_metrics" in st.session_state:
        metric_cols = st.columns(5)
        metric_cols[0].metric("Cases", st.session_state.eval_metrics["case_count"])
        metric_cols[1].metric("Passed", st.session_state.eval_metrics["passed"])
        metric_cols[2].metric("Failed", st.session_state.eval_metrics["failed"])
        metric_cols[3].metric("Avg score", st.session_state.eval_metrics["average_score"])
        metric_cols[4].metric("p50 latency", f"{st.session_state.eval_metrics['p50_latency_ms']} ms")
        st.dataframe(st.session_state.eval_results, use_container_width=True)


if __name__ == "__main__":
    main()
