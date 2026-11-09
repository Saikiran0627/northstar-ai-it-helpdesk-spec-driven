from __future__ import annotations

import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TicketDraft:
    summary: str
    description: str
    category: str = "general"
    priority: str = "medium"
    requester: str = "employee"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class TicketRecord:
    id: int
    summary: str
    description: str
    category: str
    priority: str
    requester: str
    status: str
    created_at: str
    updated_at: str


class TicketStore:
    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    summary TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    requester TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def create_ticket(self, draft: TicketDraft) -> TicketRecord:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tickets (summary, description, category, priority, requester, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (draft.summary, draft.description, draft.category, draft.priority, draft.requester, "open", now, now),
            )
            conn.commit()
            ticket_id = int(cursor.lastrowid)
        return self.get_ticket(ticket_id)

    def get_ticket(self, ticket_id: int) -> TicketRecord:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if row is None:
            raise KeyError(f"Ticket not found: {ticket_id}")
        return self._row_to_record(row)

    def list_tickets(self, limit: int = 20) -> list[TicketRecord]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM tickets ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [self._row_to_record(row) for row in rows]

    @staticmethod
    def _row_to_record(row: sqlite3.Row | dict[str, Any]) -> TicketRecord:
        return TicketRecord(
            id=int(row["id"]),
            summary=row["summary"],
            description=row["description"],
            category=row["category"],
            priority=row["priority"],
            requester=row["requester"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
