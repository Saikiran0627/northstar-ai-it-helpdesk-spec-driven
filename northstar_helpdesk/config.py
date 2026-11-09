from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - dependency may not be installed during early import checks
    load_dotenv = None


@dataclass(frozen=True)
class Settings:
    model_provider: str = "mock"
    azure_endpoint: str = ""
    azure_api_key: str = ""
    azure_model: str = ""
    azure_api_version: str = ""
    db_path: Path = Path("data/northstar_tickets.db")
    kb_path: Path = Path("knowledge_base")

    @property
    def azure_configured(self) -> bool:
        return bool(self.azure_endpoint and self.azure_api_key and self.azure_model)


def load_settings() -> Settings:
    if load_dotenv is not None:
        load_dotenv(override=False)
    provider = os.getenv("MODEL_PROVIDER", "mock").strip().lower() or "mock"
    endpoint = os.getenv("AZURE_CLAUDE_ENDPOINT", "").strip()
    api_key = os.getenv("AZURE_CLAUDE_API_KEY", "").strip()
    model = os.getenv("AZURE_CLAUDE_MODEL", "").strip()
    api_version = os.getenv("AZURE_CLAUDE_API_VERSION", "").strip()
    if provider == "azure" and not (endpoint and api_key and model):
        # Explicit Azure mode remains visible to callers; model client handles the controlled error.
        pass
    elif provider not in {"mock", "azure"}:
        provider = "mock"
    return Settings(
        model_provider=provider,
        azure_endpoint=endpoint,
        azure_api_key=api_key,
        azure_model=model,
        azure_api_version=api_version,
        db_path=Path(os.getenv("NORTHSTAR_DB_PATH", "data/northstar_tickets.db")),
        kb_path=Path(os.getenv("NORTHSTAR_KB_PATH", "knowledge_base")),
    )
