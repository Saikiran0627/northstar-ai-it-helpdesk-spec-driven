from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

SECRET_PATTERNS = [
    re.compile(r"api[_ -]?key\s*[:=]\s*[^\s]+", re.IGNORECASE),
    re.compile(r"authorization\s*[:=]\s*bearer\s+[^\s]+", re.IGNORECASE),
]

INJECTION_PATTERNS = [
    re.compile(r"ignore (all )?(previous|prior|above) instructions", re.IGNORECASE),
    re.compile(r"reveal (the )?(system|developer|hidden) prompt", re.IGNORECASE),
    re.compile(r"bypass .*confirmation", re.IGNORECASE),
    re.compile(r"create .*ticket .*without confirmation", re.IGNORECASE),
    re.compile(r"do not ask (for )?confirmation", re.IGNORECASE),
    re.compile(r"exfiltrate|steal|leak .*secret", re.IGNORECASE),
    re.compile(r"tool[_ -]?call\s*:", re.IGNORECASE),
]


@dataclass
class SecurityFinding:
    kind: str
    message: str


@dataclass
class SecurityScanResult:
    safe_text: str
    flagged: bool = False
    findings: list[SecurityFinding] = field(default_factory=list)

    def summary(self) -> dict:
        return {
            "flagged": self.flagged,
            "findings": [f"{item.kind}: {item.message}" for item in self.findings],
        }


def redact_secrets(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def scan_text(text: str) -> SecurityScanResult:
    safe_text = redact_secrets(text or "")
    findings: list[SecurityFinding] = []
    for pattern in INJECTION_PATTERNS:
        if pattern.search(safe_text):
            findings.append(SecurityFinding("prompt_injection", f"Matched pattern: {pattern.pattern}"))
    return SecurityScanResult(safe_text=safe_text, flagged=bool(findings), findings=findings)


def sanitize_trace_details(details: dict | None) -> dict:
    if not details:
        return {}
    sanitized = {}
    for key, value in details.items():
        if isinstance(value, str):
            sanitized[key] = redact_secrets(value)
        elif isinstance(value, Iterable) and not isinstance(value, (dict, bytes)):
            sanitized[key] = [redact_secrets(str(item)) for item in value]
        else:
            sanitized[key] = value
    return sanitized
