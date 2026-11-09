from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

from .model_client import BaseModelClient, MockModelClient, ModelResponse
from .rag import KnowledgeBase, DocumentChunk
from .security import scan_text
from .tickets import TicketDraft
from .tools import execute_tool, result_to_dict
from .trace import TraceRecorder


@dataclass
class AgentResult:
    answer: str
    citations: list[dict[str, Any]] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)
    pending_ticket: TicketDraft | None = None
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    latency_ms: float = 0.0
    security_flagged: bool = False
    model_provider: str = "mock"


class HelpDeskAgent:
    def __init__(self, kb: KnowledgeBase, model_client: BaseModelClient, max_steps: int = 5) -> None:
        self.kb = kb
        self.model_client = model_client
        self.max_steps = max_steps

    def run(self, user_message: str, history: list[dict[str, str]] | None = None) -> AgentResult:
        history = history or []
        start = perf_counter()
        trace = TraceRecorder()
        steps = 0
        tool_results: list[dict[str, Any]] = []
        citations: list[dict[str, Any]] = []
        pending_ticket: TicketDraft | None = None

        def step(stage: str, action: str, success: bool = True, details: dict | None = None, latency_ms: float | None = None, error: str | None = None) -> bool:
            nonlocal steps
            steps += 1
            if steps > self.max_steps:
                trace.add("agent", "max_steps_exceeded", False, {"max_steps": self.max_steps}, error="Agent step limit exceeded")
                return False
            trace.add(stage, action, success, details, latency_ms, error)
            return True

        scan = scan_text(user_message)
        if not step("input_validation", "scan_user_message", not scan.flagged, scan.summary()):
            return self._limited_result(trace, start)

        query = scan.safe_text
        chunks: list[DocumentChunk] = []
        if self._should_retrieve(query):
            chunks, retrieval_latency = self.kb.search(query)
            citations = [self._citation_dict(chunk) for chunk in chunks]
            if not step("retrieval", "tfidf_search", True, {"result_count": len(chunks), "citations": [c["citation_id"] for c in citations]}, retrieval_latency):
                return self._limited_result(trace, start)

        if scan.flagged:
            answer = (
                "I noticed instructions that look like an attempt to bypass help desk safety rules. "
                "I will ignore those instructions and can still help with a normal IT request. "
                "I cannot create or modify tickets without explicit confirmation."
            )
            step("final", "security_response", True, {"security_flagged": True})
            return AgentResult(answer=answer, citations=citations, trace=trace.as_dicts(), latency_ms=(perf_counter() - start) * 1000, security_flagged=True, model_provider=self.model_client.provider)

        service = self._detect_service(query)
        if service:
            result = execute_tool("check_service_status", service_name=service)
            result_dict = result_to_dict(result)
            tool_results.append(result_dict)
            if not step("tool_call", "check_service_status", result.success, {"service": service, "result": result_dict}, error=result.error):
                return self._limited_result(trace, start)

        wants_ticket = self._wants_ticket(query) or self._is_urgent(query)
        if wants_ticket:
            category = service or self._category_from_query(query)
            priority = "urgent" if self._is_urgent(query) else "medium"
            ticket_result = execute_tool(
                "prepare_ticket",
                summary=self._summary_from_query(query),
                description=query,
                category=category,
                priority=priority,
                requester="Northstar employee",
            )
            ticket_dict = result_to_dict(ticket_result)
            tool_results.append(ticket_dict)
            if ticket_result.success:
                pending_ticket = TicketDraft(**ticket_result.data)
            if not step("ticket_draft", "prepare_ticket", ticket_result.success, {"ticket": ticket_dict}, error=ticket_result.error):
                return self._limited_result(trace, start)

        if self._needs_clarification(query, chunks):
            answer = self._clarifying_answer(query, citations)
            step("final", "clarifying_question", True, {"citations": [c["citation_id"] for c in citations]})
            return AgentResult(answer=answer, citations=citations, trace=trace.as_dicts(), pending_ticket=pending_ticket, tool_results=tool_results, latency_ms=(perf_counter() - start) * 1000, security_flagged=False, model_provider=self.model_client.provider)

        context = self.kb.format_context(chunks)
        model_response = self.model_client.generate(query, context, [c["citation_id"] for c in citations], tool_results, history)
        if not model_response.success:
            trace.add("model", "generate_response", False, {"provider": model_response.provider}, error=model_response.error)
            fallback = MockModelClient().generate(query, context, [c["citation_id"] for c in citations], tool_results, history)
            answer = fallback.text + "\n\nNote: live model generation was unavailable, so this response used the local fallback."
            provider = f"{model_response.provider}->mock"
        else:
            trace.add("model", "generate_response", True, {"provider": model_response.provider})
            answer = model_response.text
            provider = model_response.provider
        if pending_ticket:
            answer += "\n\nI prepared a support ticket draft. Please confirm before I create it in the ticket database."
        trace.add("final", "return_answer", True, {"citation_count": len(citations), "tool_count": len(tool_results), "pending_ticket": pending_ticket is not None})
        return AgentResult(answer=answer, citations=citations, trace=trace.as_dicts(), pending_ticket=pending_ticket, tool_results=tool_results, latency_ms=(perf_counter() - start) * 1000, security_flagged=False, model_provider=provider)

    def _limited_result(self, trace: TraceRecorder, start: float) -> AgentResult:
        return AgentResult(
            answer="I could not complete the request safely because the agent reached its execution limit.",
            trace=trace.as_dicts(),
            latency_ms=(perf_counter() - start) * 1000,
            model_provider=self.model_client.provider,
        )

    @staticmethod
    def _should_retrieve(text: str) -> bool:
        keywords = ["vpn", "mfa", "password", "wifi", "wi-fi", "email", "outlook", "remote", "policy", "ticket", "disconnect", "login", "sign in"]
        return any(keyword in text.lower() for keyword in keywords)

    @staticmethod
    def _detect_service(text: str) -> str | None:
        lower = text.lower()
        if any(word in lower for word in ["vpn", "remote access", "disconnect"]):
            return "vpn"
        if any(word in lower for word in ["mfa", "sso", "login", "sign in"]):
            return "sso"
        if any(word in lower for word in ["email", "outlook", "mail"]):
            return "email"
        if any(word in lower for word in ["wifi", "wi-fi", "wireless"]):
            return "wifi"
        if "ticket" in lower:
            return "ticketing"
        return None

    @staticmethod
    def _wants_ticket(text: str) -> bool:
        lower = text.lower()
        return any(phrase in lower for phrase in ["create a ticket", "open a ticket", "file a ticket", "support ticket", "ticket for"])

    @staticmethod
    def _is_urgent(text: str) -> bool:
        lower = text.lower()
        return any(word in lower for word in ["urgent", "asap", "immediately", "client presentation", "in 30 minutes", "deadline"])

    @staticmethod
    def _category_from_query(text: str) -> str:
        service = HelpDeskAgent._detect_service(text)
        return service or "general"

    @staticmethod
    def _summary_from_query(text: str) -> str:
        cleaned = " ".join(text.strip().split())
        return cleaned[:120] or "IT support request"

    @staticmethod
    def _needs_clarification(text: str, chunks: list[DocumentChunk]) -> bool:
        lower = text.lower().strip()
        vague_terms = {"help", "it is broken", "not working", "issue", "problem"}
        if lower in vague_terms or len(lower.split()) < 4:
            return True
        if not chunks and not any(word in lower for word in ["vpn", "mfa", "wifi", "password", "email", "ticket"]):
            return True
        return False

    @staticmethod
    def _clarifying_answer(text: str, citations: list[dict[str, Any]]) -> str:
        source_text = ""
        if citations:
            source_text = "\n\nRelevant sources: " + " ".join(f"[{item['citation_id']}]" for item in citations[:2])
        return (
            "I can help, but I need a bit more detail: which service or device is affected, what error message do you see, "
            "when did it start, and how urgent is the impact?" + source_text
        )

    @staticmethod
    def _citation_dict(chunk: DocumentChunk) -> dict[str, Any]:
        return {
            "citation_id": chunk.citation_id,
            "title": chunk.title,
            "source": chunk.source,
            "score": round(chunk.score, 4),
            "snippet": chunk.text[:300],
            "flagged": chunk.flagged,
        }
