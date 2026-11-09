from pathlib import Path

from northstar_helpdesk.tickets import TicketDraft, TicketStore
from northstar_helpdesk.tools import check_service_status, execute_tool, prepare_ticket


def test_t_tool_001_service_status_known_and_unknown():
    ok = check_service_status("vpn")
    assert ok.success
    assert ok.data["service"] == "vpn"
    bad = check_service_status("mainframe")
    assert not bad.success


def test_t_tool_002_unauthorized_tool_rejected():
    result = execute_tool("create_ticket", summary="bad")
    assert not result.success
    assert "not authorized" in result.error.lower()


def test_t_ticket_001_prepare_ticket_does_not_persist(tmp_path: Path):
    store = TicketStore(tmp_path / "tickets.db")
    result = prepare_ticket("VPN issue", "VPN disconnects", "vpn", "urgent")
    assert result.success
    assert store.list_tickets() == []


def test_t_db_001_confirmed_ticket_persists(tmp_path: Path):
    store = TicketStore(tmp_path / "tickets.db")
    draft = TicketDraft("VPN issue", "VPN disconnects", "vpn", "urgent", "employee")
    record = store.create_ticket(draft)
    assert record.id == 1
    assert record.summary == "VPN issue"
    assert store.list_tickets()[0].id == 1
