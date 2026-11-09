from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

from .security import sanitize_trace_details


@dataclass
class TraceEvent:
    stage: str
    action: str
    success: bool
    details: dict[str, Any] = field(default_factory=dict)
    latency_ms: float | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = {
            "stage": self.stage,
            "action": self.action,
            "success": self.success,
            "details": sanitize_trace_details(self.details),
        }
        if self.latency_ms is not None:
            data["latency_ms"] = round(self.latency_ms, 2)
        if self.error:
            data["error"] = self.error
        return data


class TraceRecorder:
    def __init__(self) -> None:
        self.events: list[TraceEvent] = []

    def add(self, stage: str, action: str, success: bool = True, details: dict | None = None, latency_ms: float | None = None, error: str | None = None) -> None:
        self.events.append(TraceEvent(stage=stage, action=action, success=success, details=details or {}, latency_ms=latency_ms, error=error))

    def timed(self, stage: str, action: str):
        recorder = self

        class Timer:
            def __enter__(self):
                self.start = perf_counter()
                return self

            def __exit__(self, exc_type, exc, tb):
                elapsed = (perf_counter() - self.start) * 1000
                recorder.add(stage, action, success=exc is None, latency_ms=elapsed, error=str(exc) if exc else None)
                return False

        return Timer()

    def as_dicts(self) -> list[dict]:
        return [event.to_dict() for event in self.events]
