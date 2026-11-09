from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Callable


@dataclass(frozen=True)
class ToolResult:
    name: str
    success: bool
    data: dict[str, Any]
    error: str | None = None


SERVICE_STATUS = {
    "vpn": {
        "service": "vpn",
        "status": "degraded",
        "message": "Northstar VPN gateways in us-east are seeing intermittent disconnects for some remote employees.",
        "recommended_action": "Reconnect using the West gateway if available, verify MFA, and collect logs if drops continue.",
    },
    "email": {
        "service": "email",
        "status": "operational",
        "message": "Northstar mail flow and Outlook web access are operational.",
        "recommended_action": "Troubleshoot local client profile and network connectivity.",
    },
    "sso": {
        "service": "sso",
        "status": "operational",
        "message": "Single sign-on and MFA delivery are operational.",
        "recommended_action": "Check device time sync, authenticator app registration, and backup methods.",
    },
    "wifi": {
        "service": "wifi",
        "status": "operational",
        "message": "Corporate Wi-Fi controllers report normal service.",
        "recommended_action": "Forget and rejoin Northstar-Secure, then verify certificate prompts.",
    },
    "ticketing": {
        "service": "ticketing",
        "status": "operational",
        "message": "The help desk ticketing service is accepting new tickets.",
        "recommended_action": "Create tickets for issues that cannot be resolved through self-service steps.",
    },
}

SERVICE_ALIASES = {
    "vpn": "vpn",
    "remote access": "vpn",
    "email": "email",
    "outlook": "email",
    "mail": "email",
    "sso": "sso",
    "mfa": "sso",
    "login": "sso",
    "sign in": "sso",
    "wifi": "wifi",
    "wi-fi": "wifi",
    "wireless": "wifi",
    "ticket": "ticketing",
    "help desk": "ticketing",
}

ALLOWED_TOOLS = {"check_service_status", "prepare_ticket"}


def normalize_service(service_name: str) -> str | None:
    value = (service_name or "").strip().lower()
    if value in SERVICE_STATUS:
        return value
    for alias, canonical in SERVICE_ALIASES.items():
        if alias in value:
            return canonical
    return None


def check_service_status(service_name: str) -> ToolResult:
    service = normalize_service(service_name)
    if not service:
        return ToolResult("check_service_status", False, {}, f"Unsupported service: {service_name}")
    data = dict(SERVICE_STATUS[service])
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    return ToolResult("check_service_status", True, data)


def prepare_ticket(summary: str, description: str, category: str, priority: str = "medium", requester: str = "employee") -> ToolResult:
    summary = (summary or "").strip()
    description = (description or "").strip()
    category = (category or "general").strip().lower()
    priority = (priority or "medium").strip().lower()
    requester = (requester or "employee").strip()
    if not summary or not description:
        return ToolResult("prepare_ticket", False, {}, "Ticket summary and description are required.")
    if priority not in {"low", "medium", "high", "urgent"}:
        priority = "medium"
    return ToolResult("prepare_ticket", True, {
        "summary": summary[:160],
        "description": description[:4000],
        "category": category[:80],
        "priority": priority,
        "requester": requester[:120],
    })


TOOL_REGISTRY: dict[str, Callable[..., ToolResult]] = {
    "check_service_status": check_service_status,
    "prepare_ticket": prepare_ticket,
}


def execute_tool(name: str, **kwargs: Any) -> ToolResult:
    if name not in ALLOWED_TOOLS or name not in TOOL_REGISTRY:
        return ToolResult(name, False, {}, f"Tool is not authorized: {name}")
    try:
        return TOOL_REGISTRY[name](**kwargs)
    except Exception as exc:  # pragma: no cover - defensive boundary
        return ToolResult(name, False, {}, f"Tool failed: {exc}")


def result_to_dict(result: ToolResult) -> dict[str, Any]:
    return asdict(result)
